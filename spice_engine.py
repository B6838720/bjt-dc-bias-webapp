"""ngspice adapter for the Lab 04 CE voltage-divider simulator.

This module is deliberately free of Flask/HTML.  It only:
  1. validates engineering inputs,
  2. builds one netlist for one analysis mode,
  3. runs the external ngspice process with a list of arguments,
  4. parses the *real* batch log, and
  5. returns values/series plus provenance and error information.

No traces, gains or operating points are fabricated here.  Values derived from
SPICE node voltages (for example IC from VCC/RC/VC) are labelled explicitly.
"""

from __future__ import annotations

import math
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

ANALYSIS_DC = "dc"
ANALYSIS_AC = "ac"
ANALYSIS_TRANSIENT = "transient"
ANALYSES = (ANALYSIS_DC, ANALYSIS_AC, ANALYSIS_TRANSIENT)

ANALYSIS_LABELS = {
    ANALYSIS_DC: "DC Operating Point (.op)",
    ANALYSIS_AC: "AC Frequency Response (.ac)",
    ANALYSIS_TRANSIENT: "Transient Response (.tran)",
}

_NUMBER_RE = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_NODE_RE = re.compile(
    r"^\s*(vcc|base|emitter|collector)\s+([-+0-9.eE]+)\s*$",
    re.IGNORECASE,
)
_MODEL_NAME_RE = re.compile(r"^\s*\.model\s+([A-Za-z0-9_$.-]+)", re.IGNORECASE)
_FORBIDDEN_MODEL_DIRECTIVES = (
    ".control", ".endc", ".include", ".inc", ".op", ".dc", ".ac",
    ".tran", ".print", ".plot", ".end", ".tf", ".noise", ".disto",
)

Runner = Callable[..., Any]


class SimulationError(RuntimeError):
    """Raised for validation, engine, or result-parsing failures."""


@dataclass(frozen=True)
class SimulationInput:
    """SI-unit inputs passed from app.py after form parsing."""

    analysis: str
    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    rl: float
    cin: float
    cout: float
    amp: float
    freq: float
    beta: float
    vbe: float
    fstart: float
    fstop: float
    fpoints: int
    tstep: float
    tstop: float
    model_name: str
    model_text: str
    model_source: str = "unspecified"


@dataclass(frozen=True)
class ModelConfig:
    name: str
    text: str
    source: str

    @property
    def configured(self) -> bool:
        return bool(self.name and self.text)


def _num(value: float) -> str:
    return f"{value:.10g}"


def _finite_positive(name: str, value: float) -> None:
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise SimulationError(f"{name} ต้องเป็นจำนวนจำกัด")
    if float(value) <= 0:
        raise SimulationError(f"{name} ต้องมากกว่า 0")


def validate_params(params: SimulationInput) -> None:
    """Reject inputs that cannot describe a safe, bounded SPICE run."""
    if params.analysis not in ANALYSES:
        raise SimulationError(f"Analysis mode ไม่รู้จัก: {params.analysis}")

    for name, value in (
        ("VCC", params.vcc),
        ("R1", params.r1),
        ("R2", params.r2),
        ("RC", params.rc),
        ("RE", params.re),
        ("RL", params.rl),
        ("Cin", params.cin),
        ("Cout", params.cout),
        ("Amplitude", params.amp),
        ("Frequency", params.freq),
        ("β", params.beta),
        ("VBE", params.vbe),
        ("Fstart", params.fstart),
        ("Fstop", params.fstop),
        ("Tstep", params.tstep),
        ("Tstop", params.tstop),
    ):
        _finite_positive(name, value)

    if params.amp > params.vcc:
        raise SimulationError("Amplitude ต้องไม่เกิน VCC สำหรับ small-signal นี้")
    if params.vbe >= params.vcc:
        raise SimulationError("VBE ต้องน้อยกว่า VCC")
    if params.fstop <= params.fstart:
        raise SimulationError("Fstop ต้องมากกว่า Fstart")
    if params.fpoints < 2:
        raise SimulationError("Fpoints ต้องมากกว่าหรือเท่ากับ 2")
    if params.tstop <= params.tstep:
        raise SimulationError("Tstop ต้องมากกว่า Tstep")
    if not params.model_name.strip():
        raise SimulationError("ยังไม่ได้ระบุชื่อ BJT model")
    if not params.model_text.strip():
        raise SimulationError("ยังไม่ได้ใส่ BJT model card")


