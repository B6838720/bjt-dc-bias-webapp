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
test_ic_increases_with_beta (test_dc_bias.TestReferenceOperatingPoint.test_ic_increases_with_beta) ... ok
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
Ran 16 tests in 0.085s

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
| **A6** Unit + HTTP Tests | มีทั้ง unit และ HTTP test | `tests/test_dc_bias.py` 10 เคส, `tests/test_web.py` 6 เคส | ✅ |
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
| A6 | `test_dc_bias.py` 10 เคส + `test_web.py` 6 เคส | ✅ 16 เคส |
| A7 | `git ls-files` ไม่มี `.venv/`, `__pycache__`, `.pyc`, `.superpowers/` | ✅ ไม่มี |
| A7 | `git status --short` สะอาด | ✅ ว่าง |

**ผลรัน test รอบสุดท้าย:**

```
Ran 16 tests in 0.050s

OK
```

---

## 7. หมายเหตุ

- `format_current()` แสดง `0.000 mA` สำหรับกระแสศูนย์ เพื่อให้หน่วยสเกลเดียวกับ IC
- ในสภาวะ Cutoff ตัวเลขที่แสดงเป็น **ค่าจริงทางกายภาพ** (`IC=IE=0`, `VE=0`,
  `VC=VCC`, `VCE=VCC`, `VB=VTH`) ไม่ใช่ผลติดลบจากสมการ Forward-Active
- Saturation ยังแสดงค่าจากสมการพร้อม warning ตาม design

---

## 8. เปรียบเทียบกับ Approximate Analysis (กรณีผลไม่ตรงกับแอปอื่น)

ตรวจเมื่อ 2026-11-10: มีแอปอื่นให้ผลต่างจากโปรเจกต์นี้เมื่อกรอกค่าเดียวกัน
สาเหตุคือแอปนั้นใช้วิธี **approximate** (ละ `RTH`, ปัด `VTH` เป็น 2.2 V,
ใช้ `IC ≈ IE`)

| ปริมาณ | Approximate (แอปอื่น) | Exact (โปรเจกต์นี้ / ใบงาน) |
|---|---|---|
| VTH | 2.20 V | 2.164 V |
| IB | 15.0 µA | 12.30 µA |
| IC | 1.50 mA | 1.230 mA |
| IE | 1.52 mA | 1.242 mA |
| VE | 1.50 V | 1.242 V |
| VC | 8.70 V | 9.294 V |
| VCE | 7.20 V | 8.052 V |

**เงื่อนไขการใช้ approximate:** `β·RE ≥ 10·R2`

- `β·RE = 100 × 1 kΩ = 100 kΩ`
- `10·R2 = 10 × 22 kΩ = 220 kΩ`
- `100 kΩ < 220 kΩ` → **เงื่อนไขไม่ผ่าน**

**ข้อสรุป:** สมการ exact ที่คิด `RTH` คือสมการอ้างอิงในใบงาน
(`IB = (VTH−VBE)/(RTH+(β+1)RE)`) โปรเจกต์นี้จึงคงผล `IC = 1.230 mA`
และไม่ปรับให้ตรงกับ approximate

---

## 9. Lab 03 — Acceptance A1–A5 (2026-11-17)

### 9.1 วิธีตรวจและเกณฑ์ตัดสิน

| รายการ | ค่า |
|---|---|
| เครื่องมือที่ใช้จริง | **OpenCode Browser** (`tabs.open`, `snapshot`, `fill_form`, `select`, `evaluate`, `screenshot`) ผ่าน `http://127.0.0.1:5000/` |
| Playwright MCP | `NOT RUN` — ไม่พบ MCP resource ชื่อ `playwright` และไม่มี `opencode.json` / `opencode.jsonc` ในโปรเจกต์; ใช้ OpenCode Browser แทนตามข้อ 3 ของใบงาน (ให้คะแนนการตรวจผลเท่ากัน) |
| ค่าใช้ร่วม A1–A5 | `VCC = 12 V`, `RC = 2.2 kΩ`, `β = 100`, `VBE = 0.70 V`, หน่วยตัวต้านทาน `kΩ` |
| Tolerance | `|ΔIC| ≤ 0.01 mA`, `|ΔVCE| ≤ 0.02 V` เมื่อเทียบกับค่าอ้างอิงที่ยังไม่ปัดเศษ |
| ค่าอ้างอิงอิสระ | A1 `1.2299 mA / 8.0522 V`; A2 `1.1300 mA / 9.5140 V`; A3 `1.0263 mA / 8.7054 V`; A4 `0.9401 mA / 8.0328 V` (คำนวณจากสมการใน design note ไม่ได้ import โค้ดที่กำลังทดสอบ) |

### 9.2 ตารางผล A1–A5

