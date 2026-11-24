"""Flask entry point: HTTP routes only, no engineering formulas."""

import math

from flask import Flask, render_template, request

import spice_engine
from dc_bias import calculate, calculate_emitter, calculate_fixed

app = Flask(__name__)

MODE_DIVIDER = "divider"
MODE_FIXED = "fixed"
MODE_EMITTER = "emitter"

MODE_NAMES = {
    MODE_DIVIDER: "Voltage Divider Bias",
    MODE_FIXED: "Fixed Bias",
    MODE_EMITTER: "Emitter Bias",
}

MODE_FIELDS = {
    MODE_DIVIDER: ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"),
    MODE_FIXED: ("vcc", "rb", "rc", "beta", "vbe"),
    MODE_EMITTER: ("vcc", "rb", "rc", "re", "beta", "vbe"),
}

FIELD_LABELS = {
    "vcc": "VCC",
    "r1": "R1",
    "r2": "R2",
    "rb": "RB",
    "rc": "RC",
    "re": "RE",
    "beta": "β",
    "vbe": "VBE",
}
RESISTOR_FIELDS = ("r1", "r2", "rb", "rc", "re")

DEFAULT_FORM = {
    "mode": MODE_DIVIDER,
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rb": "1000",
    "rc": "2.2",
    "re": "1",
    "beta": "100",
    "vbe": "0.70",
    "r_unit": "kohm",
}

ANALYSIS_NAMES = {
    spice_engine.ANALYSIS_DC: "DC · .op",
    spice_engine.ANALYSIS_AC: "AC · .ac",
    spice_engine.ANALYSIS_TRANSIENT: "Transient · .tran",
}

# UI units: kΩ, µF, mV, µs, ms.  app.py converts them to SI before calling
# spice_engine; spice_engine never sees form strings or unit suffixes.
DEFAULT_SIM_FORM = {
    "sim_vcc": "12",
    "sim_r1": "100",
    "sim_r2": "22",
    "sim_rc": "2.2",
    "sim_re": "1",
    "sim_rl": "10",
    "sim_cin": "10",
    "sim_cout": "10",
    "sim_amp": "10",
    "sim_freq": "1000",
    "sim_beta": "100",
    "sim_vbe": "0.70",
    "sim_fstart": "1",
    "sim_fstop": "10000000",
    "sim_fpoints": "20",
    "sim_tstep": "1",
    "sim_tstop": "5",
    "sim_model_name": "",
    "sim_model_text": "",
}

SIM_FIELDS = {
    "sim_vcc": ("VCC", 1.0),
    "sim_r1": ("R1", 1000.0),
    "sim_r2": ("R2", 1000.0),
    "sim_rc": ("RC", 1000.0),
    "sim_re": ("RE", 1000.0),
    "sim_rl": ("RL", 1000.0),
    "sim_cin": ("Cin", 1e-6),
    "sim_cout": ("Cout", 1e-6),
    "sim_amp": ("Amplitude", 1e-3),
    "sim_freq": ("Frequency", 1.0),
    "sim_beta": ("β", 1.0),
    "sim_vbe": ("VBE", 1.0),
    "sim_fstart": ("Fstart", 1.0),
    "sim_fstop": ("Fstop", 1.0),
    "sim_tstep": ("Tstep", 1e-6),
    "sim_tstop": ("Tstop", 1e-3),
}


def format_voltage(v):
    return f"{v:.3f} V"


def format_current(a):
    if a == 0 or abs(a) >= 1e-3:
        return f"{a * 1e3:.3f} mA"
    return f"{a * 1e6:.2f} µA"


def format_number(value, spec=".3f"):
    if value is None:
        return "—"
    try:
        return format(value, spec)
    except (TypeError, ValueError):
        return str(value)


app.add_template_filter(format_voltage, "voltage")
app.add_template_filter(format_current, "current")
app.add_template_filter(format_number, "number")


