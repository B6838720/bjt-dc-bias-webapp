# BJT DC Bias Web App — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** สร้าง Flask Web App ที่รับค่า VCC, R1, R2, RC, RE, β, VBE แล้วให้ Python คำนวณ DC Operating Point ของ BJT Common-Emitter (Voltage-Divider Bias) และแสดงผลใน Browser พร้อม validation, region warning และ automated tests

**Architecture:** แยก 3 ชั้นชัดเจน — `dc_bias.py` (สมการบริสุทธิ์, ไม่ import Flask), `app.py` (HTTP/parsing เท่านั้น), `templates/index.html` + `static/style.css` (การนำเสนอ ไม่มีสมการ) ทดสอบด้วย `unittest` ทั้งระดับสมการและ HTTP

**Tech Stack:** Python 3.15.2, Flask 3.1.3, Jinja2, CSS ธรรมดา, `unittest`

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-dc-bias-webapp-design.md`

## Global Constraints

- ขอบเขต **DC Bias เท่านั้น** — ห้ามเพิ่ม AC / Bode / Transient / Signal Generator / Overlay / SPICE
- `dc_bias.py` **ห้าม** import `flask` หรือรู้จัก HTTP/HTML
- `templates/index.html` **ห้าม** มีสมการฟิสิกส์
- `app.py` **ห้าม** มีสมการฟิสิกส์
- หน่วยภายในของ `dc_bias.calculate()`: **V, A, Ω** (SI) — แปลงเป็น mA/µA ที่ชั้น presentation เท่านั้น
- ข้อความ error/warning เป็น **ภาษาไทย**
- ตัวต้านทานรับหน่วยจาก dropdown กลาง 1 ตัว: `ohm` หรือ `kohm` (kΩ = ×1000)
- รันคำสั่งทั้งหมดจาก project root: `C:\Users\B6838720\Documents\GitHub\BJT DC Bias Web App`
- ใช้ `python -m unittest discover -s tests -v` (ไม่ใช้ pytest)
- ห้าม commit `.venv/`, `__pycache__/`, `.env`
- ค่าคงที่ region: `REGION_ACTIVE = "forward_active"`, `REGION_CUTOFF = "cutoff"`, `REGION_SATURATION = "saturation"`

## Review Focus

1. **ค่าว่าง / ไม่ใช่ตัวเลข** (`vcc=abc`, ช่องว่าง) — ผู้ใช้คาดเห็นข้อความไทยบนหน้าเว็บ ไม่ใช่ HTTP 500
2. **`R1 + R2 = 0`** (ทั้งคู่ 0) — หารศูนย์ ต้องได้ `ValueError` ไม่ใช่ `ZeroDivisionError` หลุดเป็น 500
3. **ค่าสุดขั้วจนเกิด `inf`/`nan`** (`r1=1e308, r2=1e308`) — ต้องถูกปฏิเสธด้วยข้อความ ไม่แสดง `nan V` บนหน้าจอ
4. **Cutoff ที่สมการให้กระแสติดลบ** — ผู้ใช้คาดเห็น `IC = 0` ไม่ใช่ `IC = −1.2 mA`
5. **`VBE ≥ VCC`** — ผู้ใช้คาดเห็น error ชัดเจน ไม่ใช่ผลคำนวณที่ดูปกติแต่ผิด
6. **`β` เป็นทศนิยม** (`100.5`) — ต้องคำนวณได้ ไม่ถูกปฏิเสธ

---

### Task 1: แกนสมการ DC Bias + โครงโปรเจกต์

**Files:**
- Create: `.gitignore`
- Create: `requirements.txt`
- Create: `dc_bias.py`
- Create: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: ไม่มี (task แรก)
- Produces:
  - `dc_bias.calculate(vcc: float, r1: float, r2: float, rc: float, re: float, beta: float, vbe: float) -> dict`
  - คีย์ที่คืน: `vth, rth` (Ω), `ib, ic, ie` (A), `vb, ve, vc, vce` (V), `region: str`, `model_applies: bool`, `warnings: list[str]`
  - ค่าคงที่: `REGION_ACTIVE`, `REGION_CUTOFF`, `REGION_SATURATION`

- [ ] **Step 1: สร้างไฟล์ตั้งต้นของโปรเจกต์**

`.gitignore`:
```gitignore
__pycache__/
*.py[cod]
.venv/
venv/
.env
*.key
*.pem
.vscode/
.idea/
.DS_Store
Thumbs.db
```

`requirements.txt`:
```
Flask==3.1.3
```

- [ ] **Step 2: เขียน failing test ของค่าอ้างอิง**

`tests/test_dc_bias.py`:
```python
import unittest

