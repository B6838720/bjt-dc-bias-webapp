# AGENTS.md — กติกาสำหรับ AI/ผู้พัฒนา

ไฟล์นี้อธิบายกติกาที่ต้องรักษาไว้เมื่อแก้โค้ดโปรเจกต์ **BJT DC Bias Web App**
อ่าน `README.md` และ `docs/design-note.md` ก่อนเริ่มงาน

---

## 1. ขอบเขต (ห้ามขยายเอง)

โปรเจกต์นี้เป็น **Lab 02 — DC Bias เท่านั้น**

- ✅ คำนวณ `VTH, RTH, IB, IC, IE, VB, VE, VC, VCE` และตรวจ region
- ❌ **ห้ามเพิ่ม** AC analysis, Bode plot, Transient simulation, Signal Generator,
  Overlay animation, SPICE solver หรือ dependency ใหม่ที่ไม่ได้อยู่ใน `requirements.txt`
- ถ้าผู้ใช้ขอ feature นอกขอบเขต ให้ถามยืนยันก่อนเสมอ

---

## 2. การแยกความรับผิดชอบ (สำคัญที่สุด)

| ไฟล์ | ทำได้ | ห้ามทำ |
|---|---|---|
| `dc_bias.py` | สมการ, validation, region detection, warning | **ห้าม import `flask`**, ห้ามรู้จัก HTTP/form/HTML |
| `app.py` | routes, parsing string→float, formatting, template context | **ห้ามมีสมการฟิสิกส์** |
| `templates/index.html` | แสดงผล, ฟอร์ม, loop, if | **ห้ามมีสมการฟิสิกส์**, ห้ามคำนวณค่าทางวิศวกรรม |
| `static/style.css` | การจัดหน้า, responsive | ห้ามใส่ logic |
| `tests/` | unit + HTTP tests | ห้ามใส่ production logic |

**เหตุผล:** ถ้าย้ายสมการไป HTML หรือ `app.py` จะทดสอบไม่ได้และผิดเกณฑ์ใบงาน

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

ต้องได้ **15 tests, OK** (หรือมากกว่า ถ้าเพิ่ม test ใหม่)

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

## 7. เอกสารที่ต้องอัปเดตเมื่อพฤติกรรมเปลี่ยน

- `README.md` — ถ้าเปลี่ยนวิธีติดตั้ง/รัน หรือสมการ
- `docs/validation.md` — ถ้าเปลี่ยนค่าอ้างอิงหรือผล test
- `docs/superpowers/specs/` — เฉพาะเมื่อเปลี่ยน design (ต้องขออนุมัติเจ้าของงานก่อน)
