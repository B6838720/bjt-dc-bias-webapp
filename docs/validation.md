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

---

## 10. คำถามปิด Lab

**คำถาม:** ถ้าตัวเลขคำนวณมือถูก แต่เปลี่ยน R<sub>E</sub> แล้วผลบนหน้าเว็บไม่เปลี่ยน
คุณจะตรวจค่าที่ส่งจากฟอร์มและค่าที่เข้าไปในฟังก์ชันอย่างไร?

**คำตอบ — ไล่ตรวจ 6 ชั้นจากหน้าเว็บเข้าไปถึงสมการ:**

1. **ยืนยันโหมดก่อน (สาเหตุที่พบบ่อยสุด):** ดูข้อความ `Common-Emitter · Emitter Bias …` และ hidden input
   `<input type="hidden" name="mode" value="{{ mode }}">` (`templates/index.html:37`) ต้องเป็น `emitter`
   ถ้าเป็น `fixed` ช่อง R<sub>E</sub> จะไม่ถูก render (`templates/index.html:67` แสดงเฉพาะ divider/emitter)
   และ `MODE_FIELDS[fixed]` (`app.py:21`) ไม่มี `re` → เปลี่ยน R<sub>E</sub> ไม่มีทางเปลี่ยนผล
   ตรวจใน browser ได้ด้วย `evaluate`: อ่าน `document.querySelector('input[name="mode"]').value`

2. **อ่านค่าจริงในช่องฟอร์มหลังกดคำนวณ:** ใช้ snapshot / `evaluate` อ่าน `input[name="re"]`
   ว่าขึ้น `2` หรือยังค้าง `1` (รอบ A4 ที่ตรวจจริงได้ `{"mode":"emitter","vcc":"12","rb":"1000",
   "rc":"2.2","re":"2","beta":"100","vbe":"0.70","r_unit":"kohm"}`) ถ้ายังเป็นค่เก่า แปลว่ากรอกผิดช่อง
   หรือหน้า render ใหม่จาก `DEFAULT_FORM`

3. **ดู POST body ที่ส่งจริง:** ใช้ `network.list` (urlContains `calculate`) → `network.get`
   (includeBody) ดูว่ามี `re=2` หรือ `re=1` ถ้า body ถูกแต่ผลไม่เปลี่ยน → ปัญหาฝั่ง Flask
   ถ้า body ผิด → ปัญหาอยู่ที่ `name` ของ input ใน template

4. **ตามเข้า Flask:** `app.py:101` เก็บ `request.form` ลง `form`; `_parse_form()` (`app.py:67–84`)
   ทำ `.strip()` → `float()` → คูณ 1000 เฉพาะ `RESISTOR_FIELDS` เมื่อ `r_unit=kohm`
   → `values["re"]` ต้องเป็น `2000.0` Ω ใส่ `print`/logging ชั่วคราวตรงนี้เพื่อดู `mode`, `form`,
   `values`, `values["re"]` ถ้ายังเป็น 1000 แปลว่า parse ผิดหรือโหมดผิด

5. **ตามเข้า function และสมการ:** ดู dispatch `app.py:111–113` ต้องส่ง `re=values["re"]` เข้า
   `calculate_emitter()` และ `dc_bias.py:143` ต้องเป็น `ib = (vcc - vbe) / (rb + (beta + 1) * re)`
   (R<sub>E</sub> อยู่ในตัวหาร) วิธีแยกปัญหาเร็ว: เรียก `calculate_emitter()` จาก Python โดยตรงสองรอบ
   `re=1000` กับ `re=2000` ถ้าผลต่าง → สมการถูก ปัญหาอยู่ที่ชั้นฟอร์ม–parse–dispatch
   ถ้าผลเท่ากัน → บั๊กอยู่ใน `dc_bias.py` (เช่น hardcode `re` หรือใช้ `rc` แทน)

