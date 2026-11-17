# Lab 03 Three Bias Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** เพิ่ม Fixed Bias และ Emitter Bias ให้เว็บ Flask เดิม โดยคงผล Voltage Divider เดิมทุกประการ

**Architecture:** เก็บสมการเป็น pure function ใน `dc_bias.py` (`calculate()` เดิม + `calculate_fixed()` + `calculate_emitter()`) ใช้ helper ร่วมกันตอนสรุปผล; `app.py` แปลงหน่วย/ตรวจอินพุตรายโหมดแล้ว dispatch ด้วย `if/elif`; Jinja render เฉพาะช่องของโหมดที่เลือกโดยไม่ใช้ JavaScript

**Tech Stack:** Python 3.15.2, Flask 3.1.3, unittest, Jinja2 (ไม่เพิ่ม dependency)

**Spec:** `docs/superpowers/specs/2026-11-17-lab03-three-bias-modes-design.md`

## Global Constraints

- ห้าม import `flask` ใน `dc_bias.py`, ห้ามมีสมการฟิสิกส์ใน `app.py`, ห้ามคำนวณใน `templates/index.html`
- หน่วยภายในคือ Ω / V / A; แปลง kΩ → Ω **ครั้งเดียว** ตอนรับฟอร์ม
- dict ที่ส่งกลับต้องมีคีย์ครบ: `vb, ve, vc, vce, ic, ib, ie, region, model_applies, warnings`
- ข้อความ UI/error/warning เป็นภาษาไทย; แรงดัน 3 ตำแหน่ง (`1.942 V`), กระแส mA 3 ตำแหน่ง (`1.230 mA`)
- test เดิม 16 ตัวต้องผ่านอยู่หลังทุก task; ใช้ `unittest` เท่านั้น
- ไม่เพิ่ม JavaScript, ไม่เพิ่ม dependency, ไม่ทำ SPICE/AC/Transient/unittest ตามใบงาน (แต่ TDD ตาม `AGENTS.md` )
- ก่อน commit ต้อง `git status --short` สะอาดจาก `.venv/`, `.env`, credentials

## Review Focus

1. **โหมดไม่รู้จัก** (`mode=bogus`) → ต้อง error ภาษาไทย, ห้าม fallback เป็น Divider → ทดสอบใน Task 2
2. **ค่าที่ต้องเป็นบวก ≤ 0 ในโหมดใหม่** (`RB=0`, `RE=0`) → error ไทย, HTTP 200 ไม่ 500 → Task 1 + 2
3. **ค่าที่ไม่ใช่ตัวเลข / ไม่จำกัด (`nan`, `inf`)** ในช่องของโหมด → error, ไม่ล่ม → Task 1 + 2
4. **ผลรอบก่อนค้างเมื่อมี error (A5)** → ต้อง render `result=None` เสมอ → Task 2 + 3
5. **R<sub>E</sub> ใน A3→A4 ต้องเดินทางถึงสมการจริง** → ต้อง render ช่อง `re` เฉพาะโหมด emitter และ POST ส่งค่าเข้า `calculate_emitter()` → Task 3 + 4

---

### Task 1: ฟังก์ชันคำนวณ Fixed / Emitter ใน `dc_bias.py`

**Files:**
- Modify: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: `_validate()`, `_detect_region()`, `REGION_*`, `WARNING_*` ที่มีอยู่แล้ว
- Produces: `calculate_fixed(vcc, rb, rc, beta, vbe) -> dict`, `calculate_emitter(vcc, rb, rc, re, beta, vbe) -> dict` คืนคีย์ชุดเดียวกับ `calculate()`

- [ ] **Step 1: เพิ่ม failing tests** ใน `tests/test_dc_bias.py` (ใช้ `unittest`, imports เพิ่ม `calculate_fixed`, `calculate_emitter`)