def _parse_form(form, mode):
    """Turn the submitted strings into SI floats (ohms, volts) for one mode."""
    if mode not in MODE_FIELDS:
        raise ValueError(f"{mode}: โหมดไม่รู้จัก")
    unit_multiplier = 1000.0 if form.get("r_unit", "kohm") == "kohm" else 1.0
    values = {}
    for field in MODE_FIELDS[mode]:
        raw = (form.get(field) or "").strip()
        label = FIELD_LABELS[field]
        if raw == "":
            raise ValueError(f"{MODE_NAMES[mode]}: กรุณากรอก {label}")
        try:
            number = float(raw)
        except ValueError:
            raise ValueError(f"{MODE_NAMES[mode]}: กรุณากรอก {label} เป็นตัวเลข") from None
        if not math.isfinite(number):
            raise ValueError(f"{MODE_NAMES[mode]}: กรุณากรอก {label}เป็นจำนวนจำกัด")
        values[field] = number * unit_multiplier if field in RESISTOR_FIELDS else number
    return values


def _parse_sim_form(form):
    """Convert the CE simulator form into SI values for spice_engine."""
    values = {}
    for field, (label, multiplier) in SIM_FIELDS.items():
        raw = (form.get(field) or "").strip()
        if raw == "":
            raise ValueError(f"กรุณากรอก {label}")
        try:
            number = float(raw)
        except ValueError:
            raise ValueError(f"กรุณากรอก {label} เป็นตัวเลข") from None
        if not math.isfinite(number):
            raise ValueError(f"กรุณากรอก {label}เป็นจำนวนจำกัด")
        values[field] = number * multiplier

    raw_points = (form.get("sim_fpoints") or "").strip()
    if not raw_points.isdigit():
        raise ValueError("กรุณากรอก Fpoints เป็นจำนวนเต็มบวก")
    values["fpoints"] = int(raw_points)

    return {
        "vcc": values["sim_vcc"],
        "r1": values["sim_r1"],
        "r2": values["sim_r2"],
        "rc": values["sim_rc"],
        "re": values["sim_re"],
        "rl": values["sim_rl"],
        "cin": values["sim_cin"],
        "cout": values["sim_cout"],
        "amp": values["sim_amp"],
        "freq": values["sim_freq"],
        "beta": values["sim_beta"],
        "vbe": values["sim_vbe"],
        "fstart": values["sim_fstart"],
        "fstop": values["sim_fstop"],
        "fpoints": values["fpoints"],
        "tstep": values["sim_tstep"],
        "tstop": values["sim_tstop"],
    }


def _chart_polyline(points, x_key, y_key, *, log_x=False, width=640, height=230):
    if len(points) < 2:
        return ""
    xs = [point[x_key] for point in points]
    ys = [point[y_key] for point in points]
    if log_x:
        xs = [math.log10(value) for value in xs if value > 0]
        if len(xs) < 2:
            return ""
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    if xmax == xmin:
        xmax = xmin + 1
    if ymax == ymin:
        ymin -= 1
        ymax += 1
    pad_x, pad_y = 44, 30

    def sx(value):
        x = math.log10(value) if log_x else value
        return pad_x + (x - xmin) / (xmax - xmin) * (width - 2 * pad_x)

    def sy(value):
        return height - pad_y - (value - ymin) / (ymax - ymin) * (height - 2 * pad_y)

    return " ".join(
        f"{sx(point[x_key]):.1f},{sy(point[y_key]):.1f}" for point in points
    )


def _build_charts(sim_result):
    if not sim_result or sim_result.get("status") != "success":
        return {}
    analysis = sim_result.get("analysis")
    series = sim_result.get("series") or []
    if analysis == spice_engine.ANALYSIS_AC:
        return {
            "kind": "ac",
            "gain": {
                "polyline": _chart_polyline(series, "freq_hz", "gain_db", log_x=True),
                "y_label": "Gain (dB)",
            },
            "phase": {
                "polyline": _chart_polyline(series, "freq_hz", "phase_deg", log_x=True),
                "y_label": "Phase (°)",
            },
        }
    if analysis == spice_engine.ANALYSIS_TRANSIENT:
        points = [
            {
                "time_ms": point["time_s"] * 1000.0,
                "vin_v": point["vin_v"],
                "vout_v": point["vout_v"],
            }
            for point in series
        ]
        return {
            "kind": "transient",
            "wave": {
                "vin": _chart_polyline(points, "time_ms", "vin_v"),
                "vout": _chart_polyline(points, "time_ms", "vout_v"),
                "y_label": "Voltage (V)",
            },
        }
    return {}


