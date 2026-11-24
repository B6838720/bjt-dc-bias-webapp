# BJT DC Bias Web App → BJT Amplifier Simulator v1

Flask Web Application สำหรับคำนวณ **DC Operating Point** ของวงจรขยาย BJT แบบ Common-Emitter
ผ่านหน้าเว็บ แล้วให้ Python Backend คำนวณและส่งผลกลับมาแสดงใน Browser

**Lab 04** ต่อยอดแอปเดิมด้วย CE Voltage Divider อ้างอิง 1 วงจร และเชื่อม `ngspice`
เพื่อรัน `.op`, `.ac`, `.tran` จริง ผลทุกชุดมีป้ายแหล่งที่มาแยกจากผล Analytical ของ Lab 3

รองรับ **3 โหมดไบอัส** (เลือกจาก dropdown `เลือกวงจรไบอัส` แล้วกด `เปลี่ยนโหมด`):

| โหมด | ช่องที่ใช้ |
|---|---|
| `divider` — Voltage Divider Bias (ค่าเริ่มต้น, ผลตรง Lab 2 ทุกประการ) | `VCC, R1, R2, RC, RE, β, VBE` |
| `fixed` — Fixed Bias (emitter ต่อ GND, ไม่มีช่อง `RE`) | `VCC, RB, RC, β, VBE` |
| `emitter` — Emitter Bias (RB + RE) | `VCC, RB, RC, RE, β, VBE` |

> ขอบเขต Lab 2–3: DC Bias 3 แบบ · ขอบเขต Lab 4: + CE SPICE DC/AC/Transient 1 วงจรอ้างอิง  
> ยังไม่ทำ circuit editor อิสระ, FET, Animation overlay หรือ deploy สาธารณะ

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

สมการของโหมดที่เพิ่มใน Lab 03 (ทั้งสองใช้ `_summarize()` ร่วมกับ `calculate()`):

```
Fixed:    IB = (VCC − VBE) / RB                     , VE = 0
Emitter:  IB = (VCC − VBE) / (RB + (β + 1)·RE)
          IC = β·IB, IE = (β+1)·IB, VE = IE·RE, VB = VE + VBE
          VC = VCC − IC·RC, VCE = VC − VE
```

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

ค่าอ้างอิงโหมดใหม่ (ใช้ค่าร่วม `VCC=12 V, RC=2.2 kΩ, β=100, VBE=0.70 V`):

| โหมด | อินพุตเพิ่ม | IC | VCE |
|---|---|---|---|
| Fixed | `RB = 1 MΩ` | 1.130 mA | 9.514 V |
| Emitter | `RB = 1 MΩ, RE = 1 kΩ` | 1.026 mA | 8.705 V |
| Emitter | `RB = 1 MΩ, RE = 2 kΩ` | 0.940 mA | 8.033 V (IC ลดลง) |

---

## 2. โครงสร้างโปรเจกต์

