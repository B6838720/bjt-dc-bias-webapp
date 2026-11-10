# BJT DC Bias Web App

Flask Web Application สำหรับคำนวณ **DC Operating Point** ของวงจรขยาย BJT
แบบ Common-Emitter, **Voltage-Divider Bias** โดยรับค่า `VCC, R1, R2, RC, RE, β, VBE`
ผ่านหน้าเว็บ แล้วให้ Python Backend คำนวณและส่งผลกลับมาแสดงใน Browser

> ขอบเขต Week 2: **DC Bias เท่านั้น** — ไม่มี AC analysis, Bode plot, Transient, Signal Generator หรือ SPICE solver

---

## 1. ภาพรวมสมการ (Forward-Active Approximation)

```
VTH = VCC × R2 / (R1 + R2)
RTH = R1·R2 / (R1 + R2)
IB  = (VTH − VBE) / (RTH + (β + 1)·RE)
IC  = β · IB
IE  = (β + 1) · IB
VE  = IE · RE
VB  = VE + VBE
VC  = VCC − IC · RC
VCE = VC − VE
```

หน่วยภายในของ `dc_bias.calculate()` คือ **Ω, V, A** (SI) — แปลงเป็น mA/µA
ที่ชั้นแสดงผลเท่านั้น

### ค่าอ้างอิงสำหรับตรวจ

`VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ, β=100, VBE=0.70 V`

| ปริมาณ | ค่า |
|---|---|
| VTH | 2.164 V |
| RTH | 18.03 kΩ |
| IB | 12.30 µA |
| IC | 1.230 mA |
| IE | 1.242 mA |
| VB | 1.942 V |
| VE | 1.242 V |
| VC | 9.294 V |
| VCE | 8.052 V |
| Region | Forward Active |

---

## 2. โครงสร้างโปรเจกต์

```
app.py                  Flask routes + parsing ฟอร์ม (ไม่มีสมการ)
dc_bias.py              สมการ DC Bias + validation + region detection (ไม่ import Flask)
templates/index.html    หน้าเว็บ (ไม่มีสมการ)
static/style.css        การจัดหน้า + responsive
tests/test_dc_bias.py   unit tests ของสมการ
tests/test_web.py       HTTP tests ของ Flask
docs/                   design note, validation evidence, reflection
```

---

## 3. การติดตั้งและรัน (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m flask --app app run --debug
```

เปิด Browser ที่ **<http://127.0.0.1:5000/>**

> ต้องรันผ่าน Flask เท่านั้น — เปิด `templates/index.html` ด้วย `file://`
> จะไม่มีการคำนวณ เพราะ Jinja2 template ต้องถูก render โดย Flask

---

## 4. การรัน Tests

```powershell
python -m unittest discover -s tests -v
```

ผลที่คาดหวัง: **16 tests, OK** (unit 10 + HTTP 6)

---

## 5. การตรวจ Operating Region

| ลำดับ | เงื่อนไข | Region | การแสดงผล |
|---|---|---|---|
| 1 | `VTH ≤ VBE` | **Cutoff** | ⚠️ ทรานซิสเตอร์ไม่นำกระแส — แสดงค่าจริงของวงจร (`IC=IE=0`, `VE=0`, `VC=VCC`, `VCE=VCC`, `VB=VTH`) |
| 2 | `VCE < 0.3 V` | **Saturation** | ⚠️ ไม่อยู่ใน Forward Active — สมการประมาณใช้ไม่ได้ ผลอาจคลาดเคลื่อน |
| 3 | อื่น ๆ | **Forward Active** | ✅ ใช้แบบจำลองได้ |

Region ถูกตัดสินตามลำดับจากบนลงล่าง (precedence) — Cutoff ชนะ Saturation เสมอ

---

## 6. Validation

Validation แบ่งเป็น 2 ชั้น:

- **`app.py`** — แปลง string → float, ข้อความเช่น `"กรุณากรอก VCC เป็นตัวเลข"` (HTTP 200 เสมอ ไม่ปล่อย 500)
- **`dc_bias.calculate()`** — รับ float เท่านั้น และ raise `ValueError` เมื่อ
  `VCC ≤ 0`, `R1/R2/RC/RE ≤ 0`, `β ≤ 0`, `VBE ≤ 0`, `VBE ≥ VCC`, `R1 + R2 ≤ 0`
  หรือผลลัพธ์เป็น `inf`/`nan`

---

## 7. ข้อจำกัดของแบบจำลอง

- ใช้ **Forward-Active approximation** — สมมติว่าทรานซิสเตอร์อยู่ใน active region
- `β` และ `VBE` ถือว่าคงที่ ไม่ขึ้นกับกระแสหรืออุณหภูมิ
- ไม่ได้แก้สมการ Early effect (`VA`), recombination, หรือ parasitic
- **ไม่ใช่ SPICE** — ไม่มีการทำ iterative solving หรือ device model จริง
- ไม่รองรับ AC analysis, ความถี่, Bode, Transient, Impedance, Gain
- ผลนอก Forward Active เป็นเพียงการเตือน ไม่ใช่การแก้สมการใหม่

### 7.1 ทำไมผลไม่ตรงกับแอปที่ใช้ "Approximate Analysis"

บางแอปหรือตำราบางเล่มใช้วิธี approximate ซึ่งละ `RTH` และถือว่า `VB ≈ VTH`:

```
IE ≈ (VTH − VBE) / RE
IC ≈ IE
```

วิธีนี้ใช้ได้เฉพาะเมื่อ **`β·RE ≥ 10·R2`** เท่านั้น

สำหรับค่าอ้างอิงของแล็บนี้ (`β=100, RE=1 kΩ, R2=22 kΩ`):

- `β·RE = 100 kΩ`
- `10·R2 = 220 kΩ`
- **100 kΩ < 220 kΩ → เงื่อนไขไม่ผ่าน**

ดังนั้นต้องใช้สมการ exact ที่คิด `RTH` (ได้ `IC = 1.230 mA` ไม่ใช่ `1.50 mA`)
ถ้าเห็นผลเป็น `1.50 mA` จากที่อื่น แปลว่าแอปนั้นใช้ approximate
ซึ่ง**ไม่ถูกต้องสำหรับค่าชุดนี้** — โปรเจกต์นี้จึงยึดสมการอ้างอิงในใบงาน

---

## 8. ขอบเขต Week 2 (สิ่งที่ยังไม่ทำ)

- ❌ AC / Small-signal analysis
- ❌ Bode plot / Frequency response
- ❌ Transient simulation
- ❌ Signal generator และ Overlay animation
- ❌ SPICE netlist / solver
- ❌ การบันทึกผลลงฐานข้อมูล หรือ export PDF

---

## 9. เอกสารเพิ่มเติม

- `docs/design-note.md` — สถาปัตยกรรมและเหตุผลการแยกชั้น
- `docs/validation.md` — ตารางเทียบค่า + หลักฐานการทดสอบ A1–A7
- `docs/reflection.md` — คำตอบคำถามรายบุคคลในใบงาน
- `docs/superpowers/specs/2026-11-10-bjt-dc-bias-webapp-design.md` — design ฉบับเต็ม