```python
class TestFixedAndEmitter(unittest.TestCase):
    def test_fixed_reference(self):
        r = calculate_fixed(vcc=12.0, rb=1e6, rc=2200.0, beta=100.0, vbe=0.70)
        self.assertAlmostEqual(r["ib"] * 1e6, 11.30, places=2)
        self.assertAlmostEqual(r["ic"] * 1e3, 1.1300, places=3)
        self.assertAlmostEqual(r["ve"], 0.0, places=6)
        self.assertAlmostEqual(r["vb"], 0.70, places=6)
        self.assertAlmostEqual(r["vc"], 9.5140, places=3)
        self.assertAlmostEqual(r["vce"], 9.5140, places=3)
        self.assertEqual(r["region"], REGION_ACTIVE)
        self.assertEqual(r["warnings"], [])

    def test_emitter_reference(self):
        r = calculate_emitter(vcc=12.0, rb=1e6, rc=2200.0, re=1000.0,
                              beta=100.0, vbe=0.70)
        self.assertAlmostEqual(r["ic"] * 1e3, 1.0263, places=3)
        self.assertAlmostEqual(r["ve"], 1.0366, places=3)
        self.assertAlmostEqual(r["vb"], 1.7366, places=3)
        self.assertAlmostEqual(r["vce"], 8.7054, places=3)

    def test_larger_re_reduces_ic(self):
        a = calculate_emitter(vcc=12.0, rb=1e6, rc=2200.0, re=1000.0,
                              beta=100.0, vbe=0.70)
        b = calculate_emitter(vcc=12.0, rb=1e6, rc=2200.0, re=2000.0,
                              beta=100.0, vbe=0.70)
        self.assertAlmostEqual(b["ic"] * 1e3, 0.9401, places=3)
        self.assertLess(b["ic"], a["ic"])

    def test_nonpositive_rb_rejected(self):
        with self.assertRaises(ValueError):
            calculate_fixed(vcc=12.0, rb=0.0, rc=2200.0, beta=100.0, vbe=0.70)

    def test_nonpositive_re_rejected(self):
        with self.assertRaises(ValueError):
            calculate_emitter(vcc=12.0, rb=1e6, rc=2200.0, re=0.0,
                              beta=100.0, vbe=0.70)
```

- [ ] **Step 2: รันให้เห็น fail จริง**

Run: `.venv\Scripts\python.exe -m unittest tests.test_dc_bias -v`
Expected: FAIL — `ImportError: cannot import name 'calculate_fixed'`

- [ ] **Step 3: implement ใน `dc_bias.py`**

คง `calculate()` เดิมไม่เปลี่ยนพฤติกรรม แล้ว:
  - แยก `_summarize(ib, re, vcc, rc, beta, vbe, vth=None, rth=None)` เป็น helper ภายในที่คำนวณ `ic, ie, ve, vb, vc, vce`, ตรวจ `math.isfinite`, เรียก `_detect_region()`, จัดการ cutoff ตามเดิม, สร้าง `warnings` (เพิ่ม `ib <= 0`) และคืน dict คีย์ชุดเดิม
  - ให้ `calculate()` เรียก helper นี้ด้วย `vth/rth` ของ Divider (ผลต้องเท่าเดิม)
  - `calculate_fixed()`: ตรวจ `vcc>0, rb>0, rc>0, beta>0, 0<vbe<vcc` ด้วย `_validate`-style แล้ว `ib=(vcc-vbe)/rb`, เรียก helper ด้วย `re=0`
  - `calculate_emitter()`: ตรวจเพิ่ม `re>0` แล้ว `ib=(vcc-vbe)/(rb+(beta+1)*re)`, เรียก helper

- [ ] **Step 4: รัน tests ให้ผ่าน**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: PASS — 21 tests (16 เดิม + 5 ใหม่), `OK`

- [ ] **Step 5: Commit**

```powershell
git add dc_bias.py tests/test_dc_bias.py
git commit -m "feat: add fixed and emitter bias calculators"
```

---

### Task 2: รับโหมด / แปลงหน่วย / dispatch ใน `app.py`

**Files:**
- Modify: `app.py`
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: `calculate()`, `calculate_fixed()`, `calculate_emitter()` จาก Task 1
- Produces: `_parse_form(form, mode) -> dict[str, float]`, `MODE_FIELDS` map, `calculate_route()` ที่ส่ง `mode` เข้า template ทุกครั้ง

- [ ] **Step 1: เพิ่ม failing tests** ใน `tests/test_web.py`

```python
def test_divider_mode_keeps_old_result(self):
    response = self.client.post("/calculate", data=dict(REFERENCE_FORM, mode="divider"))
    body = response.get_data(as_text=True)
    self.assertEqual(response.status_code, 200)
    self.assertIn("1.230", body)
    self.assertIn("8.052", body)

def test_fixed_mode_uses_fixed_formula(self):
    data = {"mode": "fixed", "vcc": "12", "rb": "1000", "rc": "2.2",
            "beta": "100", "vbe": "0.70", "r_unit": "kohm"}
    body = self.client.post("/calculate", data=data).get_data(as_text=True)
    self.assertIn("1.130", body)
    self.assertIn("9.514", body)

def test_emitter_mode_uses_re(self):
    data = {"mode": "emitter", "vcc": "12", "rb": "1000", "rc": "2.2",
            "re": "1", "beta": "100", "vbe": "0.70", "r_unit": "kohm"}
    body = self.client.post("/calculate", data=data).get_data(as_text=True)
    self.assertIn("1.026", body)
    self.assertIn("8.705", body)

def test_unknown_mode_is_error(self):
    data = dict(REFERENCE_FORM, mode="bogus")
    body = self.client.post("/calculate", data=data).get_data(as_text=True)
    self.assertIn("โหมดไม่รู้จัก", body)
    self.assertNotIn("1.230", body)

def test_zero_rb_error_has_no_stale_result(self):
    data = {"mode": "fixed", "vcc": "12", "rb": "0", "rc": "2.2",
            "beta": "100", "vbe": "0.70", "r_unit": "kohm"}
    body = self.client.post("/calculate", data=data).get_data(as_text=True)
    self.assertIn("RB ต้องมากกว่า 0", body)
    self.assertNotIn("9.514", body)
```