6. **เช็คชั้นแสดงผลและใช้ test ช่วยตัดสิน:** `templates/index.html:112–113` ต้อง render
   `result.vce|voltage` และ `result.ic|current` ไม่ใช่ตัวเลข hardcode (`test_calculate_shows_backend_results`
   การันตีอยู่); `test_larger_re_reduces_ic` (`tests/test_dc_bias.py:118`) พิสูจน์ว่าฟังก์ชันตอบสนองต่อ
   R<sub>E</sub>, `test_emitter_mode_uses_re` (`tests/test_web.py`) พิสูจน์ว่า POST ผ่านเว็บส่งค่าเข้า
   สมการ ถ้า unit test ผ่านแต่ web test พัง → โฟกัส `app.py`/template; ถ้าทั้งคู่ผ่านแต่หน้าเว็บยังไม่เปลี่ยน
   → ถอยไปดู snapshot ใหม่ว่ากำลังอ่านผลรอบเก่าอยู่หรือไม่

**เส้นทางข้อมูล R<sub>E</sub> ใน A4 ของโปรเจกต์นี้ (ตอบข้อ 135–160 ด้วย):**

```
input#re (templates/index.html:70)  --POST re=2-->
app.py:101 form["re"]  -->  _parse_form() app.py:84  values["re"] = 2 × 1000 = 2000.0 Ω
-->  app.py:113 calculate_emitter(re=values["re"])
-->  dc_bias.py:143 ib = (12 − 0.70) / (1e6 + 101 × 2000) = 9.401 µA
-->  _summarize() ic = β·ib = 0.9401 mA
-->  templates/index.html:113 result.ic|current
-->  snapshot จริง: IC = 940.10 µA (ลดจาก A3 ที่ 1.026 mA)
```

**สรุปสั้น:** ไล่ตามลำดับ โหมด → ค่าใน input → POST body → `request.form`/`values["re"]` →
argument ของ `calculate_emitter()` → ตัวหาร `(β+1)R<sub>E</sub>` → `result.ic`/`result.vce` ที่แสดง
จุดที่ค่าหายหรือถูกแทนที่คือจุดที่ต้องแก้

---

## 11. Lab 04 — Browser Acceptance B1–B8 (2026-11-24)

### 11.1 สภาพแวดล้อมที่ใช้รันจริง

| รายการ | ค่าจริง |
|---|---|
| Browser | OpenCode Browser (Chromium) ผ่าน `http://127.0.0.1:5000/` — ใช้ `navigate/snapshot/evaluate/wait/screenshot/network` |
| Playwright MCP | **NOT RUN** — ไม่มี MCP resource ชื่อ playwright ใน workspace; ใช้ OpenCode Browser แทนตามข้อ 3 ของใบงาน |
| ngspice | **ngspice-41** console build (`ngspice_con.exe`) ติดตั้งด้วย micromamba/conda-forge `ngspice-exe=41 h295a5eb_0` |
| คำสั่งจริงที่ adapter เรียก | `ngspice_con.exe -b -o <run.log> <circuit.cir>` (argv list, ไม่ใช้ `shell=True`) |
| BJT model | `PN2222` จาก ngspice source repo: `examples/tclspice/tcl-testbench1/PN2222.mod`, commit `032b1c32c4dbad45ff132bcfac1dbecadbd8abb0`, blob `d683d374e82704e64fc10884941de711e8bdfb3c`; คัดลอกไว้ที่ `models/ngspice/PN2222.mod` พร้อม `models/ngspice/SOURCE.md` |
| ข้อควรระวัง | model card ระบุ `* Fairchild pid=19 case=TO92` — **ไม่ใช่ Starter Kit ที่อาจารย์แจก** ผล SPICE จึงต่างจาก Analytical Lab 3 ได้ และห้ามปรับค่าจริงให้ตรง |
| Test suite | `.venv\Scripts\python.exe -m unittest discover -s tests` → **Ran 52 tests — OK** (Lab 3 เดิม 29 + adapter/HTTP 23 รวมกรณี log จริงและ phase rad→deg) |
| Impeccable | ติดตั้ง project scope แล้ว; detector รอบสุดท้ายคืน `[]`; stylesheet ที่ใช้คือ `/static/style.css` |

