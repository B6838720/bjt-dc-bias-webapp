# Validation Evidence — BJT DC Bias Web App

> บันทึกหลักฐานการตรวจรับตามเกณฑ์ใบงาน Lab 02 (A1–A7)
> วันที่ตรวจ: 2026-11-10

---

## 1. สภาพแวดล้อมที่ใช้ตรวจ

| รายการ | ค่า |
|---|---|
| OS | Windows (win32) |
| Python | 3.15.2 |
| Flask | 3.1.3 |
| Jinja2 | 3.1.6 |
| Werkzeug | 3.1.9 |
| รันแอป | `python -m flask --app app run` |
| URL | `http://127.0.0.1:5000/` |
| รัน test | `python -m unittest discover -s tests -v` |

---

## 2. ค่าอ้างอิง: เว็บ vs การคำนวณอิสระ

**อินพุต:** `VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ, β=100, VBE=0.70 V`

ค่าอิสระคำนวณด้วยสมการในสเปรดชีต/สคริปต์แยก (ไม่ import `dc_bias`)
เพื่อพิสูจน์ว่าเว็บไม่ได้ hardcode ค่า

| ปริมาณ | ค่าคำนวณอิสระ | ค่าที่เว็บแสดง | ต่างกัน |
|---|---|---|---|
| VTH | 2.1639 V | 2.164 V | < 0.001 V |
| RTH | 18,032.79 Ω | 18,033 Ω | < 1 Ω |
| IB | 12.299 µA | 12.30 µA | < 0.01 µA |
| IC | 1.2299 mA | 1.230 mA | < 0.001 mA |
| IE | 1.2422 mA | 1.242 mA | < 0.001 mA |
| VB | 1.9422 V | 1.942 V | < 0.001 V |
| VE | 1.2422 V | 1.242 V | < 0.001 V |
| VC | 9.2943 V | 9.294 V | < 0.001 V |
| VCE | 8.0522 V | 8.052 V | < 0.001 V |
| Region | Forward Active | Forward Active | ตรงกัน |

**สรุป:** ค่าที่แสดงบนหน้าเว็บตรงกับค่าคำนวณอิสระภายใน rounding 3 ตำแหน่ง
และ `tests/test_web.py` ตรวจว่า HTML มี `1.230` และ `8.052` ซึ่งเป็นค่าที่
`dc_bias.calculate()` คำนวณจริง (ไม่ใช่ค่าคงที่ใน template)

---

## 3. กรณีทดสอบที่ตรวจด้วย HTTP จริง

รัน Flask server แล้วยิง `Invoke-WebRequest` (PowerShell) เข้า `127.0.0.1:5000`

| # | กรณี | อินพุต | ผลที่ต้องได้ | ผลจริง |
|---|---|---|---|---|
| 1 | ค่าอ้างอิง | ค่ามาตรฐาน | 200, VB 1.942 V, IC 1.230 mA, VCE 8.052 V, Forward Active | ✅ ตรงทั้งหมด |
| 2 | ตัวต้านทานเป็นศูนย์ | `R1 = 0` | 200, กล่องแดง "ต้องมากกว่า 0" | ✅ ตรง |
| 3 | Cutoff | `R2 = 5` | 200, ป้าย Cutoff, `IC 0.000 mA`, warning | ✅ ตรง |

---

## 4. ผลรัน Test Suite

```
test_reference_operating_point (test_dc_bias.TestReferenceOperatingPoint.test_reference_operating_point) ... ok
test_cutoff_reports_physical_values (test_dc_bias.TestRegions.test_cutoff_reports_physical_values) ... ok
test_fractional_beta_accepted (test_dc_bias.TestRegions.test_fractional_beta_accepted) ... ok
test_saturation_detected (test_dc_bias.TestRegions.test_saturation_detected) ... ok
test_overflowing_inputs_rejected (test_dc_bias.TestValidation.test_overflowing_inputs_rejected) ... ok
test_vbe_not_below_vcc_rejected (test_dc_bias.TestValidation.test_vbe_not_below_vcc_rejected) ... ok
test_zero_beta_rejected (test_dc_bias.TestValidation.test_zero_beta_rejected) ... ok
test_zero_divider_rejected (test_dc_bias.TestValidation.test_zero_divider_rejected) ... ok
test_zero_resistor_rejected (test_dc_bias.TestValidation.test_zero_resistor_rejected) ... ok
test_calculate_shows_backend_results (test_web.TestCalculateRoute.test_calculate_shows_backend_results) ... ok
test_cutoff_shows_zero_current (test_web.TestCalculateRoute.test_cutoff_shows_zero_current) ... ok
test_empty_field_shows_error (test_web.TestCalculateRoute.test_empty_field_shows_error) ... ok
test_invalid_resistor_shows_error (test_web.TestCalculateRoute.test_invalid_resistor_shows_error) ... ok
test_non_numeric_shows_error (test_web.TestCalculateRoute.test_non_numeric_shows_error) ... ok
test_index_returns_form (test_web.TestIndexPage.test_index_returns_form) ... ok

----------------------------------------------------------------------
Ran 15 tests in 0.091s

OK
```