```
app.py                  Flask routes + parsing ฟอร์ม + dispatch (ไม่มีสมการ/netlist)
dc_bias.py              สมการ DC Bias + validation + region detection (ไม่ import Flask)
spice_engine.py         Lab 04 adapter: netlist → ngspice batch → parse log → provenance
templates/index.html    ฟอร์ม Lab 3 + ฟอร์ม/ผล/กราฟ Lab 04 (ไม่มีสมการ)
static/style.css        การจัดหน้า + responsive + chart styling
tests/test_dc_bias.py   unit tests ของสมการ Analytical
tests/test_web.py       HTTP tests ของ /calculate (Lab 3 regression)
tests/test_spice_engine.py  netlist/parser/error tests (fake runner, ไม่ต้องมี ngspice)
tests/test_web_spice.py     HTTP tests ของ /simulate (mock engine)
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

ผลที่คาดหวังหลัง Lab 04: **52 tests, OK**
(29 เดิมจาก Lab 3 + 17 adapter tests + 6 HTTP simulator tests)

> adapter/HTTP tests ส่วนใหญ่ใช้ fake runner/mock engine จึงรันได้แม้ยังไม่ได้ติดตั้ง ngspice
> แต่ **ไม่ใช่หลักฐานผลจำลองจริง** — หลักฐาน B2–B6 มาจากการรัน ngspice-41 จริงแล้วอ่านจาก browser
> ดู `docs/validation.md` ข้อ 11

```powershell
# ตรวจว่า remote ตรงกับ repo ของงาน
git remote -v
git log --oneline -5
```

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
- **`dc_bias.calculate_fixed()` / `calculate_emitter()`** — ใช้ `_validate_common()`
  ร่วมกัน และตรวจ `RB ≤ 0` / `RE ≤ 0` เพิ่มเติม; เมื่อ `IB ≤ 0` จะเพิ่ม warning
  ว่าแบบจำลอง Forward Active อาจใช้ไม่ได้; โหมด `bogus` ได้ error ไทย ไม่ fallback เป็น Divider

---

## 7. ข้อจำกัดของแบบจำลอง Analytical (`dc_bias.py`)

ข้อความนี้หมายถึง **ผลอ้างอิงจาก Lab 3 เท่านั้น** ไม่ได้หมายถึงผล SPICE ใน Lab 4

- ใช้ **Forward-Active approximation** — สมมติว่าทรานซิสเตอร์อยู่ใน active region
- `β` และ `VBE` ถือว่าคงที่ ไม่ขึ้นกับกระแสหรืออุณหภูมิ
- ไม่ได้แก้สมการ Early effect (`VA`), recombination, หรือ parasitic
- **ไม่ใช่ SPICE** — ไม่มีการทำ iterative solving หรือ device model จริง
- ไม่รองรับ AC analysis, ความถี่, Bode, Transient, Impedance, Gain
- ผลนอก Forward Active เป็นเพียงการเตือน ไม่ใช่การแก้สมการใหม่

ผลจาก `ngspice` ถูกแสดงคนละป้ายกับตารางนี้ และอาจต่างจากตัวเลขข้างต้นได้
เพราะขึ้นกับ BJT model และสภาวะจริงของ solver

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

## 8. Lab 04 — CE Amplifier Simulator (ngspice)

### 8.1 สิ่งที่เพิ่ม

- เลือก Analysis Mode ได้ 3 แบบ: `DC · .op`, `AC · .ac`, `Transient · .tran`
- ฟอร์ม CE Voltage Divider อ้างอิง: `VCC, R1, R2, RC, RE, RL, Cin, Cout`
- แหล่งสัญญาณ: `Amplitude (mV peak)` และ `Frequency (Hz)`
- `spice_engine.py` สร้าง netlist เรียก ngspice แบบ batch และ parse log จริง
- กราฟ Gain/Phase และ Vin/Vout ถูกสร้างจาก series ที่ parse ได้ ไม่ใช่ค่าคงที่ใน HTML
- แสดง engine status, model name/source, unit, provenance และ ngspice log excerpt
- ผล Analytical จาก `dc_bias.py` ถูกแสดงคนละป้ายกับผล SPICE

### 8.2 ติดตั้ง ngspice

ngspice เป็น **โปรแกรมภายนอก** ไม่ใช่ `pip install` ตรวจด้วย:

```powershell
ngspice --version
```

ดาวน์โหลดตามระบบปฏิบัติการ: <https://ngspice.sourceforge.io/download.html>

ถ้า executable ไม่อยู่ใน PATH ตั้งก่อนรัน Flask:

```powershell
$env:NGSPICE_EXECUTABLE = "C:\path\to\ngspice.exe"
```

### 8.3 BJT Model ที่ใช้จริง (Lab 04)

 Starter Kit ที่อาจารย์แจกยังไม่มีใน workspace นี้ ตามที่ผู้ใช้เลือกข้อ 2 จึงใช้
 **model จาก ngspice source repo แทน พร้อม provenance** (ไม่เดาค่าเอง):

- ชื่อโมเดล: `PN2222`
- ไฟล์: `models/ngspice/PN2222.mod`
- ต้นทาง: `examples/tclspice/tcl-testbench1/PN2222.mod`
- repo commit: `032b1c32c4dbad45ff132bcfac1dbecadbd8abb0`
- blob: `d683d374e82704e64fc10884941de711e8bdfb3c`
- รายละเอียดเพิ่มเติม: `models/ngspice/SOURCE.md`
- model card ระบุ `* Fairchild pid=19 case=TO92` → **ไม่ใช่ Starter Kit**

ตั้งค่าแทนการกรอกในฟอร์มได้ด้วย:

```powershell
$env:NGSPICE_MODEL_NAME = "PN2222"
$env:NGSPICE_MODEL_FILE = "C:\path\to\repo\models\ngspice\PN2222.mod"
```

หรือใช้ `NGSPICE_MODEL_TEXT` / ช่อง `Model name` + `Model card` ในหน้าเว็บได้
(ค่าที่กรอกในฟอร์มจะแทนที่ env)

### 8.4 การรัน

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m flask --app app run --debug
```