| ID | วิธีตรวจ | อินพุต | ค่าคาดหมาย | ผลจริงพร้อมหน่วย | สถานะ | หลักฐาน |
|---|---|---|---|---|---|---|
| **A1 · โหมดเดิม** | OpenCode Browser: กรอกฟอร์ม Divider → กด `คำนวณ DC Bias` → อ่าน snapshot | Divider · `R1=100 kΩ, R2=22 kΩ, RE=1 kΩ` | ตรง baseline Lab 2: `IC 1.230 mA`, `VCE 8.052 V` | `IC = 1.230 mA`, `VCE = 8.052 V`, `VB 1.942 V`, `VE 1.242 V`, `VC 9.294 V`, `IB 12.30 µA`, `IE 1.242 mA`, `VTH 2.164 V`, `RTH 18,033 Ω`, `Forward Active` (ΔIC 0.0001 mA, ΔVCE 0.0002 V) | **PASS** | snapshot หลัง POST: `[definition] "1.230 mA"` / `"8.052 V"`; `docs/lab03-baseline.md` |
| **A2 · Fixed** | OpenCode Browser: `select mode=fixed` → `เปลี่ยนโหมด` → กรอกฟอร์ม → snapshot | Fixed · `RB=1 MΩ` (กรอก `1000` kΩ), **ไม่มีช่อง RE** | คำนวณได้โดยไม่กรอก RE: `IC 1.1300 mA`, `VCE 9.5140 V` | `IC = 1.130 mA`, `VCE = 9.514 V`, `VB 0.700 V`, `VE 0.000 V`, `IB 11.30 µA`, `Forward Active` (ΔIC 0.0000 mA, ΔVCE 0.0000 V) | **PASS** | snapshot แสดงเฉพาะ `VCC, RB, RC, หน่วย, β, VBE` (ไม่มี `name="r1"` / `name="re"`) และผล `1.130 mA` / `9.514 V` |
| **A3 · Emitter** | OpenCode Browser: `select mode=emitter` → กรอกฟอร์ม → snapshot | Emitter · `RB=1 MΩ`, `RE=1 kΩ` | มีช่อง RE และใช้ค่า RE: `IC 1.0263 mA`, `VCE 8.7054 V` | `IC = 1.026 mA`, `VCE = 8.705 V`, `VB 1.737 V`, `VE 1.037 V`, `IB 10.26 µA`, `Forward Active` (ΔIC 0.0003 mA, ΔVCE 0.0004 V) | **PASS** | snapshot แสดง `RE (Emitter → GND)` และผล `1.026 mA` / `8.705 V` |
| **A4 · เปลี่ยนค่าเดียว** | OpenCode Browser: แก้ **เฉพาะ RE** จาก `1` เป็น `2` → กดคำนวณ → snapshot + `evaluate` อ่านค่าฟอร์ม | Emitter · เหมือน A3 แต่ `RE=2 kΩ` | **ทำนายก่อนรัน:** IC ต้อง *ลด* เพราะ `IB=(VCC−VBE)/(RB+(β+1)RE)` → RE เพิ่ม → ตัวหารเพิ่ม → IB ลด → IC ลด; ผลอ้างอิง `IC 0.9401 mA`, `VCE 8.0328 V` | `IC = 940.10 µA = 0.9401 mA`, `VCE = 8.033 V`, `VE 1.899 V`, `VB 2.599 V` → **ลดจาก A3 จริง** (1.026 → 0.9401 mA, ΔVCE 0.0002 V) | **PASS** | `evaluate` ของฟอร์มหลัง POST: `{"mode":"emitter","vcc":"12","rb":"1000","rc":"2.2","re":"2","beta":"100","vbe":"0.70","r_unit":"kohm"}` → โหมดยัง emitter และทุกค่าอื่นเท่าเดิม มีแค่ RE เปลี่ยน |
| **A5 · อินพุตผิด** | OpenCode Browser: Fixed · คำนวณ `RB=1000` สำเร็จก่อน (มีผลเก่า) → เปลี่ยน `RB=0` → คำนวณ → snapshot + console | Fixed · `RB=0` | มีข้อความให้แก้ RB, เว็บไม่ล่ม (ไม่ 500), และ **ไม่แสดงผล 1.130 mA / 9.514 V ของรอบก่อน** | แจ้ง `"ค่า RB ต้องมากกว่า 0"` (role=alert); ผลลัพธ์เป็นข้อความเริ่มต้น `"กรอกค่าแล้วกด คำนวณ DC Bias ..."` ไม่มี `1.130 mA` / `9.514 V`; console error = 0; HTTP 200 | **PASS** | snapshot หลัง POST; ภาพ `docs/evidence/lab03-a5-fixed-rb0.jpeg`; `test_zero_rb_error_has_no_stale_result` |

**ที่มาของข้อความ A5:** ข้อความ `"ค่า RB ต้องมากกว่า 0"` มาจาก **Flask** (`dc_bias._validate_common` → `ValueError` → route ส่งกลับพร้อม `result=None`) ไม่ใช่ข้อจำกัดจาก HTML — ฟอร์มใช้ `type="number"` ซึ่งยอมรับ `0` ได้ (`required` กันเฉพาะช่องว่าง) จึงพิสูจน์ว่ามีการตรวจอินพุตฝั่ง Flask จริงตามที่ใบงานต้องการ

### 9.3 หลักฐานเพิ่มเติม

- ผลรัน test หลัง implement ครบทั้ง 3 โหมด: `.venv\Scripts\python.exe -m unittest discover -s tests -v` → **Ran 29 tests — OK**
- ภาพหน้าจอกรณี A5 (ข้อความ error + ไม่มีผลค้าง): `docs/evidence/lab03-a5-fixed-rb0.jpeg`
- ไฟล์ที่แนบในแชท (`image.png`) อ่านเนื้อหาไม่ได้จากโมเดลนี้ จึงยังไม่สามารถสรุปการสาธิตเชื่อม Playwright MCP ในภาพได้; ต้องให้เจ้าของงานพิมพ์ข้อความมาเพิ่มหากต้องการส่วนคะแนนนั้น
- ทุกค่าที่รายงานข้างต้นอ่านจาก accessibility snapshot ของหน้าเว็บจริงหลังกดปุ่ม ไม่ได้อ่านจากโค้ดหรือ unit test