def _configured_model() -> ModelConfig:
    """Read the starter-kit model from env/file without exposing it to HTML."""
    name = os.getenv("NGSPICE_MODEL_NAME", "").strip()
    text = ""
    source = "not configured"

    model_file = os.getenv("NGSPICE_MODEL_FILE", "").strip()
    if model_file:
        try:
            text = Path(model_file).read_text(encoding="utf-8").strip()
            source = f"file:{model_file}"
        except OSError as exc:
            return ModelConfig(name, "", f"ERROR reading NGSPICE_MODEL_FILE: {exc}")
    else:
        text = os.getenv("NGSPICE_MODEL_TEXT", "").strip()
        source = "env:NGSPICE_MODEL_TEXT" if text else "not configured"

    if not name and text:
        match = _MODEL_NAME_RE.match(text)
        if match:
            name = match.group(1)

    return ModelConfig(name, text, source)


def describe_model_config() -> dict[str, Any]:
    """Report only the model name/source, never the full model card, to the UI."""
    config = _configured_model()
    return {
        "name": config.name,
        "source": config.source,
        "configured": config.configured,
    }


def effective_model_config(form_name: str = "", form_text: str = "") -> ModelConfig:
    """Merge optional form overrides with the configured starter-kit model."""
    config = _configured_model()
    name = (form_name or "").strip() or config.name
    text = (form_text or "").strip() or config.text
    source = "form:sim_model_text" if (form_text or "").strip() else config.source
    return ModelConfig(name, text, source)


def sanitize_model_text(text: str) -> str:
    """Keep only a single .model card and reject injected analysis directives."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines or not lines[0].lower().startswith(".model"):
        raise SimulationError("Model card ต้องเริ่มด้วยบรรทัด .model")

    for line in lines:
        lowered = line.lower()
        if any(lowered.startswith(directive) for directive in _FORBIDDEN_MODEL_DIRECTIVES):
            raise SimulationError(f"Model card ไม่อนุญาตให้มี directive: {line.split()[0]}")
    return "\n".join(lines)


def build_netlist(params: SimulationInput, *, model_source: str | None = None) -> str:
    """Build exactly one netlist for the selected analysis mode."""
    model = sanitize_model_text(params.model_text)
    source = model_source or params.model_source or "unspecified"

    lines = [
        "* ENG29 2121 Lab 04 - CE Voltage Divider Simulator v1",
        f"* analysis: {params.analysis}",
        f"* model-source: {source}",
        f"VCC vcc 0 DC {_num(params.vcc)}",
        f"R1 vcc base {_num(params.r1)}",
        f"R2 base 0 {_num(params.r2)}",
        f"RC vcc collector {_num(params.rc)}",
        f"RE emitter 0 {_num(params.re)}",
        f"Q1 collector base emitter {params.model_name.strip()}",
        f"Cin input base {_num(params.cin)}",
        f"Cout collector output {_num(params.cout)}",
        f"RL output 0 {_num(params.rl)}",
        (
            f"Vin input 0 DC 0 AC {_num(params.amp)} "
            f"SIN(0 {_num(params.amp)} {_num(params.freq)})"
        ),
        model,
    ]

    if params.analysis == ANALYSIS_DC:
        lines.extend([".op"])
    elif params.analysis == ANALYSIS_AC:
        lines.extend(
            [
                f".ac DEC {int(params.fpoints)} {_num(params.fstart)} {_num(params.fstop)}",
                ".print ac vdb(output) vdb(input) vp(output) vp(input)",
            ]
        )
    elif params.analysis == ANALYSIS_TRANSIENT:
        lines.extend(
            [
                f".tran {_num(params.tstep)} {_num(params.tstop)}",
                ".print tran v(input) v(output)",
            ]
        )
    else:  # pragma: no cover - guarded by validate_params
        raise SimulationError(f"Analysis mode ไม่รู้จัก: {params.analysis}")

    lines.append(".end")
    return "\n".join(lines) + "\n"


def build_command(engine: str, netlist_path: Path, log_path: Path) -> list[str]:
    """Return the batch-mode argv.  Never uses shell=True or string commands."""
    return [engine, "-b", "-o", str(log_path), str(netlist_path)]


def _tokens(line: str) -> list[str]:
    return _NUMBER_RE.findall(line)


def _numbers(line: str) -> list[float]:
    try:
        return [float(token) for token in _tokens(line)]
    except ValueError:
        return []


def _without_index(row: list[float], data_columns: int) -> list[float]:
    """Strip ngspice's leading Index column only when the width expects it."""
    if (
        len(row) == data_columns + 1
        and row[0].is_integer()
        and row[0] >= 0
    ):
        return row[1:]
    return row