เปิด <http://127.0.0.1:5000/> → เลือก Analysis Mode → ปรับค่า → กด **Run Simulation**

คำสั่งที่ adapter เรียกจริงมีรูปแบบ:

```text
ngspice -b -o <run.log> <circuit.cir>
```

ไม่ใช้ `shell=True`, มี `timeout`, และใช้ working directory ชั่วคราวแยกต่อรอบ

### 8.5 ผลการตรวจ Lab 04

- รันจริงด้วย **ngspice-41** (`ngspice_con.exe`) และ model `PN2222` จาก ngspice source repo
- **52 tests ผ่าน** และ B1–B8 ผ่านด้วย browser จริง (ดู `docs/validation.md` ข้อ 11)
- ผล SPICE ต่างจาก Analytical Lab 3 ได้ (คนละ model) จึงแยกป้าย `SPICE (ngspice)` กับ `Analytical (Lab 3)` เสมอ
- เมื่อ engine fail หน้าเว็บแสดง `Simulation Error` และไม่โชว์ badge Success หรือค่าจากรอบก่อน
- `ngspice.exe` เป็น GUI และอาจ hang → ใช้ `ngspice_con.exe` เสมอ

### 8.6 สรุปการตั้งค่าและผลที่ใช้ตรวจรับ (Publish Evidence)

| รายการ | ค่าที่ใช้จริง / ผลที่ได้ |
|---|---|
| `NGSPICE_EXECUTABLE` | `ngspice_con.exe` (console build); ใช้ path ของเครื่องผู้ตรวจ เช่น `C:\path\to\ngspice_con.exe` **ห้ามใช้ `ngspice.exe`** |
| `NGSPICE_MODEL_NAME` | `PN2222` |
| `NGSPICE_MODEL_FILE` | `$PWD\models\ngspice\PN2222.mod` |
| ngspice version | `ngspice-41` (conda-forge `ngspice-exe=41 h295a5eb_0`) |
| model provenance | ngspice source repo `examples/tclspice/tcl-testbench1/PN2222.mod`, commit `032b1c32...`, blob `d683d374...`; ไม่ใช่ Starter Kit |
| Test | `python -m unittest discover -s tests -v` → **52 tests, OK** |
| B1 Regression | Divider `IC 1.230 mA / VCE 8.052 V`; Fixed `1.130 mA / 9.514 V`; Emitter `1.026 mA / 8.705 V` |
| B2 DC SPICE | `VB 2.016 V, VE 1.364 V, VC 9.017 V, VCE 7.653 V, IC 1.356 mA` |
| B3 เปลี่ยน RE `1→2 kΩ` | `IC 1.356 mA → 718.93 µA`, `VCE 7.653 → 8.971 V`; netlist `RE emitter 0 2000` |
| B4 AC | `Gain @ 1 kHz 4.90 dB`, `Phase @ 1 kHz -179.9 °`, `−3 dB 1.78 Hz`, 141 points |
| B5 Transient | `Vin 0.0100 V`, `Vout 0.0176 V`, `Tend 0.005 s`, `inverted`, 295 points |
| B6 เปลี่ยน source | `20 mV / 500 Hz` → netlist `SIN(0 0.02 500)`, `Vin 0.0200 V`, `Vout 0.0353 V` |
| B7 Error | `RE=0` → `Simulation Error` และไม่มี badge `success` / ค่าค้าง |
| B8 UI | screenshot ก่อน/หลัง + รายเคสอยู่ใน `docs/evidence/lab04-before/` และ `docs/evidence/lab04-after/b1-b8/` |
| Repo / feature SHA | <https://github.com/B6838720/bjt-dc-bias-webapp> · `1314f8c8c1d9f56dbcb9cccf8b8bffb1d1aef96c` |