from dc_bias import REGION_ACTIVE, calculate

REFERENCE = dict(
    vcc=12.0, r1=100_000.0, r2=22_000.0,
    rc=2_200.0, re=1_000.0, beta=100.0, vbe=0.70,
)


class TestReferenceOperatingPoint(unittest.TestCase):
    def test_reference_operating_point(self):
        r = calculate(**REFERENCE)
        self.assertAlmostEqual(r["vth"], 2.1639, places=3)
        self.assertAlmostEqual(r["rth"], 18_032.79, places=1)
        self.assertAlmostEqual(r["ib"] * 1e6, 12.298, places=2)
        self.assertAlmostEqual(r["ic"] * 1e3, 1.2298, places=3)
        self.assertAlmostEqual(r["ie"] * 1e3, 1.2421, places=3)
        self.assertAlmostEqual(r["vb"], 1.9421, places=3)
        self.assertAlmostEqual(r["ve"], 1.2421, places=3)
        self.assertAlmostEqual(r["vc"], 9.2943, places=3)
        self.assertAlmostEqual(r["vce"], 8.0522, places=3)
        self.assertEqual(r["region"], REGION_ACTIVE)
        self.assertTrue(r["model_applies"])
        self.assertEqual(r["warnings"], [])
```

- [ ] **Step 3: รัน test ให้เห็นว่า fail**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dc_bias'`

- [ ] **Step 4: เขียน `dc_bias.py`**

```python
"""BJT DC bias calculations (voltage-divider bias, forward-active model).

Pure functions only: no Flask, no HTTP, no HTML.
Units: volts, amps, ohms.
"""

REGION_ACTIVE = "forward_active"
REGION_CUTOFF = "cutoff"
REGION_SATURATION = "saturation"


def calculate(vcc, r1, r2, rc, re, beta, vbe):
    ...
```

ลอจิกที่ต้องเขียน (ลำดับตามสมการใน spec 6.2):
1. `vth = vcc * r2 / (r1 + r2)`, `rth = r1 * r2 / (r1 + r2)`
2. `ib = (vth - vbe) / (rth + (beta + 1) * re)` → `ic = beta * ib` → `ie = (beta + 1) * ib`
3. `ve = ie * re` → `vb = ve + vbe` → `vc = vcc - ic * rc` → `vce = vc - ve`
4. `region = REGION_ACTIVE`, `model_applies = True`, `warnings = []` (ใน task นี้ยังไม่มี validation/region logic)

- [ ] **Step 5: รัน test ให้ผ่าน**

Run: `python -m unittest discover -s tests -v`
Expected: PASS 1 test

- [ ] **Step 6: Commit (ผ่าน GitHub Desktop)**

ไฟล์ที่ต้องเข้า commit: `.gitignore`, `requirements.txt`, `dc_bias.py`, `tests/test_dc_bias.py`
Summary: `Add DC bias calculation module with reference test`

---

### Task 2: Validation + Region Detection + ค่าจริงในสภาวะ Cutoff