def _scientific_count(line: str) -> int:
    """Count exponent-form numbers; ngspice print rows are all scientific."""
    return len(re.findall(r"[-+]?(?:\d+\.?\d*|\.\d+)[eE][-+]?\d+", line))


def _phase_delta_degrees(output_rad: float, input_rad: float) -> float:
    """ngspice `vp()` is in radians; display it as wrapped degrees."""
    delta = math.degrees(output_rad - input_rad)
    if math.isclose(abs(delta), 180.0, abs_tol=1e-3):
        return -180.0
    return (delta + 180.0) % 360.0 - 180.0


def _downsample(series: list[dict[str, float]], limit: int = 300) -> list[dict[str, float]]:
    if len(series) <= limit:
        return series
    step = math.ceil(len(series) / limit)
    return series[::step][:limit]


def _log_tail(text: str, limit: int = 5000) -> str:
    text = text.strip()
    return text[-limit:] if len(text) > limit else text


def parse_dc_log(log_text: str, params: SimulationInput) -> dict[str, Any]:
    """Read node voltages from a real .op log and derive VCE/IC transparently."""
    nodes: dict[str, float] = {}
    for line in log_text.splitlines():
        match = _NODE_RE.match(line)
        if match:
            nodes[match.group(1).lower()] = float(match.group(2))

    required = ("vcc", "base", "emitter", "collector")
    missing = [name for name in required if name not in nodes]
    if missing:
        raise SimulationError(
            "ไม่พบ node voltage จาก ngspice .op log: " + ", ".join(missing)
        )

    vcc = nodes["vcc"]
    vb = nodes["base"]
    ve = nodes["emitter"]
    vc = nodes["collector"]
    vce = vc - ve
    ic = (vcc - vc) / params.rc

    values = {
        "VB": vb,
        "VE": ve,
        "VC": vc,
        "VCE": vce,
        "IC": ic,
    }
    return {
        "values": values,
        "series": [],
        "derived": [
            f"VCE = VC - VE = {vc:.6g} - {ve:.6g} V",
            f"IC = (VCC - VC) / RC = ({vcc:.6g} - {vc:.6g}) / {params.rc:.6g} A",
        ],
        "warnings": [
            "ผล DC มาจาก ngspice .op; IC กับ VCE ถูก derive จาก node voltage จริง"
        ],
    }


def _value_at(
    series: list[dict[str, float]], key: str, target_hz: float
) -> float | None:
    if not series:
        return None
    closest = min(series, key=lambda point: abs(point["freq_hz"] - target_hz))
    return closest[key]


def _gain_db_at(series: list[dict[str, float]], target_hz: float) -> float | None:
    return _value_at(series, "gain_db", target_hz)


def _find_3db_cutoff(series: list[dict[str, float]]) -> tuple[float | None, str]:
    if len(series) < 2:
        return None, "not determined in sweep range"
    peak = max(point["gain_db"] for point in series)
    target = peak - 3.0
    for left, right in zip(series, series[1:]):
        a = left["gain_db"] - target
        b = right["gain_db"] - target
        if a == 0:
            return left["freq_hz"], "estimated by linear interpolation in log(f)"
        if a * b < 0:
            log_f = math.log10(left["freq_hz"]) + (
                -a / (b - a)
            ) * (math.log10(right["freq_hz"]) - math.log10(left["freq_hz"]))
            return 10 ** log_f, "estimated by linear interpolation in log(f)"
    return None, "not determined in sweep range"