---

## 5. Acceptance Mapping (A1–A7)

| เกณฑ์ | สิ่งที่ต้องพิสูจน์ | หลักฐาน | สถานะ |
|---|---|---|---|
| **A1** `GET /` | หน้าเว็บเปิดได้ 200 และมีฟอร์มครบ 7 ช่อง | `test_index_returns_form` + HTTP GET → 200, พบ `name="vcc"`, `name="r_unit"` | ✅ |
| **A2** `POST /calculate` | ฟอร์มส่งค่าไป Python และได้ผลกลับมา | `test_calculate_shows_backend_results` + HTTP POST → 200 พร้อมค่าคำนวณ | ✅ |
| **A3** Engineering Reference | ค่าตรงกับ independent calculation | ตารางข้อ 2 + `test_reference_operating_point` | ✅ |
| **A4** Validation | อินพุตผิดได้ข้อความไทย ไม่ 500 | `test_non_numeric_shows_error`, `test_empty_field_shows_error`, `test_invalid_resistor_shows_error` + HTTP case 2 | ✅ |
| **A5** Outside Active Region | มี warning/ป้าย region | `test_cutoff_reports_physical_values`, `test_cutoff_shows_zero_current`, `test_saturation_detected` + HTTP case 3 | ✅ |
| **A6** Unit + HTTP Tests | มีทั้ง unit และ HTTP test | `tests/test_dc_bias.py` 9 เคส, `tests/test_web.py` 6 เคส | ✅ |
| **A7** Reproducibility | clone → install → run → test ได้ | `README.md`, `requirements.txt`, `.gitignore`; `.venv/` และ `__pycache__/` ไม่ถูก track | ✅ |

---

## 6. Final Acceptance Run (Task 6)

รัน server จริงที่ `http://127.0.0.1:5000/` แล้วตรวจทุกเกณฑ์ด้วย HTTP
(ผลจากรอบตรวจรับสุดท้าย 2026-11-10):

| เกณฑ์ | สิ่งที่ตรวจ | ผล |
|---|---|---|
| A1 | `GET /` → 200, ฟอร์มครบ 7 ช่อง (`vcc, r1, r2, rc, re, beta, vbe`) | ✅ 200, ครบทุกช่อง |
| A1 | `GET /static/style.css` → 200 | ✅ 200 |
| A2 | `POST /calculate` ค่าอ้างอิง → 200 | ✅ 200 |
| A3 | VB `1.942 V`, VE `1.242 V`, VC `9.294 V`, VCE `8.052 V`, IC `1.230 mA` | ✅ ตรงทุกค่า |
| A3 | ป้าย `Forward Active` | ✅ พบ |
| A4 | `R1 = 0` → 200 + "ต้องมากกว่า 0" | ✅ 200, ข้อความถูก |
| A4 | `R1 = R2 = 1e308` → 200 + "ไม่สมเหตุสมผล" (ไม่ 500) | ✅ 200, ข้อความถูก |
| A5 | `R2 = 5` → Cutoff + `0.000 mA` + warning | ✅ ครบ |
| A5 | `RC = 100` → Saturation + warning | ✅ ครบ |
| A6 | `test_dc_bias.py` 9 เคส + `test_web.py` 6 เคส | ✅ 15 เคส |
| A7 | `git ls-files` ไม่มี `.venv/`, `__pycache__`, `.pyc`, `.superpowers/` | ✅ ไม่มี |
| A7 | `git status --short` สะอาด | ✅ ว่าง |

**ผลรัน test รอบสุดท้าย:**

```
Ran 15 tests in 0.050s

OK
```

---

## 7. หมายเหตุ

- `format_current()` แสดง `0.000 mA` สำหรับกระแสศูนย์ เพื่อให้หน่วยสเกลเดียวกับ IC
- ในสภาวะ Cutoff ตัวเลขที่แสดงเป็น **ค่าจริงทางกายภาพ** (`IC=IE=0`, `VE=0`,
  `VC=VCC`, `VCE=VCC`, `VB=VTH`) ไม่ใช่ผลติดลบจากสมการ Forward-Active
- Saturation ยังแสดงค่าจากสมการพร้อม warning ตาม design
