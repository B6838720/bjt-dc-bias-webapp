# Design (short) — Lab 03: สามวงจรไบอัสในเว็บ Flask เดิม

> วันที่: 2026-11-17 · ขั้นตอนที่ 2 ของใบงาน Lab 03
> ผลที่ต้องได้ตามใบงาน: **ตารางค่าคาดหมายและแผนสั้น** (เอกสารนี้ + `docs/lab03-baseline.md`)

---

## 1. Intent / ทำไม

ต่อยอดเว็บ Lab 02 (Voltage Divider เดียว) ให้เลือกได้ 3 โหมด โดยเพิ่ม **Fixed Bias** และ
**Emitter Bias แบบแหล่งจ่ายเดียว** ด้วยโค้ดที่ AI เขียนตามสมการที่เราทวนแล้ว **ผล Divider เดิม
ต้องไม่เปลี่ยน** และต้องพิสูจน์ผลผ่าน browser ด้วยตาราง A1–A5

## 2. Goals / Non-goals / Anti-goals

- **Goals:** แยกฟังก์ชันคำนวณใหม่ใน Python, dispatch ตามโหมดใน Flask, ตรวจอินพุตรายโหมด,
  แสดงผล/ข้อผิดพลาดระบุโหมด, คงผลเดิม, มีค่าอ้างอิงอิสระ
- **Non-goals:** SPICE, DC Load Line, AC/Transient, bypass capacitor, unittest ใหม่ตามใบงาน
  (แต่ `AGENTS.md` บังคับ TDD — ให้เพิ่ม test ใหม่ตามกติกาโปรเจกต์), Playwright script
- **Anti-goals (ถ้าเกิดถือว่าล้มเหลว):** ย้ายสมการไป HTML, สร้างโปรเจกต์ใหม่, เปลี่ยนชื่อคีย์
  ทำให้ test เดิมพัง, แสดงผลรอบก่อนเมื่อกรอกผิด, เดาเป็น Divider เมื่อโหมดไม่รู้จัก

## 3. Constraints

- เคารพ `AGENTS.md`: `dc_bias.py` ห้าม import flask, `app.py` ห้ามมีสมการ, HTML ห้ามคำนวณ
- หน่วยภายใน Ω/V/A; แปลง kΩ→Ω **ครั้งเดียว** ตอนรับฟอร์ม (โค้ดเดิมทำอยู่แล้ว)
- UI/error ภาษาไทย; แรงดัน 3 ตำแหน่ง, กระแส mA 3 ตำแหน่ง
- ใบงานอนุญาตใช้ชื่อคีย์เดิมของ Lab 2 ได้ → **คง `vb, ve, vc, vce, ic, ib, ie, region,
  model_applies, warnings`**
- ใบงานบอก "ไม่จำเป็นต้องเพิ่ม JavaScript" → เลือกวิธี refresh ฝั่ง server

## 4. Approaches ที่พิจารณา

### 4.1 การเปลี่ยนโหมดบนฟอร์ม

| ทางเลือก | ข้อดี | ข้อเสีย | ตัดสิน |
|---|---|---|---|
| **A. `<select name="mode">` + ปุ่ม “เปลี่ยนโหมด” ส่ง GET `/?mode=...` แล้ว Jinja render เฉพาะช่องของโหมด + hidden `mode` ตอน POST** | ไม่มี JS, ตรงคำว่า “เลือกโหมดแล้วโหลดฟอร์มใหม่”, snapshot อ่านง่าย, ไม่มีค่าเก่าค้าง | มีรอบ往返额外 1 รอบตอนเปลี่ยนโหมด | **เลือก** |
| B. JavaScript show/hide/channel disabled | ไม่ reload | ใบงานบอกไม่จำเป็น, เพิ่มพื้นที่ที่ต้องตรวจ | ไม่เลือก |
| C. แสดงทุกช่องแล้ว `disabled` รายโหมด | ทำง่ายสุด | ไม่ตรง “เห็นช่องที่ใช้เท่านั้น” และ snapshot เห็นช่องเกิน | ไม่เลือก |

### 4.2 โครงสร้างฟังก์ชันคำนวณ

| ทางเลือก | ตัดสิน |
|---|---|
| **A. คง `calculate()` เดิม + เพิ่ม `calculate_fixed()` / `calculate_emitter()` เป็น pure function น้องกัน + dispatcher ใน `app.py`** | **เลือก** — แยกสมการชัด, lab ให้เพิ่มฟังก์ชันแยกกัน, test เดิมไม่กระทบ |
| B. เปลี่ยน `calculate()` ให้รับ `mode` | ไม่เลือก — ผิดสัญญา `AGENTS.md` และทำให้ Divider เสี่ยงเปลี่ยน |
| C. class/strategy hierarchy | ไม่เลือก — เกินความจำเป็นของแล็บนี้ |

### 4.3 การเตือนเมื่อแบบจำลองใช้ไม่ได้

ใบงานว่าเตือนเมื่อ `I_B ≤ 0` หรือ `V_CE ≤ 0.2 V`; โค้ดเดิมใช้ `V_TH ≤ V_BE` (cutoff) และ
`V_CE < 0.3 V` (saturation) **ตัดสิน:** ใช้ helper เดิมร่วมกันทุกโหมด + เพิ่มเช็ค `I_B ≤ 0`
→ ครอบคลุม 0.2 V และทำให้ threshold เข้มงวดขึ้น แต่ยังไม่เปลี่ยนผล Divider เดิม

## 5. ตารางค่าคาดหมาย (อิสระจากโปรแกรมที่ตรวจ)

