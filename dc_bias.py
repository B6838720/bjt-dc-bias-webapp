"""BJT DC bias calculations (voltage-divider bias, forward-active model).

Pure functions only: no Flask, no HTTP, no HTML.
Units: volts, amps, ohms.
"""

import math

REGION_ACTIVE = "forward_active"
REGION_CUTOFF = "cutoff"
REGION_SATURATION = "saturation"

SATURATION_VCE_LIMIT = 0.3

WARNING_CUTOFF = (
    "ทรานซิสเตอร์อยู่ในสภาวะ Cutoff: ค่าที่แสดงเป็นค่าจริงของวงจร "
    "ไม่ได้มาจากสมการ Forward-Active"
)
WARNING_SATURATION = (
    "ทรานซิสเตอร์อยู่ในสภาวะ Saturation: สมการ Forward-Active ใช้ไม่ได้ "
    "ผลอาจคลาดเคลื่อน"
)
WARNING_LOW_BETA = "ค่า β ต่ำผิดปกติ"
WARNING_NONPOSITIVE_IB = "กระแสฐานคำนวณได้ไม่มากกว่า 0: แบบจำลอง Forward Active อาจใช้ไม่ได้"


def _validate(vcc, r1, r2, rc, re, beta, vbe):
    """Reject inputs that cannot describe a working circuit."""
    if vcc <= 0:
        raise ValueError("VCC ต้องมากกว่า 0")
    for name, value in (("R1", r1), ("R2", r2), ("RC", rc), ("RE", re)):
        if value <= 0:
            raise ValueError(f"ค่า {name} ต้องมากกว่า 0")
    if r1 + r2 <= 0:
        raise ValueError("R1 + R2 ต้องมากกว่า 0")
    if beta <= 0:
        raise ValueError("β ต้องมากกว่า 0")
    if vbe <= 0 or vbe >= vcc:
        raise ValueError("VBE ต้องอยู่ระหว่าง 0 ถึง VCC")


def _detect_region(vth, vbe, vce):
    """Classify the operating region. Order matters: cutoff wins over saturation."""
    if vth <= vbe:
        return REGION_CUTOFF
    if vce < SATURATION_VCE_LIMIT:
        return REGION_SATURATION
    return REGION_ACTIVE


def _validate_common(vcc, rc, beta, vbe):
    """Shared physical checks for every bias topology."""
    if vcc <= 0:
        raise ValueError("VCC ต้องมากกว่า 0")
    if rc <= 0:
        raise ValueError("ค่า RC ต้องมากกว่า 0")
    if beta <= 0:
        raise ValueError("β ต้องมากกว่า 0")
    if vbe <= 0 or vbe >= vcc:
        raise ValueError("VBE ต้องอยู่ระหว่าง 0 ถึง VCC")


def _summarize(ib, re, vcc, rc, beta, vbe, source, vth=None, rth=None):
    """Finish the operating point from IB using the shared forward-active model."""
    ic = beta * ib
    ie = (beta + 1) * ib

    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    raw = [ib, ic, ie, vb, ve, vc, vce]
    if vth is not None:
        raw.extend((vth, rth))
    if not all(math.isfinite(value) for value in raw):
        raise ValueError("ค่าอินพุตทำให้ผลลัพธ์ไม่สมเหตุสมผล")

    region = _detect_region(source, vbe, vce)

    if region == REGION_CUTOFF:
        # The transistor is off: report the circuit's physical state instead of
        # the forward-active formulas, which would produce negative currents.
        ib = ic = ie = 0.0
        ve = 0.0
        vb = source
        vc = vcc
        vce = vcc

    warnings = []
    if region == REGION_CUTOFF:
        warnings.append(WARNING_CUTOFF)
    elif region == REGION_SATURATION:
        warnings.append(WARNING_SATURATION)
    if ib <= 0 and region != REGION_CUTOFF:
        warnings.append(WARNING_NONPOSITIVE_IB)
    if beta < 1:
        warnings.append(WARNING_LOW_BETA)

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
        "region": region,
        "model_applies": region == REGION_ACTIVE,
        "warnings": warnings,
    }


def calculate(vcc, r1, r2, rc, re, beta, vbe):
    """Return the DC operating point of a voltage-divider biased BJT."""
    _validate(vcc, r1, r2, rc, re, beta, vbe)

    vth = vcc * r2 / (r1 + r2)
    rth = r1 * r2 / (r1 + r2)

    ib = (vth - vbe) / (rth + (beta + 1) * re)
    return _summarize(ib, re, vcc, rc, beta, vbe, vth, vth=vth, rth=rth)


def calculate_fixed(vcc, rb, rc, beta, vbe):
    """Return the DC operating point of a fixed-bias BJT (emitter grounded)."""
    _validate_common(vcc, rc, beta, vbe)
    if rb <= 0:
        raise ValueError("ค่า RB ต้องมากกว่า 0")
    ib = (vcc - vbe) / rb
    return _summarize(ib, 0.0, vcc, rc, beta, vbe, vcc)


def calculate_emitter(vcc, rb, rc, re, beta, vbe):
    """Return the DC operating point of a single-supply emitter-bias BJT."""
    _validate_common(vcc, rc, beta, vbe)
    if rb <= 0:
        raise ValueError("ค่า RB ต้องมากกว่า 0")
    if re <= 0:
        raise ValueError("ค่า RE ต้องมากกว่า 0")
    ib = (vcc - vbe) / (rb + (beta + 1) * re)
    return _summarize(ib, re, vcc, rc, beta, vbe, vcc)