- [ ] **Step 2: รันให้เห็น fail จริง**

Run: `.venv\Scripts\python.exe -m unittest tests.test_web -v`
Expected: FAIL — fixed/emitter ไม่คำนวณ, ไม่มีข้อความ "โหมดไม่รู้จัก"

- [ ] **Step 3: implement ใน `app.py`**

  - `MODE_FIELDS = {"divider": ("vcc","r1","r2","rc","re","beta","vbe"), "fixed": ("vcc","rb","rc","beta","vbe"), "emitter": ("vcc","rb","rc","re","beta","vbe")}`
  - `MODE_LABELS` เพิ่ม `"rb": "RB"`; คง `FIELD_LABELS` เดิมสำหรับ Divider
  - `_parse_form(form, mode)`: อ่านเฉพาะฟิลด์ใน `MODE_FIELDS[mode]` (ถ้า `mode` ไม่รู้จัก → raise `ValueError("โหมดไม่รู้จัก")`), ตรวจว่าง/ตัวเลขเหมือนเดิม, คูณ 1000 เฉพาะฟิลด์ resistance, ใช้ `math.isfinite` กัน `inf/nan`
  - `index()` อ่าน `mode = request.args.get("mode", "divider")` แล้วส่ง `form` ที่มี `mode` ด้วย
  - `calculate_route()` อ่าน `mode` จาก `request.form` → `_parse_form()` → dispatch ด้วย `if/elif` → ถ้าไม่ตรงโหมดใด raise `ValueError("โหมดไม่รู้จัก")`; ส่ง `mode=mode, result=None` ตอน error เสมอ
  - ข้อความ error ต้องระบุชื่อโหมดด้วย เช่น `"Fixed — RB ต้องมากกว่า 0"`

- [ ] **Step 4: รัน tests ให้ผ่าน**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: PASS — 26 tests, `OK`

- [ ] **Step 5: Commit**

```powershell
git add app.py tests/test_web.py
git commit -m "feat: dispatch bias mode from form"
```

---

### Task 3: ฟอร์มเลือกโหมดและแสดงผลใน `templates/index.html`

**Files:**
- Modify: `templates/index.html`
- Modify: `static/style.css` (เฉพาะถ้าจำเป็น)
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: `mode`, `form`, `result`, `error` จาก `app.py` (Task 2)
- Produces: ฟอร์มที่มี `name="mode"` (hidden ในฟอร์มคำนวณ), ปุ่ม “เปลี่ยนโหมด”, ช่องตามโหมด

- [ ] **Step 1: เพิ่ม failing tests** ใน `tests/test_web.py`

```python
def test_index_has_mode_selector(self):
    body = self.client.get("/").get_data(as_text=True)
    self.assertIn('name="mode"', body)
    self.assertIn("เปลี่ยนโหมด", body)

def test_get_fixed_mode_hides_divider_fields(self):
    body = self.client.get("/?mode=fixed").get_data(as_text=True)
    self.assertIn('name="rb"', body)
    self.assertNotIn('name="r1"', body)
    self.assertNotIn('name="re"', body)

def test_get_emitter_mode_shows_re(self):
    body = self.client.get("/?mode=emitter").get_data(as_text=True)
    self.assertIn('name="rb"', body)
    self.assertIn('name="re"', body)
```

- [ ] **Step 2: รันให้เห็น fail จริง**

Run: `.venv\Scripts\python.exe -m unittest tests.test_web -v`
Expected: FAIL — ไม่มี `"เปลี่ยนโหมด"`, ไม่มีช่อง `rb`