คำนวณด้วยสคริปต์แยกที่ **ไม่ import `dc_bias.py`** จากสมการข้อ 1 เท่านั้น
ใช้ร่วมกัน: V<sub>CC</sub>=12 V, R<sub>C</sub>=2.2 kΩ, β=100, V<sub>BE</sub>=0.70 V
เกณฑ์: |ΔI<sub>C</sub>| ≤ 0.01 mA, |ΔV<sub>CE</sub>| ≤ 0.02 V

| กรณี | โหมด / อินพุต | I<sub>B</sub> | I<sub>C</sub> | V<sub>E</sub> | V<sub>B</sub> | V<sub>CE</sub> | หมายเหตุ |
|---|---|---|---|---|---|---|---|
| A1 | Divider 100k / 22k / 1k | 12.2986 µA | 1.2299 mA | 1.2422 V | 1.9422 V | 8.0522 V | ตรง baseline เดิม every ค่า |
| A2 | Fixed R<sub>B</sub>=1 MΩ | 11.3000 µA | 1.1300 mA | 0 V | 0.7000 V | 9.5140 V | ไม่ต้องกรอก R<sub>E</sub> |
| A3 | Emitter R<sub>B</sub>=1 MΩ, R<sub>E</sub>=1 kΩ | 10.2634 µA | 1.0263 mA | 1.0366 V | 1.7366 V | 8.7054 V | ต้องเห็นช่อง R<sub>E</sub> |
| A4 | Emitter R<sub>B</sub>=1 MΩ, R<sub>E</sub>=2 kΩ | 9.4010 µA | 0.9401 mA | 1.8990 V | 2.5990 V | 8.0328 V | **I<sub>C</sub> ลดจาก A3** เพราะตัวหาร R<sub>B</sub>+(β+1)R<sub>E</sub> เพิ่ม |
| A5 | Fixed R<sub>B</sub>=0 | — | — | — | — | — | ต้อง error เว็บไม่ล่ม ไม่โชว์ผลเก่า |

## 6. แผนแก้ไฟล์ (ยังไม่ implement)

| ไฟล์ | การเปลี่ยน |
|---|---|
| `dc_bias.py` | คง `calculate()` เดิมแบบไม่แตะพฤติกรรม · แยก `_finalize(ib, re, ...)` ใช้ร่วม · เพิ่ม `calculate_fixed()` และ `calculate_emitter()` คืน dict ชุดเดิม |
| `app.py` | `DEFAULT_FORM` เพิ่ม `mode="divider"` · `FIELD_LABELS` เป็นรายโหมด (`MODE_FIELDS`) · `_parse_form(mode)` ตรวจเฉพาะช่องที่ใช้ + finite · `calculate_route()` dispatch ด้วย `if/elif` · โหมดไม่รู้จัก → ข้อความไทย · ส่ง `mode` กลับ template ทุกครั้ง |
| `templates/index.html` | select โหมด + ปุ่ม “เปลี่ยนโหมด” (GET) · render field ตาม `mode` · hidden `mode` ในฟอร์มคำนวณ · ป้ายผล/error มีชื่อโหมด · ไม่แสดง `result` เมื่อ `error` |
| `static/style.css` | ปรับเล็กน้อยถ้าจำเป็น (ปุ่มเลือกโหมด) |
| `tests/test_dc_bias.py` | เพิ่ม test ของฟังก์ชันใหม่ (เขียน failing ก่อนตาม TDD) + ยืนยัน Divider เดิมยังผ่าน |
| `tests/test_web.py` | เพิ่ม test dispatch/error รายโหมด + ยืนยัน 16 เดิมผ่าน |
| `docs/validation.md` | แทนที่/เพิ่มตาราง A1–A5 และผลจริงหลังรัน browser |
| `docs/lab03-baseline.md` | เก็บไว้เป็นหลักฐานก่อนแก้ (ทำแล้ว) |

## 7. Interfaces

```python
calculate(vcc, r1, r2, rc, re, beta, vbe) -> dict          # เดิม 100%
calculate_fixed(vcc, rb, rc, beta, vbe) -> dict             # ใหม่
calculate_emitter(vcc, rb, rc, re, beta, vbe) -> dict       # ใหม่
# dict ทุกตัวมี: vb, ve, vc, vce, ic, ib, ie (SI), region, model_applies, warnings
```

```python
_parse_form(form, mode) -> dict[str, float]   # เฉพาะฟิลด์ของโหมดนั้น, คูณ kΩ→Ω
calculate_route(): mode = request.form.get("mode") or request.args.get("mode")
   if mode == "fixed": ... elif mode == "emitter": ... elif mode == "divider": ...
   else: error "โหมดไม่รู้จัก"
```

## 8. Tests strategy

1. เขียน test ใหม่ที่ fail ก่อน (fixed/emitter ค่าตามตารางข้อ 5, A5 invalid, unknown mode)
2. รัน `python -m unittest discover -s tests -v` → เห็น fail จริง
3. เขียนโค้ดขั้นต่ำให้ผ่าน → รันใหม่ → ต้องผ่าน **16 เดิม + ใหม่**
4. ค่อยให้ browser ตรวจ A1–A5 ตามตาราง (ขั้นตอนที่ 5–6 ของใบงาน)

## 9. สิ่งที่ยังต้องระวัง

- **Stale result:** ถ้า error ต้อง render `result=None` เสมอ (A5)
- **A3→A4:** ต้องยืนยัน mode ยังเป็น emitter และค่าเดิมเท่าเดิม เปลี่ยนแค่ R<sub>E</sub>
- **MCP:** ยังไม่มี `opencode.json` / playwright ในเซสชันนี้ → ทำขั้นตอนที่ 5 แยก
- ภาพ `image.png` จากผู้ใช้ยังอ่านไม่ได้ → ยังไม่สรุปเนื้อหา demo