def _render(
    *,
    form=None,
    result=None,
    error=None,
    mode=MODE_DIVIDER,
    analysis=spice_engine.ANALYSIS_DC,
    sim_form=None,
    sim_result=None,
    sim_error=None,
    analytical=None,
):
    model_config = spice_engine.describe_model_config()
    current_sim_form = dict(DEFAULT_SIM_FORM)
    current_sim_form.update(sim_form or {})
    if not current_sim_form.get("sim_model_name") and model_config["name"]:
        current_sim_form["sim_model_name"] = model_config["name"]

    return render_template(
        "index.html",
        form=form or dict(DEFAULT_FORM),
        result=result,
        error=error,
        mode=mode,
        analysis=analysis,
        analyses=ANALYSIS_NAMES,
        sim_form=current_sim_form,
        sim_result=sim_result,
        sim_error=sim_error,
        analytical=analytical,
        model_config=model_config,
        charts=_build_charts(sim_result),
    )


@app.get("/")
def index():
    mode = request.args.get("mode", MODE_DIVIDER)
    if mode not in MODE_FIELDS:
        mode = MODE_DIVIDER
    analysis = request.args.get("analysis", spice_engine.ANALYSIS_DC)
    if analysis not in ANALYSIS_NAMES:
        analysis = spice_engine.ANALYSIS_DC
    return _render(mode=mode, analysis=analysis)


@app.post("/calculate")
def calculate_route():
    mode = request.form.get("mode") or request.args.get("mode") or MODE_DIVIDER
    analysis = request.form.get("analysis") or request.args.get("analysis") or spice_engine.ANALYSIS_DC
    if analysis not in ANALYSIS_NAMES:
        analysis = spice_engine.ANALYSIS_DC
    form = {field: request.form.get(field, "") for field in FIELD_LABELS}
    form["mode"] = mode
    form["r_unit"] = request.form.get("r_unit", "kohm")
    try:
        values = _parse_form(form, mode)
        if mode == MODE_FIXED:
            result = calculate_fixed(
                vcc=values["vcc"], rb=values["rb"], rc=values["rc"],
                beta=values["beta"], vbe=values["vbe"],
            )
        elif mode == MODE_EMITTER:
            result = calculate_emitter(
                vcc=values["vcc"], rb=values["rb"], rc=values["rc"],
                re=values["re"], beta=values["beta"], vbe=values["vbe"],
            )
        elif mode == MODE_DIVIDER:
            result = calculate(**values)
        else:
            raise ValueError(f"{mode}: โหมดไม่รู้จัก")
    except ValueError as exc:
        return _render(
            form=form, result=None, error=str(exc), mode=mode, analysis=analysis
        )
    return _render(form=form, result=result, error=None, mode=mode, analysis=analysis)


@app.post("/simulate")
def simulate_route():
    analysis = request.form.get("analysis") or spice_engine.ANALYSIS_DC
    if analysis not in ANALYSIS_NAMES:
        analysis = spice_engine.ANALYSIS_DC

    mode = request.form.get("mode") or MODE_DIVIDER
    if mode not in MODE_FIELDS:
        mode = MODE_DIVIDER

    sim_form = {field: request.form.get(field, default) for field, default in DEFAULT_SIM_FORM.items()}
    sim_form["analysis"] = analysis

    try:
        si_values = _parse_sim_form(sim_form)
        model_config = spice_engine.effective_model_config(
            sim_form.get("sim_model_name", ""),
            sim_form.get("sim_model_text", ""),
        )
        params = spice_engine.SimulationInput(
            analysis=analysis,
            model_name=model_config.name,
            model_text=model_config.text,
            model_source=model_config.source,
            **si_values,
        )
        sim_result = spice_engine.simulate(params)
    except (ValueError, spice_engine.SimulationError) as exc:
        return _render(
            mode=mode,
            analysis=analysis,
            sim_form=sim_form,
            sim_error=str(exc),
            sim_result=None,
        )

    analytical = None
    try:
        analytical = calculate(
            vcc=si_values["vcc"],
            r1=si_values["r1"],
            r2=si_values["r2"],
            rc=si_values["rc"],
            re=si_values["re"],
            beta=si_values["beta"],
            vbe=si_values["vbe"],
        )
    except ValueError:
        analytical = None

    return _render(
        mode=mode,
        analysis=analysis,
        sim_form=sim_form,
        sim_result=sim_result,
        analytical=analytical,
    )


if __name__ == "__main__":
    app.run(debug=True)
