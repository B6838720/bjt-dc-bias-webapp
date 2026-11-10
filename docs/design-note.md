# Design Note — BJT DC Bias Web App

> เอกสารนี้สรุปสถาปัตยกรรมและเหตุผลการออกแบบ
> Design ฉบับเต็ม (พร้อมเกณฑ์รับคะแนน) อยู่ที่
> `docs/superpowers/specs/2026-11-10-bjt-dc-bias-webapp-design.md`

---

## 1. เป้าหมาย

รับค่า `VCC, R1, R2, RC, RE, β, VBE` จากฟอร์มเว็บ → คำนวณ DC Operating Point
ของวงจร BJT Common-Emitter แบบ Voltage-Divider Bias → แสดงผลใน Browser
โดยค่าที่แสดงต้องมาจาก Python จริง ไม่ใช่ค่าคงที่ใน HTML

---

## 2. สถาปัตยกรรม 3 ชั้น

```
┌─────────────────────────────┐
│ Browser                     │
│  templates/index.html       │  ← แสดงผลเท่านั้น (ไม่มีสมการ)
│  static/style.css           │
└──────────────┬──────────────┘
               │ HTTP GET / , POST /calculate
┌──────────────▼──────────────┐
│ Flask — app.py              │  ← routes, parsing string→float, formatting
│  • DEFAULT_FORM             │
│  • _parse_form()            │
│  • format_voltage/current   │
└──────────────┬──────────────┘
               │ เรียก calculate(**floats)
┌──────────────▼──────────────┐
│ dc_bias.py                  │  ← สมการ + validation + region detection
│  • calculate()              │     pure function, ไม่ import Flask
│  • _validate()              │
│  • _detect_region()         │
└─────────────────────────────┘
```

### ทำไมต้องแยก 3 ชั้น

| ชั้น | เหตุผล |
|---|---|
| `dc_bias.py` แยกออกมา | ทดสอบสมการได้โดยไม่ต้องเปิด server, ใช้ซ้ำได้ (CLI/notebook), และพิสูจน์ได้ว่า "ค่ามาจาก Python" ตามเกณฑ์ A2/A3 |
| `app.py` ไม่มีสมการ | ถ้ามีสมการปน จะมี 2 แหล่งความจริง (single source of truth หาย) และ test ทางวิศวกรรมจะปนกับ test HTTP |
| `index.html` ไม่มีสมการ | ป้องกันการคำนวณฝั่ง client ที่ตรวจสอบไม่ได้ และทำให้ template อ่านง่าย |

---

## 3. Data Flow

1. ผู้ใช้เปิด `GET /` → Flask render `index.html` พร้อม `DEFAULT_FORM` (ค่าเริ่มต้นเป็น string)
2. ผู้ใช้กรอกค่า → Browser ส่ง `POST /calculate` แบบ `application/x-www-form-urlencoded`
3. `app._parse_form()`:
   - อ่านค่าทีละ field ตาม `FIELD_LABELS`
   - ค่าว่าง → `ValueError("กรุณากรอก {label}")`
   - ไม่ใช่ตัวเลข → `ValueError("กรุณากรอก {label} เป็นตัวเลข")`
   - คูณ `r_unit` (kΩ → ×1000) เฉพาะ `r1, r2, rc, re`
4. `dc_bias.calculate(**values)`:
   - `_validate()` ตรวจความสมเหตุสมผลทางฟิสิกส์
   - คำนวณสมการ Forward-Active
   - ตรวจ `inf`/`nan`
   - `_detect_region()` → Cutoff / Saturation / Forward Active
   - ถ้า Cutoff → แทนค่าด้วยค่าจริงทางกายภาพ
   - สร้าง `warnings` ภาษาไทย
5. `app.calculate_route()` render `index.html` เดิมพร้อม `result` และ `form` (sticky values)
6. Template แสดง `region` เป็นป้ายสี, ตารางค่า, และ warning (ถ้ามี)

---

## 4. การตัดสินใจสำคัญ

| เรื่อง | ที่เลือก | เหตุผล |
|---|---|---|
| เส้นทาง | `GET /` + `POST /calculate` | ตรงเกณฑ์ A1/A2 และแยก test ได้ชัด |
| หน่วยตัวต้านทาน | dropdown กลาง 1 ตัว (Ω / kΩ) | ตรงข้อกำหนด "แปลง kΩ → Ω" โดยไม่ต้องมีช่องหน่วย 4 ช่อง |
| Validation | 2 ชั้น: `app.py` (string) + `dc_bias` (ฟิสิกส์) | รักษากติกา `dc_bias` ไม่รู้จัก HTTP และแยก test ได้ตรงชั้น |
| Error handling | `ValueError` + ข้อความไทย, ตอบ HTTP 200 | ผู้ใช้เห็นข้อความบนหน้าเดิม ไม่เจอ 500 |
| หลัง POST | render หน้าเดิม (ไม่ redirect) | คงค่าในฟอร์ม (sticky) และลดความซับซ้อน |
| Region precedence | Cutoff → Saturation → Forward Active | ภายใต้สมการนี้ `VCE > VCC` เป็น subset ของ Cutoff จึงไม่มี region `Invalid` |
| ค่านอก Forward Active | Cutoff → ค่าจริงทางกายภาพ, Saturation → ค่าจากสมการ + warning | กันไม่ให้รายงานแสดง `IC` ติดลบซึ่งดูผิด |
| กระแสศูนย์ | แสดง `0.000 mA` | ให้หน่วยสเกลเดียวกับค่ากระแสอื่น |

---

## 5. สัญญาระหว่างชั้น (Interface Contract)

```python
# dc_bias.py
REGION_ACTIVE     = "forward_active"
REGION_CUTOFF     = "cutoff"
REGION_SATURATION = "saturation"

calculate(vcc, r1, r2, rc, re, beta, vbe) -> {
    "vth": float, "rth": float,          # Ω
    "ib": float, "ic": float, "ie": float,  # A
    "vb": float, "ve": float, "vc": float, "vce": float,  # V
    "region": str,
    "model_applies": bool,
    "warnings": list[str],
}
```

```python
# app.py
DEFAULT_FORM: dict[str, str]
format_voltage(v: float) -> str   # "1.942 V"
format_current(a: float) -> str   # "1.230 mA" หรือ "12.30 µA"
_parse_form(form) -> dict[str, float]
```

Template ใช้ filter `|voltage` และ `|current` ที่ลงทะเบียนไว้ใน `app.py`
เพื่อให้ HTML ไม่ต้องรู้เรื่องการแปลงหน่วย

---

## 6. การทดสอบ

| ไฟล์ | จำนวน | ครอบอะไร |
|---|---|---|
| `tests/test_dc_bias.py` | 10 | ค่าอ้างอิง, monotonic β, validation, region, Cutoff physical values, β ทศนิยม |
| `tests/test_web.py` | 6 | `GET /`, `POST /calculate` (ค่าจริง, error, ค่าว่าง, Cutoff) |

รันด้วย `python -m unittest discover -s tests -v` → **16 tests, OK**

---

## 7. ข้อจำกัดที่รู้ตัว

- เป็น **Forward-Active approximation** ไม่ใช่ device model จริง
- `β` และ `VBE` คงที่ ไม่ขึ้นกับอุณหภูมิ/กระแส
- ไม่มี Early effect (`VA`)
- Saturation เป็นเพียงการเตือน — ยังแสดงค่าจากสมการเดิม
- ไม่มี persistence, authentication, หรือ API แบบ JSON