def parse_ac_log(log_text: str) -> dict[str, Any]:
    """Read vdb/vp tables written by `.print ac` and compute gain/phase.

    ngspice batch mode does not put all four requested expressions on one line.
    It writes one `Index frequency <expr1> <expr2>` table per expression pair,
    repeating the header after each page break.  We join the two tables by
    frequency.  The older single-row five-column shape is still accepted.
    """
    db_by_frequency: dict[float, tuple[float, float]] = {}
    phase_by_frequency: dict[float, tuple[float, float]] = {}
    legacy_rows: list[list[float]] = []
    kind: str | None = None

    for line in log_text.splitlines():
        if "vdb(" in line and "vp(" not in line:
            kind = "db"
            continue
        if "vp(" in line:
            kind = "phase"
            continue

        if _scientific_count(line) < 2:
            continue
        numbers = _numbers(line)
        if kind is None:
            legacy_row = _without_index(numbers, 5)
            if len(legacy_row) == 5:
                legacy_rows.append(legacy_row)
            continue
        row = _without_index(numbers, 3)
        if len(row) != 3:
            continue
        freq, first, second = row[:3]
        if freq <= 0 or not all(math.isfinite(v) for v in (freq, first, second)):
            continue
        if kind == "db":
            db_by_frequency[freq] = (first, second)
        else:
            phase_by_frequency[freq] = (first, second)

    raw: list[dict[str, float]] = []
    if legacy_rows:
        for row in legacy_rows:
            freq, out_db, in_db, out_phase, in_phase = row[:5]
            if freq <= 0 or not all(math.isfinite(v) for v in row[:5]):
                continue
            raw.append(
                {
                    "freq_hz": freq,
                    "out_db": out_db,
                    "in_db": in_db,
                    "gain_db": out_db - in_db,
                    "phase_deg": _phase_delta_degrees(out_phase, in_phase),
                }
            )
    else:
        for freq in sorted(db_by_frequency.keys() & phase_by_frequency.keys()):
            out_db, in_db = db_by_frequency[freq]
            out_phase, in_phase = phase_by_frequency[freq]
            raw.append(
                {
                    "freq_hz": freq,
                    "out_db": out_db,
                    "in_db": in_db,
                    "gain_db": out_db - in_db,
                    "phase_deg": _phase_delta_degrees(out_phase, in_phase),
                }
            )

    if not raw:
        raise SimulationError(
            "ไม่พบข้อมูลFrequency/Gain/Phase จาก ngspice .ac log "
            "(ตรวจ .print ac ใน netlist)"
        )

    series = _downsample(raw)
    cutoff_hz, cutoff_note = _find_3db_cutoff(raw)
    values = {
        "PeakGain_dB": max(point["gain_db"] for point in raw),
        "GainAt1k_dB": _gain_db_at(raw, 1000.0),
        "PhaseAt1k_deg": _value_at(raw, "phase_deg", 1000.0),
        "Cutoff_Hz": cutoff_hz,
    }
    warnings = [f"-3 dB point: {cutoff_note}"]
    return {
        "values": values,
        "series": series,
        "derived": [
            "Gain(dB) = vdb(output) - vdb(input) โดย join ตาราง .print ac ด้วย frequency",
            "Phase(deg) = degrees(vp(output) - vp(input)) โดย join ตาราง .print ac ด้วย frequency (ngspice vp เป็น radian)",
            "Frequency axis เป็นหน่วย Hz จากคอลัมน์ frequency ของ .print ac",
        ],
        "warnings": warnings,
    }