**Files:**
- Modify: `dc_bias.py`
- Modify: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: `calculate()` จาก Task 1 (signature เดิม ไม่เปลี่ยน)
- Produces: `calculate()` เพิ่มพฤติกรรม
  - raise `ValueError` เมื่อ `vcc <= 0`, `r* <= 0`, `beta <= 0`, `vbe <= 0`, `vbe >= vcc`, `r1 + r2 <= 0`, หรือผลลัพธ์เป็น `inf`/`nan`
  - `region` เป็นหนึ่งใน `REGION_CUTOFF` / `REGION_SATURATION` / `REGION_ACTIVE`
  - `model_applies = (region == REGION_ACTIVE)`
  - ในสภาวะ Cutoff: `ib = ic = ie = 0.0`, `ve = 0.0`, `vb = vth`, `vc = vcc`, `vce = vcc`
  - `warnings` มีข้อความไทยเมื่อ `beta < 1` หรือ region ไม่ใช่ active

- [ ] **Step 1: เขียน failing tests**

เพิ่มใน `tests/test_dc_bias.py`:
```python
from dc_bias import REGION_CUTOFF, REGION_SATURATION, calculate


class TestValidation(unittest.TestCase):
    def test_zero_resistor_rejected(self):
        with self.assertRaises(ValueError):
            calculate(vcc=12.0, r1=0.0, r2=22_000.0, rc=2_200.0,
                      re=1_000.0, beta=100.0, vbe=0.70)

    def test_zero_beta_rejected(self):
        with self.assertRaises(ValueError):
            calculate(vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_200.0,
                      re=1_000.0, beta=0.0, vbe=0.70)

    def test_vbe_not_below_vcc_rejected(self):
        with self.assertRaises(ValueError):
            calculate(vcc=0.5, r1=100_000.0, r2=22_000.0, rc=2_200.0,
                      re=1_000.0, beta=100.0, vbe=0.70)

    def test_zero_divider_rejected(self):
        with self.assertRaises(ValueError):
            calculate(vcc=12.0, r1=0.0, r2=0.0, rc=2_200.0,
                      re=1_000.0, beta=100.0, vbe=0.70)

    def test_overflowing_inputs_rejected(self):
        with self.assertRaises(ValueError):
            calculate(vcc=12.0, r1=1e308, r2=1e308, rc=2_200.0,
                      re=1_000.0, beta=100.0, vbe=0.70)


class TestRegions(unittest.TestCase):
    def test_cutoff_reports_physical_values(self):
        r = calculate(vcc=12.0, r1=100_000.0, r2=5_000.0, rc=2_200.0,
                      re=1_000.0, beta=100.0, vbe=0.70)
        self.assertEqual(r["region"], REGION_CUTOFF)
        self.assertFalse(r["model_applies"])
        self.assertEqual(r["ic"], 0.0)
        self.assertEqual(r["ie"], 0.0)
        self.assertEqual(r["ib"], 0.0)
        self.assertEqual(r["ve"], 0.0)
        self.assertAlmostEqual(r["vc"], 12.0, places=6)
        self.assertAlmostEqual(r["vce"], 12.0, places=6)
        self.assertAlmostEqual(r["vb"], r["vth"], places=6)
        self.assertTrue(r["warnings"])

    def test_saturation_detected(self):
        r = calculate(vcc=12.0, r1=100_000.0, r2=22_000.0, rc=100_000.0,
                      re=1_000.0, beta=100.0, vbe=0.70)
        self.assertEqual(r["region"], REGION_SATURATION)
        self.assertFalse(r["model_applies"])
        self.assertLess(r["vce"], 0.3)
        self.assertTrue(r["warnings"])

    def test_fractional_beta_accepted(self):
        r = calculate(vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_200.0,
                      re=1_000.0, beta=100.5, vbe=0.70)
        self.assertGreater(r["ic"], 0.0)
```

- [ ] **Step 2: รัน test ให้เห็นว่า fail**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL — `TestValidation` ไม่ raise, `TestRegions` ได้ `forward_active` ไม่ใช่ cutoff/saturation

- [ ] **Step 3: เพิ่ม validation และ region logic ใน `dc_bias.py`**

