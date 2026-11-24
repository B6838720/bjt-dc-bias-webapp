# AGENTS.md — กติกาสำหรับ AI/ผู้พัฒนา

ไฟล์นี้อธิบายกติกาที่ต้องรักษาไว้เมื่อแก้โค้ดโปรเจกต์ **BJT DC Bias Web App**
อ่าน `README.md` และ `docs/design-note.md` ก่อนเริ่มงาน

---

## 1. ขอบเขตปัจจุบัน (Lab 04)

โปรเจกต์นี้คือ **Lab 04 — BJT Amplifier Simulator v1** (ต่อยอดจาก Lab 03)

- ✅ คง DC Bias 3 แบบ `divider / fixed / emitter` และผล A1–A5 ไว้เหมือนเดิม
- ✅ เพิ่มวงจร CE Voltage Divider อ้างอิง **หนึ่งวงจร** สำหรับจำลองจริง
- ✅ เชื่อม `ngspice` ผ่าน `spice_engine.py` เพื่อรัน `.op`, `.ac`, `.tran`
- ✅ ผลทุกชุดต้องมี engine status, model, unit และ provenance ว่ามาจาก SPICE หรือ Analytical
- ✅ Impeccable ปรับเฉพาะไฟล์ UI; Playwright MCP ตรวจ B1–B8 จาก browser จริง
- ❌ ห้ามลบ/เปลี่ยน signature ของ `dc_bias.calculate()`, `calculate_fixed()`, `calculate_emitter()`
- ❌ ห้ามทำ circuit editor อิสระ, FET, deploy ภายนอก, หรือใส่กราฟ/ค่าสำเร็จรูปแทนผลรันจริง
- ❌ ห้ามเดาค่า BJT model — ใช้ Starter Kit ถ้ามี; กรณีนี้ใช้โมเดลจาก ngspice source repo พร้อม provenance ตามที่ผู้ใช้เลือกข้อ 2
- ถ้าจะเพิ่ม dependency ใหม่ ต้องอัปเดต `requirements.txt` และ `README.md` ด้วย

---

## 2. การแยกความรับผิดชอบ (สำคัญที่สุด)

| ไฟล์ | ทำได้ | ห้ามทำ |
|---|---|---|
| `dc_bias.py` | สมการ Analytical DC, validation, region detection, warning | **ห้าม import `flask`**, ห้ามรู้จัก HTTP/form/HTML |
| `spice_engine.py` | สร้าง netlist, เรียก ngspice, parse ผล, แจ้ง error | **ห้าม import `flask`**, ห้าม CREATE mock trace/current/gain |
| `app.py` | routes, parsing string→float, dispatch ไป engine/reference, formatting, template context | **ห้ามมีสมการฟิสิกส์หรือ netlist** |
| `templates/index.html` | แสดงผล, ฟอร์ม, loop, if, SVG path ที่สร้างจากข้อมูลจริง | **ห้ามมีสมการฟิสิกส์**, ห้ามคำนวณค่าทางวิศวกรรม |
| `static/style.css` | การจัดหน้า, responsive | ห้ามใส่ logic |
| `tests/` | unit + HTTP tests (อาจใช้ fake runner แทน ngspice จริง) | ห้ามใส่ production logic |

**เหตุผล:** ถ้าย้ายสมการหรือ netlist ไป HTML/`app.py` จะทดสอบไม่ได้และผิดเกณฑ์ใบงาน  
**Lab 04 เพิ่ม:** `app.py` dispatch ได้ แต่ต้องแยกป้ายผล `SPICE (ngspice)` กับ `Analytical (Lab 3)` เสมอ

---

## 3. สัญญาของ `dc_bias.calculate()`

```python
calculate(vcc, r1, r2, rc, re, beta, vbe) -> dict
```

- รับ **float เท่านั้น** (หน่วย SI: Ω, V, A) — การแปลง string เป็นหน้าที่ `app.py`
- คืน dict ที่มีคีย์ครบ:
  `vth, rth, ib, ic, ie, vb, ve, vc, vce, region, model_applies, warnings`