- [ ] **Step 3: implement template**

  - ฟอร์มแยก “เลือกวงจร”: `<select name="mode">` มี 3 option (`divider`, `fixed`, `emitter`) + ปุ่ม submit `เปลี่ยนโหมด` แบบ `method="get" action="/"` และ `selected` ตาม `mode`
  - ฟอร์มคำนวณ: `<input type="hidden" name="mode" value="{{ mode }}">` + `#r_unit` dropdown เหมือนเดิม + render fields ตาม `mode` ด้วย `{% if %}` (`divider` = เดิม 7 ช่อง, `fixed` = `rb, rc, beta, vbe`, `emitter` = `rb, rc, re, beta, vbe`)
  - ป้ายหัวข้อ/ผล/error ต้องมีชื่อโหมด เช่น `Fixed Bias` / `Emitter Bias` / `Voltage Divider Bias`
  - render `result` เฉพาะเมื่อ `result` และไม่มี `error`; ถ้า `error` ให้แสดง error และข้อความเริ่มต้นแทนผล
  - `VTH/RTH` แสดงเฉพาะโหมด divider (เพราะโหมดอื่นไม่มีคีย์นี้)

- [ ] **Step 4: รัน tests ให้ผ่าน**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: PASS — 29 tests, `OK`

- [ ] **Step 5: Commit**

```powershell
git add templates/index.html static/style.css tests/test_web.py
git commit -m "feat: mode-aware bias form"
```

---

### Task 4: ตรวจ A1–A5 ผ่าน Browser + อัปเดต docs

**Files:**
- Modify: `docs/validation.md`
- Read-only: `docs/lab03-baseline.md`
- ไม่แก้โค้ดโปรแกรมใน task นี้ (ถ้าพบ fail ให้กลับไป task ที่ตรงแล้ว commit เพิ่ม)

**Interfaces:**
- Consumes: แอปที่รันที่ `http://127.0.0.1:5000/`, ตารางค่าคาดหมายใน spec ข้อ 5

- [ ] **Step 1: รัน server และ test สุดท้าย**

Run: `.venv\Scripts\python.exe -m flask --app app run --debug` (ค้างไว้) และ
`.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: `OK` 29 tests

- [ ] **Step 2: ตรวจ A1–A5 ผ่าน Browser จริง**

เปิด `http://127.0.0.1:5000/` ใช้ snapshot/goto/click ตามลำดับ:
  - A1: เลือก `divider` → กรอกค่าตาม baseline → กดคำนวณ → บันทึก IC 1.230 mA, VCE 8.052 V
  - A2: เปลี่ยนโหมดเป็น `fixed` (กด “เปลี่ยนโหมด” แล้วอ่าน snapshot ใหม่) → กรอก `RB=1000 kΩ` → IC 1.130 mA, VCE 9.514 V
  - A3: เปลี่ยนเป็น `emitter` → `RB=1000, RE=1 kΩ` → IC 1.026 mA, VCE 8.705 V
  - A4: **คงโหมด emitter** เปลี่ยนแค่ `RE=2 kΩ` → IC 0.940 mA, VCE 8.033 V (ต้องลดจาก A3)
  - A5: เปลี่ยนเป็น `fixed` → `RB=0` → ต้องเห็นข้อความ error และไม่มีผลคำนวณ
Expected: ทุกกรณี `PASS`; เก็บ snapshot/ข้อความจากหน้าเว็บอย่างน้อย 1 กรณีเป็นหลักฐาน

- [ ] **Step 3: อัปเดต `docs/validation.md`**

เพิ่มหัวข้อ Lab 03 พร้อมตาราง `ID | วิธีตรวจ | อินพุต | ค่าคาดหมาย | ผลจริงพร้อมหน่วย | สถานะ | หลักฐาน` และระบุวิธีที่ใช้จริง (OpenCode Browser / Playwright MCP / Manual) รวมหมายเหตุผลต่าง ≤ 0.01 mA / 0.02 V

- [ ] **Step 4: ตรวจก่อน commit**

Run: `git diff` และ `git diff --staged`, แล้ว `git status --short`
Expected: ไม่มี `.venv/`, `.env`, credentials; เฉพาะไฟล์ที่ตั้งใจ

- [ ] **Step 5: Commit**

```powershell
git add docs/validation.md
git commit -m "docs: record lab03 browser acceptance A1-A5"
```

---

## Self-Review (ผู้เขียนแผนตรวจแล้ว)

- ครบทุกข้อของ spec: สมการ 3 แบบ, unit, dict keys, mode dispatch, invalid input, A1–A5, docs ✅
- ไม่มี step ที่ตัดสินใจเองได้ (ทุก signature/channel/ค่าอ้างอิงระบุไว้) ✅
- ชื่อฟังก์ชัน `_parse_form(mode)`, `calculate_fixed()`, `calculate_emitter()` ตรงกันทุก task ✅
- Review Focus 5 ข้อมี test ตรงใน Task 1–4 ✅
- ความยาวแผนสมดุลกับ spec (ไม่ได้เขียน body โค้ดทั้งไฟล์) ✅
