"""BJT DC bias calculations (voltage-divider bias, forward-active model).

Pure functions only: no Flask, no HTTP, no HTML.
Units: volts, amps, ohms.
"""

REGION_ACTIVE = "forward_active"
REGION_CUTOFF = "cutoff"
REGION_SATURATION = "saturation"


def calculate(vcc, r1, r2, rc, re, beta, vbe):
    """Return the DC operating point of a voltage-divider biased BJT."""
    vth = vcc * r2 / (r1 + r2)
    rth = r1 * r2 / (r1 + r2)

    ib = (vth - vbe) / (rth + (beta + 1) * re)
    ic = beta * ib
    ie = (beta + 1) * ib

    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    return {
        "vth": vth,
        "rth": rth,
        "ib": ib,
        "ic": ic,
        "ie": ie,
        "vb": vb,
        "ve": ve,
        "vc": vc,
        "vce": vce,
        "region": REGION_ACTIVE,
        "model_applies": True,
        "warnings": [],
    }
