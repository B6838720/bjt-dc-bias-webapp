"""Flask entry point: HTTP routes only, no engineering formulas."""

from flask import Flask, render_template, request

from dc_bias import calculate

app = Flask(__name__)

DEFAULT_FORM = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "beta": "100",
    "vbe": "0.70",
    "r_unit": "kohm",
}

FIELD_LABELS = {
    "vcc": "VCC",
    "r1": "R1",
    "r2": "R2",
    "rc": "RC",
    "re": "RE",
    "beta": "β",
    "vbe": "VBE",
}
RESISTOR_FIELDS = ("r1", "r2", "rc", "re")


def format_voltage(v):
    return f"{v:.3f} V"


def format_current(a):
    if a == 0 or abs(a) >= 1e-3:
        return f"{a * 1e3:.3f} mA"
    return f"{a * 1e6:.2f} µA"


app.add_template_filter(format_voltage, "voltage")
app.add_template_filter(format_current, "current")


def _parse_form(form):
    """Turn the submitted strings into SI floats (ohms, volts)."""
    unit_multiplier = 1000.0 if form.get("r_unit", "kohm") == "kohm" else 1.0
    values = {}
    for field, label in FIELD_LABELS.items():
        raw = (form.get(field) or "").strip()
        if raw == "":
            raise ValueError(f"กรุณากรอก {label}")
        try:
            number = float(raw)
        except ValueError:
            raise ValueError(f"กรุณากรอก {label} เป็นตัวเลข") from None
        values[field] = number * unit_multiplier if field in RESISTOR_FIELDS else number
    return values


@app.get("/")
def index():
    return render_template("index.html", form=DEFAULT_FORM, result=None, error=None)


@app.post("/calculate")
def calculate_route():
    form = {field: request.form.get(field, "") for field in FIELD_LABELS}
    form["r_unit"] = request.form.get("r_unit", "kohm")
    try:
        values = _parse_form(form)
        result = calculate(**values)
    except ValueError as exc:
        return render_template("index.html", form=form, result=None, error=str(exc))
    return render_template("index.html", form=form, result=result, error=None)


if __name__ == "__main__":
    app.run(debug=True)
