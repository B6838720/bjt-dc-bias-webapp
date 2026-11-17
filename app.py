"""Flask entry point: HTTP routes only, no engineering formulas."""

import math

from flask import Flask, render_template, request

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


def format_voltage(v):
    return f"{v:.3f} V"


def format_current(a):
    if a == 0 or abs(a) >= 1e-3:
        return f"{a * 1e3:.3f} mA"
    return f"{a * 1e6:.2f} µA"


app.add_template_filter(format_voltage, "voltage")
app.add_template_filter(format_current, "current")


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


@app.get("/")
def index():
    mode = request.args.get("mode", MODE_DIVIDER)
    if mode not in MODE_FIELDS:
        mode = MODE_DIVIDER
    form = dict(DEFAULT_FORM, mode=mode)
    return render_template("index.html", form=form, result=None, error=None, mode=mode)


@app.post("/calculate")
def calculate_route():
    mode = request.form.get("mode") or request.args.get("mode") or MODE_DIVIDER
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
        return render_template(
            "index.html", form=form, result=None, error=str(exc), mode=mode
        )
    return render_template(
        "index.html", form=form, result=result, error=None, mode=mode
    )


if __name__ == "__main__":
    app.run(debug=True)