---

## 9. เอกสารเพิ่มเติม

- `docs/design-note.md` — สถาปัตยกรรมและเหตุผลการแยกชั้น (Lab 2)
- `docs/validation.md` — ข้อ 2–8: หลักฐาน Lab 2 (A1–A7); **ข้อ 9: ตาราง A1–A5 ของ Lab 03**; **ข้อ 10: คำถามปิด Lab**; **ข้อ 11: ตาราง B1–B8 ของ Lab 04**
- `docs/lab04-reflection.md` — คำตอบคำถามสั้น 5 ข้อสำหรับตรวจรายบุคคล Lab 04
- `docs/reflection.md` — คำตอบคำถามรายบุคคลในใบงาน (Lab 2)
- `docs/lab03-baseline.md` — ผล Voltage Divider ก่อนเพิ่ม 2 โหมด (baseline Lab 03)
- `docs/evidence/lab03-a5-fixed-rb0.jpeg` — หลักฐานหน้าเว็บกรณี A5 (RB=0)
- `models/ngspice/SOURCE.md` — provenance ของ BJT model ที่ใช้รันจริง
- `docs/evidence/lab04-before/` / `docs/evidence/lab04-after/` — screenshot Desktop/Mobile ก่อน–หลัง Impeccable
- `docs/evidence/lab04-after/ac-real-ngspice*.png` — Bode plot จริงจาก `.ac`
- `docs/evidence/lab04-after/tran-real-ngspice.png` — waveform จริงจาก `.tran`
- `docs/evidence/lab04-after/b1-b8/` — screenshot รายเคส B1–B8 หลังตรวจรับจริง
- `docs/superpowers/specs/2026-11-10-bjt-dc-bias-webapp-design.md` — design Lab 2 ฉบับเต็ม
- `docs/superpowers/specs/2026-11-17-lab03-three-bias-modes-design.md` — design note Lab 03
- `docs/superpowers/plans/2026-11-17-lab03-three-bias-modes.md` — plan Lab 03

---

## 10. ที่มา Commit และการทดลองทำซ้ำ

- Repository: <https://github.com/B6838720/bjt-dc-bias-webapp>
- **Feature commit ของ Lab 04:** `1314f8c8c1d9f56dbcb9cccf8b8bffb1d1aef96c`
- **Baseline Lab 03 สำหรับ regression Lab 04:** `469f1ac6c2621ca930d6e44fb2c77fd2c5bd4efb`
- ผลจริง A1–A5 อยู่ใน `docs/validation.md` ข้อ 9; ผลจริง B1–B8 อยู่ในข้อ 11

### 10.1 ทำซ้ำ Lab 04 (SPICE จริง)

```powershell
git clone https://github.com/B6838720/bjt-dc-bias-webapp.git
cd bjt-dc-bias-webapp
git checkout 1314f8c8c1d9f56dbcb9cccf8b8bffb1d1aef96c
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
$env:NGSPICE_EXECUTABLE = "C:\path\to\ngspice_con.exe"
$env:NGSPICE_MODEL_NAME  = "PN2222"
$env:NGSPICE_MODEL_FILE  = "$PWD\models\ngspice\PN2222.mod"
python -m flask --app app run --host 127.0.0.1 --port 5000
```

จากนั้นเปิด <http://127.0.0.1:5000/> แล้วทำตามลำดับ B1–B8 ใน `docs/validation.md` ข้อ 11.2
(โดยเฉพาะ B2 DC, B4 AC, B5 Transient, B6 เปลี่ยน amplitude/frequency และ B7 `RE=0`)

- `ngspice.exe` เป็น GUI และอาจ hang → ใช้ `ngspice_con.exe` เสมอ
- model `PN2222` มาจาก ngspice source repo พร้อม provenance ใน `models/ngspice/SOURCE.md` (ไม่ใช่ Starter Kit)