> 21–23 tests ที่ใช้ fake runner/mock engine พิสูจน์โครง/netlist/parser/error path เท่านั้น  
> **หลักฐาน B2–B6 ในตารางด้านล่างมาจาก ngspice-41 ที่รันจริงแล้วอ่านค่าจากหน้าเว็บหลัง POST ไม่ได้มาจาก mock**

### 11.2 ผลตรวจรับ B1–B8

| Case | การตรวจใน Browser | ผลจริงที่อ่านได้ | Status | หลักฐาน |
|---|---|---|---|---|
| **B1 · Regression** | เปิด `GET /?mode=...` แล้ว POST `/calculate` ครบ 3 โหมด | Divider `IC=1.230 mA, VCE=8.052 V`; Fixed `IC=1.130 mA, VCE=9.514 V`; Emitter `IC=1.026 mA, VCE=8.705 V` — ตรง A1–A5 เดิมทุกค่า | **PASS** | snapshot หลัง POST ของแต่ละโหมด + `tests/test_web.py` 14 เคสผ่าน |
| **B2 · DC SPICE** | เลือก `DC · .op` → Run ด้วยค่าเริ่มต้น `RE=1 kΩ` | Badge `✓ ngspice · success · DC Operating Point (.op)`; `VB=2.016 V, VE=1.364 V, VC=9.017 V, VCE=7.653 V, IC=1.356 mA`; model `PN2222`; warning ระบุ IC/VCE ถูก derive จาก node voltage จริง | **PASS** | `docs/evidence/lab04-after/ac-real-ngspice.png` (หน้าเดียวกันแสดง Analytical Reference เปรียบเทียบ), netlist/log ในข้อ 11.3 |
| **B3 · เปลี่ยน RE** | เปลี่ยนเฉพาะ `RE` จาก `1` เป็น `2 kΩ` แล้ว Run DC ซ้ำ | Netlist เปลี่ยนเป็น `RE emitter 0 2000`; `VB 2.016→2.082 V`, `VE 1.364→1.447 V`, `VC 9.017→10.418 V`, `VCE 7.653→8.971 V`, `IC 1.356 mA→718.93 µA` — เปลี่ยนจริงตาม netlist ไม่ใช่ค่าค้าง | **PASS** | snapshot สองรอบ + บรรทัด `RE emitter 0 2000` ใน netlist ที่หน้าเว็บแสดง |
| **B4 · AC** | เลือก `AC · .ac` → Run sweep `DEC 20 1 10000000` | Badge success; `Peak gain 4.90 dB`, `Gain @ 1 kHz 4.90 dB`, `Phase @ 1 kHz -179.9 °`, `−3 dB point 1.78 Hz`; กราฟ gain/phase มี **141 points** จาก `series` จริง; phase แปลงจาก `vp()` (radian) เป็นองศา | **PASS** | `docs/evidence/lab04-after/ac-real-ngspice.png`, `...-390.png`; log excerpt ข้อ 11.3 |
| **B5 · Transient** | เลือก `Transient · .tran` → Run ที่ `Amplitude=10 mV, Frequency=1 kHz` | Badge success; `Vin peak 0.0100 V`, `Vout peak 0.0176 V`, `Time end 0.00500 s`, `Phase relation inverted`; กราฟ Vin/Vout มี **295 points** จาก log จริง; correlation ≈ −0.999998 | **PASS** | `docs/evidence/lab04-after/tran-real-ngspice.png` |
| **B6 · เปลี่ยน Source** | คง `RE=1 kΩ`, เปลี่ยน `Amplitude=20 mV`, `Frequency=500 Hz` แล้ว Run transient ซ้ำ | Netlist เปลี่ยนเป็น `Vin input 0 DC 0 AC 0.02 SIN(0 0.02 500)`; `Vin peak 0.0200 V`, `Vout peak 0.0353 V` (เทียบ B5 เดิม `0.0100/0.0176 V`); polyline ของ Vin/Vout เปลี่ยนจริง | **PASS** | snapshot หลัง POST + บรรทัด `SIN(...)` ใน netlist; `Vin/Vout` samples เปลี่ยนจากรอบก่อน |
| **B7 · Invalid/Fail** | ตั้ง `RE=0` แล้ว Run (หลังจากมีผลสำเร็จอยู่แล้ว) | แจ้ง `Simulation Error: RE ต้องมากกว่า 0`; ไม่มี badge `ngspice · success`; ไม่มีค่าเก่า `0.0200 V` ค้าง; console error = 0; HTTP 200 | **PASS** | snapshot หลัง POST + `test_engine_error_shows_error_and_no_stale_success` |
| **B8 · UI Desktop/Mobile** | เปิดหน้าเดิมที่ ~1280px และ ~390px, สลับโหมด DC Bias และดูกราฟ SPICE | ปุ่ม/ฟอร์ม/หน่วยอ่านได้ ไม่ถูกตัด; กราฟ AC/Transient แสดงผลจริงได้ทั้งสองขนาด; Perceived Performance ปรับแล้ว ( detector `[]`) | **PASS** | `lab04-before/1280x900-full.png` → `lab04-after/1280x900-full.png`; `lab04-before/390x844-full.png` → `lab04-after/390x844-full.png`; `lab04-after/ac-real-ngspice*.png` |