โครงที่ต้องได้:
```python
def _validate(vcc, r1, r2, rc, re, beta, vbe):
    # raise ValueError พร้อมข้อความไทยตาม spec 6.3
    ...

def _detect_region(vth, vbe, vce):
    if vth <= vbe:
        return REGION_CUTOFF
    if vce < 0.3:
        return REGION_SATURATION
    return REGION_ACTIVE
```

ใน `calculate()`:
1. เรียก `_validate(...)` ก่อนคำนวณ
2. คำนวณตาม Task 1
3. `region = _detect_region(vth, vbe, vce)`
4. ถ้า `region == REGION_CUTOFF` ให้ override: `ib = ic = ie = 0.0`, `ve = 0.0`, `vb = vth`, `vc = vcc`, `vce = vcc`
5. ตรวจ `math.isfinite()` ของทุกค่าตัวเลข → ถ้าไม่ใช่ raise `ValueError("ค่าอินพุตทำให้ผลลัพธ์ไม่สมเหตุสมผล")`
6. `model_applies = region == REGION_ACTIVE`
7. `warnings`: ถ้า `region == REGION_CUTOFF` → `"ทรานซิสเตอร์อยู่ในสภาวะ Cutoff: ค่าที่แสดงเป็นค่าจริงของวงจร ไม่ได้มาจากสมการ Forward-Active"`; ถ้า `region == REGION_SATURATION` → `"ทรานซิสเตอร์อยู่ในสภาวะ Saturation: สมการ Forward-Active ใช้ไม่ได้ ผลอาจคลาดเคลื่อน"`; ถ้า `beta < 1` → `"ค่า β ต่ำผิดปกติ"`

> หมายเหตุ: ต้องตรวจ `isfinite` **ก่อน** override ค่า Cutoff เพื่อจับ `nan` จากอินพุตสุดขั้ว

- [ ] **Step 4: รัน test ให้ผ่านทั้งหมด**

Run: `python -m unittest discover -s tests -v`
Expected: PASS 9 tests (1 เดิม + 8 ใหม่)

- [ ] **Step 5: Commit**

Summary: `Add validation, region detection and physical cutoff values`

---

### Task 3: Flask app + หน้าเว็บฟอร์ม + CSS

**Files:**
- Create: `app.py`
- Create: `templates/index.html`
- Create: `static/style.css`
- Create: `tests/test_web.py`

**Interfaces:**
- Consumes: `dc_bias.calculate()` (Task 1–2)
- Produces:
  - `app.app` — Flask instance
  - `app.DEFAULT_FORM: dict[str, str]` — ค่าเริ่มต้นเป็น string: `{"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2", "re": "1", "beta": "100", "vbe": "0.70", "r_unit": "kohm"}`
  - `app.format_voltage(v: float) -> str` → `f"{v:.3f} V"`
  - `app.format_current(a: float) -> str` → `>= 1e-3` ใช้ `f"{a * 1e3:.3f} mA"` ไม่งั้น `f"{a * 1e6:.2f} µA"`
  - Route `GET /` → `index()`
  - Template context: `form` (dict ของ string), `result` (dict หรือ `None`), `error` (str หรือ `None`)

- [ ] **Step 1: เขียน failing test ของหน้าแรก**

`tests/test_web.py`:
```python
import unittest

from app import app


class TestIndexPage(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_index_returns_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('name="vcc"', body)
        self.assertIn('name="beta"', body)
        self.assertIn('name="r_unit"', body)
```

- [ ] **Step 2: รัน test ให้เห็นว่า fail**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: สร้าง `app.py` (เฉพาะ GET)**

```python
from flask import Flask, render_template

from dc_bias import calculate  # noqa: F401  (ใช้ใน Task 4)

app = Flask(__name__)

DEFAULT_FORM = {
    "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
    "re": "1", "beta": "100", "vbe": "0.70", "r_unit": "kohm",
}


def format_voltage(v):
    return f"{v:.3f} V"


def format_current(a):
    if abs(a) >= 1e-3:
        return f"{a * 1e3:.3f} mA"
    return f"{a * 1e6:.2f} µA"


@app.get("/")
def index():
    return render_template("index.html", form=DEFAULT_FORM, result=None, error=None)
```

