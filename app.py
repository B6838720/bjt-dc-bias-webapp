"""Flask entry point: HTTP routes only, no engineering formulas."""

from flask import Flask, render_template

from dc_bias import REGION_ACTIVE, REGION_CUTOFF, REGION_SATURATION, calculate  # noqa: F401

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


def format_voltage(v):
    return f"{v:.3f} V"


def format_current(a):
    if abs(a) >= 1e-3:
        return f"{a * 1e3:.3f} mA"
    return f"{a * 1e6:.2f} µA"


app.add_template_filter(format_voltage, "voltage")
app.add_template_filter(format_current, "current")


@app.get("/")
def index():
    return render_template("index.html", form=DEFAULT_FORM, result=None, error=None)


if __name__ == "__main__":
    app.run(debug=True)