**สรุป:** B1–B8 ผ่านทั้ง 8 กรณีด้วย ngspice จริง ไม่มี `NOT RUN` เหลือในตารางรับรอบนี้

### 11.3 Netlist / log excerpt จากรอบรันจริง

DC (`RE=1 kΩ`):

```text
VCC vcc 0 DC 12
R1 vcc base 100000
R2 base 0 22000
RC vcc collector 2200
RE emitter 0 1000
Q1 collector base emitter PN2222
.model PN2222   NPN(Is=14.34f Xti=3 Eg=1.11 Vaf=74.03 Bf=255.9 ...)
.op
.end
```

```text
BJT: Bipolar Junction Transistor
     device                    q1
      model                pn2222
         ic            0.00135619
         ib           8.21767e-06
         vbe              0.651451
Resistor: Simple linear resistor
     device                re                    rc
          i            0.00136423            0.00135601
```

AC (สังเกตว่าตาราง `vdb` และ `vp` ถูก join ด้วย frequency):

```text
.ac DEC 20 1 10000000
.print ac vdb(output) vdb(input) vp(output) vp(input)

Index   frequency       vdb(output)     vdb(input)
60      1.000000e+03    -3.51007e+01    -4.00000e+01
Index   frequency       vp(output)      vp(input)
60      1.000000e+03    -3.13938e+00    0.000000e+00
```

Transient (`SIN(0 0.01 1000)`):

```text
.tran 1e-06 0.005
.print tran v(input) v(output)

Index   time            v(input)        v(output)
0       0.000000e+00    0.000000e+00    0.000000e+00
1       1.000000e-08    6.283185e-07   -2.39166e-05
2       2.000000e-08    1.256637e-06   -1.58780e-05
```

### 11.4 ไฟล์หลักฐานที่เพิ่มในรอบ Lab 04

- `models/ngspice/PN2222.mod` — model card จริงที่ ngspice อ่าน
- `models/ngspice/SOURCE.md` — provenance (repo/commit/blob) และข้อความว่าไม่ใช่ Starter Kit
- `docs/evidence/lab04-before/1280x900-full.png`, `docs/evidence/lab04-before/390x844-full.png`
- `docs/evidence/lab04-after/1280x900-full.png`, `docs/evidence/lab04-after/390x844-full.png`
- `docs/evidence/lab04-after/ac-real-ngspice.png` — Bode gain + phase และตารางเทียบ Analytical
- `docs/evidence/lab04-after/ac-real-ngspice-390.png` — กราฟ AC แบบแคบ
- `docs/evidence/lab04-after/tran-real-ngspice.png` — waveform Vin/Vout จริงจาก `.tran`
- `docs/evidence/lab04-after/b1-b8/` — screenshot รายเคสหลังตรวจรับ: `b1-divider/fixed/emitter`, `b2-dc-spice`, `b3-re-2k`, `b4-ac-spice`, `b5-tran-spice`, `b6-source-changed`, `b7-invalid-re`, `b8-desktop/mobile`