- [ ] **Step 4: สร้าง `templates/index.html`**

โครงที่ต้องมี (ภาษาไทย):
- `<form method="post" action="/calculate">`
- input `name="vcc"` (type number, step any), `r1`, `r2`, `rc`, `re`, `beta`, `vbe`
- `<select name="r_unit">` มี `<option value="ohm">Ω</option>` และ `<option value="kohm">kΩ</option>`
- ปุ่ม submit ข้อความ `คำนวณ DC Bias`
- ทุก input ใช้ `value="{{ form.<field> }}"` เพื่อ sticky values
- บล็อก error: `{% if error %}<div class="error">{{ error }}</div>{% endif %}`
- บล็อกผลลัพธ์: `{% if result %}` แสดง `result.vb|voltage` ฯลฯ — ใช้ filter ที่ลงทะเบียนใน `app.py` (`app.add_template_filter(format_voltage, "voltage")`, `app.add_template_filter(format_current, "current")`)
- แสดง `region` เป็นป้าย: `forward_active` → `✅ Forward Active`, `cutoff` → `⚠️ Cutoff`, `saturation` → `⚠️ Saturation`
- แสดง `result.warnings` เป็นรายการในกล่อง `.warning`
- `<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">`

> ต้องเพิ่ม filter registration ใน `app.py` ก่อน template ใช้งานได้

- [ ] **Step 5: สร้าง `static/style.css`**

ขั้นต่ำ: 2 คอลัมน์ด้วย CSS Grid (`grid-template-columns: 1fr 1fr`), ยุบเป็นคอลัมน์เดียวที่ `@media (max-width: 720px)`, กล่อง `.error` พื้นแดงอ่อน, `.warning` พื้นเหลืองอ่อน, ฟอนต์ `Tahoma, "Noto Sans Thai", sans-serif`

- [ ] **Step 6: รัน test ให้ผ่าน**

Run: `python -m unittest discover -s tests -v`
Expected: PASS 10 tests

- [ ] **Step 7: ตรวจด้วยตาเปล่า**

Run: `python -m flask --app app run --debug`
เปิด `http://127.0.0.1:5000/` → เห็นฟอร์มพร้อมค่าเริ่มต้น 12 / 100 / 22 / 2.2 / 1 / 100 / 0.70 และ dropdown kΩ
จากนั้นกด `Ctrl+C` เพื่อหยุด server

- [ ] **Step 8: Commit**

Summary: `Add Flask index route, form template and stylesheet`

---

### Task 4: POST /calculate — parsing, error display, sticky form

**Files:**
- Modify: `app.py`
- Modify: `templates/index.html`
- Modify: `tests/test_web.py`

**Interfaces:**
- Consumes: `dc_bias.calculate()`, `format_voltage`, `format_current` จาก Task 3
- Produces:
  - Route `POST /calculate` → `calculate_route()`
  - `app._parse_form(form) -> dict` — คืนค่า SI (`float`) พร้อมคูณ `r_unit`
  - error message แบบ string เดียว (ตัวแรกที่เจอ) ส่งใน context `error`

- [ ] **Step 1: เขียน failing tests**