- raise `ValueError` พร้อมข้อความ **ภาษาไทย** เมื่ออินพุตผิดเชิงฟิสิกส์
- **ห้าม** เปลี่ยนชื่อคีย์หรือ signature โดยไม่แก้ test และ template พร้อมกัน

### Region

- ค่าคงที่: `REGION_ACTIVE = "forward_active"`, `REGION_CUTOFF = "cutoff"`,
  `REGION_SATURATION = "saturation"`
- ลำดับการตัดสิน: **Cutoff → Saturation → Forward Active**
- สภาวะ Cutoff ต้องคืน **ค่าจริงทางกายภาพ** (`ib = ic = ie = 0`, `ve = 0`,
  `vb = vth`, `vc = vcc`, `vce = vcc`) ไม่ใช่ค่าติดลบจากสมการ

---

## 4. กติกา TDD (บังคับ)

ทุก feature หรือ bugfix ต้องทำตามลำดับ:

1. เขียน test ที่ fail ก่อน
2. รัน `python -m unittest discover -s tests -v` → เห็น fail จริง
3. เขียนโค้ดขั้นต่ำให้ผ่าน
4. รันอีกครั้ง → ผ่านทั้งหมด
5. commit

**ห้ามเขียน production code ก่อนมี failing test**

---

## 5. ก่อน commit ทุกครั้ง

```powershell
python -m unittest discover -s tests -v
```

ต้องได้อย่างน้อย **29 tests, OK** (15 unit + 14 HTTP จาก Lab 03; ต้องผ่านก่อนเพิ่มงาน Lab 04)

ตรวจว่าไม่มีไฟล์ขยะติดไป:

```powershell
git status --short
```

- ❌ ห้าม commit `.venv/`, `__pycache__/`, `.env`, `.superpowers/`
- ✅ ไฟล์ที่ควรอยู่ใน commit: `.py`, `.html`, `.css`, `.md`, `requirements.txt`, `.gitignore`

---

## 6. ภาษาและรูปแบบ

- ข้อความ UI, error, warning เป็น **ภาษาไทย** (ศัพท์วิศวกรรมใช้ภาษาอังกฤษได้)
- ตัวเลขบนหน้าจอ: แรงดัน 3 ตำแหน่งทศนิยม (`1.942 V`), กระแส mA 3 ตำแหน่ง (`1.230 mA`)
- ใช้ `unittest` เท่านั้น (ไม่ใช้ pytest) เพื่อให้ตรงกับใบงาน
- รักษา style เดิมของไฟล์: ฟังก์ชันสั้น, ไม่มี dependency ซ่อน

---

## 7. กติกาเพิ่มเติมสำหรับผลจำลอง Lab 04

- ต้องเรียก `ngspice` ด้วย `subprocess.run([...])`, มี `timeout`, ไม่ใช้ `shell=True`
- ต้องใช้ working directory แยกต่อรอบ (เช่น `TemporaryDirectory`) และเก็บ netlist/log ของรอบนั้น
- ถ้า engine ไม่พบ, run fail, log ว่าง, หรือ parse ไม่ได้ → คืน error ห้ามโชว์ result เก่าหรือ status Success
- ห้าม hard-code gain, cutoff frequency, waveform หรือตัวเลข DC ลงใน template/code แล้วอ้างว่าเป็นผล ngspice
- ถ้าหา -3 dB ไม่เจอในช่วง sweep ให้ระบุ `not determined in sweep range`
- ค่าที่คำนวณต่อจาก node voltage ของ SPICE (เช่น IC จาก `(VCC-VC)/RC`) ต้องบอกวิธีderive ให้ชัด
- ผล `dc_bias.py` เป็น analytical reference อย่างเดียว ห้ามรวมกับผล SPICE เป็นตารางเดียวแบบไม่มีป้ายกำกับ

---

## 8. เอกสารที่ต้องอัปเดตเมื่อพฤติกรรมเปลี่ยน

- `README.md` — ถ้าเปลี่ยนวิธีติดตั้ง/รัน หรือสมการ
- `docs/validation.md` — ถ้าเปลี่ยนค่าอ้างอิงหรือผล test
- `docs/superpowers/specs/` — เฉพาะเมื่อเปลี่ยน design (ต้องขออนุมัติเจ้าของงานก่อน)