def parse_tran_log(log_text: str) -> dict[str, Any]:
    """Read time/v(in)/v(out) columns written by `.print tran`."""
    raw: list[dict[str, float]] = []
    for line in log_text.splitlines():
        if _scientific_count(line) < 2:
            continue
        row = _without_index(_numbers(line), 3)
        if len(row) != 3:
            continue
        time_s, vin, vout = row[:3]
        if time_s < 0 or not all(math.isfinite(v) for v in row[:3]):
            continue
        raw.append({"time_s": time_s, "vin_v": vin, "vout_v": vout})

    if not raw:
        raise SimulationError(
            "ไม่พบข้อมูล Time/Vin/Vout จาก ngspice .tran log "
            "(ตรวจ .print tran ใน netlist)"
        )

    series = _downsample(raw)
    vins = [point["vin_v"] for point in raw]
    vouts = [point["vout_v"] for point in raw]
    mean_in = sum(vins) / len(vins)
    mean_out = sum(vouts) / len(vouts)
    cov = sum((a - mean_in) * (b - mean_out) for a, b in zip(vins, vouts))
    var_in = sum((a - mean_in) ** 2 for a in vins)
    var_out = sum((b - mean_out) ** 2 for b in vouts)
    correlation = cov / math.sqrt(var_in * var_out) if var_in and var_out else 0.0
    relation = "inverted" if correlation < -0.3 else "non-inverted"

    values = {
        "VinPeak_V": max(abs(v) for v in vins),
        "VoutPeak_V": max(abs(v) for v in vouts),
        "TimeEnd_s": raw[-1]["time_s"],
        "Correlation": correlation,
        "PhaseRelation": relation,
    }
    return {
        "values": values,
        "series": series,
        "derived": [
            "Time axis เป็นหน่วย s จากคอลัมน์แรกของ .print tran",
            "Vin/Vout เป็นหน่วย V จากคอลัมน์ v(input)/v(output)",
        ],
        "warnings": [
            "ทิศทางเฟสประเมินจาก correlation ระหว่าง Vin กับ Vout "
            "(ไม่ใช่การวัดเฟสเชิงความถี่)"
        ],
    }


def _run_engine(
    params: SimulationInput,
    netlist: str,
    *,
    engine: str,
    runner: Runner,
    timeout: float,
) -> tuple[str, str]:
    with tempfile.TemporaryDirectory(prefix="lab04-ce-") as workdir:
        work = Path(workdir)
        netlist_path = work / "circuit.cir"
        log_path = work / "run.log"
        netlist_path.write_text(netlist, encoding="utf-8")

        command = build_command(engine, netlist_path, log_path)
        try:
            completed = runner(
                command,
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=timeout,
                errors="replace",
            )
        except FileNotFoundError as exc:
            raise SimulationError(
                f"ไม่พบ ngspice executable: {engine} "
                "(ตั้ง NGSPICE_EXECUTABLE หรือเพิ่มลง PATH)"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise SimulationError(
                f"ngspice timeout หลัง {timeout:g} วินาที"
            ) from exc

        log_text = ""
        if log_path.exists():
            log_text = log_path.read_text(encoding="utf-8", errors="replace")
        if not log_text.strip():
            log_text = f"{completed.stdout or ''}\n{completed.stderr or ''}".strip()

        if completed.returncode != 0:
            raise SimulationError(
                f"ngspice run fail (code {completed.returncode}): "
                f"{_log_tail(log_text, 1200)}"
            )
        if re.search(
            r"fatal error|unknown model|no such model|unable to find|"
            r"could not open|unrecognized",
            log_text,
            re.IGNORECASE,
        ):
            raise SimulationError(f"ngspice รายงานข้อผิดพลาด: {_log_tail(log_text, 1200)}")
        if not log_text.strip():
            raise SimulationError("ngspice log ว่าง — ไม่มีผลจำลองให้แสดง")

        return log_text, netlist


def simulate(
    params: SimulationInput,
    *,
    engine: str | None = None,
    runner: Runner | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Run one real ngspice analysis and return parsed, provenance-tagged data."""
    validate_params(params)
    netlist = build_netlist(params)
    engine = engine or os.getenv("NGSPICE_EXECUTABLE", "ngspice")
    runner = runner or subprocess.run

    log_text, netlist = _run_engine(
        params, netlist, engine=engine, runner=runner, timeout=timeout
    )

    if params.analysis == ANALYSIS_DC:
        parsed = parse_dc_log(log_text, params)
    elif params.analysis == ANALYSIS_AC:
        parsed = parse_ac_log(log_text)
    else:
        parsed = parse_tran_log(log_text)

    return {
        "status": "success",
        "engine": "ngspice",
        "analysis": params.analysis,
        "analysis_label": ANALYSIS_LABELS[params.analysis],
        "model_name": params.model_name.strip(),
        "model_source": params.model_source,
        "provenance": "ngspice batch log (-o) parsed by spice_engine.py",
        "values": parsed["values"],
        "series": parsed["series"],
        "derived": parsed["derived"],
        "warnings": parsed["warnings"],
        "log_excerpt": _log_tail(log_text),
        "netlist": netlist,
    }