เพิ่มใน `tests/test_web.py`:
```python
REFERENCE_FORM = {
    "vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
    "re": "1", "beta": "100", "vbe": "0.70", "r_unit": "kohm",
}


class TestCalculateRoute(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_calculate_shows_backend_results(self):
        response = self.client.post("/calculate", data=REFERENCE_FORM)
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("1.230", body)   # IC = 1.230 mA จาก Python
        self.assertIn("8.052", body)   # VCE
        self.assertIn("Forward Active", body)

    def test_invalid_resistor_shows_error(self):
        data = dict(REFERENCE_FORM, r1="0")
        response = self.client.post("/calculate", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("ต้องมากกว่า 0", response.get_data(as_text=True))

    def test_non_numeric_shows_error(self):
        data = dict(REFERENCE_FORM, vcc="abc")
        response = self.client.post("/calculate", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("กรุณากรอก VCC เป็นตัวเลข", response.get_data(as_text=True))

    def test_empty_field_shows_error(self):
        data = dict(REFERENCE_FORM, vbe="")
        response = self.client.post("/calculate", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("กรุณากรอก VBE", response.get_data(as_text=True))

    def test_cutoff_shows_zero_current(self):
        data = dict(REFERENCE_FORM, r2="5")
        response = self.client.post("/calculate", data=data)
        body = response.get_data(as_text=True)
        self.assertIn("Cutoff", body)
        self.assertIn("0.000 mA", body)
```

- [ ] **Step 2: รัน test ให้เห็นว่า fail**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL — POST `/calculate` คืน 404

- [ ] **Step 3: เพิ่ม parsing + route ใน `app.py`**

```python
FIELD_LABELS = {
    "vcc": "VCC", "r1": "R1", "r2": "R2", "rc": "RC",
    "re": "RE", "beta": "β", "vbe": "VBE",
}
RESISTOR_FIELDS = ("r1", "r2", "rc", "re")


def _parse_form(form):
    unit_multiplier = 1000.0 if form.get("r_unit", "ohm") == "kohm" else 1.0
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
```

- [ ] **Step 4: ปรับ template ให้แสดงผล**

เพิ่มหลังบล็อก error: เมื่อมี `result` แสดงตาราง VB/VE/VC/VCE ด้วย `|voltage` และ IB/IC/IE ด้วย `|current`, ป้าย region และรายการ `result.warnings` ในกล่อง `.warning`

- [ ] **Step 5: รัน test ให้ผ่านทั้งหมด**

Run: `python -m unittest discover -s tests -v`
Expected: PASS 15 tests

- [ ] **Step 6: ตรวจด้วยตาเปล่า 3 กรณี**

Run: `python -m flask --app app run --debug` แล้ว
1. ค่าอ้างอิง → เห็น `VB 1.942 V`, `IC 1.230 mA`, `VCE 8.052 V`, ป้าย Forward Active
2. `R1 = 0` → กล่องแดง "ต้องมากกว่า 0"
3. `R2 = 5` → ป้าย Cutoff, `IC 0.000 mA`, กล่องเหลืองอธิบายสภาวะ Cutoff

- [ ] **Step 7: Commit**

Summary: `Wire POST /calculate with parsing, errors and region display`

---

### Task 5: เอกสารประกอบ (README / AGENTS / docs)

**Files:**
- Create: `README.md`
- Create: `AGENTS.md`
- Create: `docs/design-note.md`
- Create: `docs/validation.md`
- Create: `docs/reflection.md`

**Interfaces:**
- Consumes: ทุกไฟล์จาก Task 1–4
- Produces: เอกสารที่ทำให้ clone → install → run → test ได้ (เกณฑ์ A7)

- [ ] **Step 1: เขียน `README.md`**

ต้องมีครบ:
- ชื่อโปรเจกต์ + คำอธิบายสั้น
- ภาพรวมสมการ (คัดลอกจาก spec 6.2)
- ค่าตัวอย่าง + ผลอ้างอิง (ตารางใน spec 6.2)
- วิธีติดตั้ง (Windows PowerShell):
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  python -m pip install -r requirements.txt
  python -m flask --app app run --debug
  ```
- วิธีรัน tests: `python -m unittest discover -s tests -v`
- ข้อจำกัดของแบบจำลอง: Forward-Active approximation, β/VBE คงที่, ไม่ใช่ SPICE, ไม่รองรับ AC
- ขอบเขต Week 2 (สิ่งที่ยังไม่ทำ)

- [ ] **Step 2: เขียน `AGENTS.md`**

กติกาสำหรับ AI ที่จะมาแก้โค้ดต่อ: ห้ามใส่สมการใน template/app.py, `dc_bias.py` ต้องเป็น pure function, ทุก feature ใหม่ต้องมี test, รัน `python -m unittest discover -s tests -v` ก่อน commit

- [ ] **Step 3: เขียน `docs/design-note.md`**

สรุปสถาปัตยกรรม 3 ชั้น + เหตุผลที่แยก + data flow (Browser → Flask → `dc_bias` → template) อ้างอิง design doc

- [ ] **Step 4: เขียน `docs/validation.md`**

ตารางเทียบค่าที่ได้จากเว็บกับค่าคำนวณอิสระ (ค่าอ้างอิง spec 6.2) + ตารางกรณีทดสอบ (A1–A7) + ผลรัน test จริง (คัดลอก output)

- [ ] **Step 5: เขียน `docs/reflection.md`**

ตอบคำถามรายบุคคลในใบงาน 4 ข้อ:
1. ทำไมเปิด `templates/index.html` ตรง ๆ ไม่เท่ากับรัน Flask
2. ฟอร์มส่งข้อมูลไป Python อย่างไร
3. แก้สมการใน `dc_bias.py` ต้องแก้ HTML ไหม
4. ทำไมผลนอก Region ต้องมี Warning

- [ ] **Step 6: ตรวจว่า README ทำตามได้จริง**

Run: `python -m unittest discover -s tests -v`
Expected: PASS 15 tests — ยืนยันว่าคำสั่งใน README ใช้ได้

- [ ] **Step 7: Commit**

Summary: `Add README, AGENTS guide and lab documentation`

---

### Task 6: ตรวจรับรอบสุดท้าย (Acceptance A1–A7)

**Files:**
- Modify: `docs/validation.md` (บันทึกผลจริง)

**Interfaces:**
- Consumes: ทั้งโปรเจกต์
- Produces: หลักฐานครบสำหรับส่ง Moodle

- [ ] **Step 1: รัน test suite เต็ม**

Run: `python -m unittest discover -s tests -v`
Expected: PASS 15 tests, 0 failures, 0 errors — คัดลอก output ลง `docs/validation.md`

- [ ] **Step 2: ตรวจ A1–A5 ด้วยเบราว์เซอร์**

Run: `python -m flask --app app run --debug`

| เกณฑ์ | สิ่งที่ต้องเห็น |
|---|---|
| A1 | `GET /` → 200, ฟอร์มครบ 7 ช่อง |
| A2 | กรอกค่าอ้างอิง → เห็นผลที่คำนวณจาก Python |
| A3 | VB 1.942 V, VE 1.242 V, VC 9.294 V, VCE 8.052 V, IC 1.230 mA |
| A4 | `R1=0` → error ไทย, หน้าไม่ล้ม |
| A5 | `R2=5` → ป้าย Cutoff + warning |

- [ ] **Step 3: ตรวจ A6–A7**

- A6: นับ test — `tests/test_dc_bias.py` ≥ 3 เคส, `tests/test_web.py` ≥ 1 เคส ✅
- A7: ตรวจว่า `requirements.txt` + README ครบ, `.venv/` และ `__pycache__/` ไม่ถูก track

Run: `git status --short`
Expected: ไม่มี `.venv/` หรือ `__pycache__/` ในรายการ

- [ ] **Step 4: Commit + Push ผ่าน GitHub Desktop**

1. เปิด GitHub Desktop → repo `BJT DC Bias Web App`
2. ตรวจ Changes ว่าไม่มี `.venv/`
3. Summary: `Add final validation evidence for Lab 02`
4. กด **Commit to main** → **Publish repository** (ครั้งแรก) หรือ **Push origin**
5. ไปแท็บ **History** → คลิกขวา commit ล่าสุด → **Copy SHA…**
6. ส่ง Repository URL + SHA ทาง Moodle
