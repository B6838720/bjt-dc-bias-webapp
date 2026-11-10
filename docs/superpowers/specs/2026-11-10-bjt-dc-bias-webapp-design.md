# BJT DC Bias Web App — Design Document

**ENG29 2121 · Computer Programming for Electrical Engineers · 2/2569**
**Lab 02 — First DC Bias Web App**
วันที่: 2026-11-10 · สถานะ: **อนุมัติแล้ว**

---

## 1. Intent — ทำไมต้องมีชิ้นงานนี้

นักศึกษาต้องผ่านกระบวนการพัฒนา Web Application จริง (Brainstorm → Plan → Code →
Test → Review → GitHub) เพื่อให้เห็นความแตกต่างระหว่าง Frontend (HTML/CSS),
Backend (Python), Template, Static Resource และ HTTP Request/Response

ผลลัพธ์คือเว็บที่ **คำนวณ DC Operating Point ของ BJT ด้วย Python จริง** ไม่ใช่ตัวเลข
ที่เขียนค้างไว้ใน HTML นักศึกษาต้องตรวจสอบผลกับสมการวิศวกรรมด้วยตนเอง

---

## 2. Goals

| # | เป้าหมาย | เกณฑ์ที่วัดได้ |
|---|---|---|
| G1 | เปิดเว็บได้ผ่าน local server | `http://127.0.0.1:5000/` ตอบ HTTP 200 และเห็นฟอร์ม |
| G2 | รับค่าอินพุต 7 ตัว | VCC, R1, R2, RC, RE, β, VBE |
| G3 | Backend คำนวณจริง | Python คืน VB, VE, VC, VCE, IC (+ IB, IE) พร้อมหน่วย |
| G4 | Validation | ค่าผิด (R≤0, β≤0, VCC≤0, ไม่ใช่ตัวเลข, ว่าง) → ข้อความไทย ไม่ทำให้หน้าล้ม |
| G5 | Region warning | Cutoff / Saturation ต้องมีคำเตือน ไม่รายงานว่า approximation ใช้ได้ |
| G6 | Automated tests | ≥3 tests ตรวจสมการ + ≥1 test ผ่าน Flask test client |
| G7 | Reproducible | README ทำให้ clone → install → run → test ได้ |

---

## 3. Non-goals (ขอบเขตที่ **ไม่ทำ** ใน Week 2)

- ❌ AC small-signal, Gain, Bode Plot
- ❌ Transient analysis, Signal Generator, Amplitude/Frequency controls
- ❌ DC/AC Overlay animation, Interactive schematic
- ❌ SPICE / ngspice integration หรือ solver ของตัวเอง
- ❌ Bias type อื่น (Fixed Bias, Emitter Bias) — เก็บไว้ Week 3
- ❌ FET / MOSFET
- ❌ Database, Authentication, User accounts
- ❌ JavaScript framework, build step, bundler
- ❌ Load line graph

> ขอบเขตนี้ได้รับการยืนยันจากเจ้าของงานแล้ว: **"DC Bias เท่านั้น"**

---

## 4. Constraints

- **OS:** Windows 11, PowerShell
- **Python:** 3.15.2 (default บนเครื่อง) — ถ้า dependency ไม่รองรับให้ถอยไป 3.14
- **Library:** Flask 3.x เท่านั้น, `unittest` จาก stdlib (ไม่ใช้ pytest)
- **Frontend:** Jinja2 template + CSS ธรรมดา, ไม่มี JS framework
- **Path มีช่องว่าง:** `C:\Users\B6838720\Documents\GitHub\BJT DC Bias Web App`
  → ทุกคำสั่ง shell ต้อง quote path
- **Git:** commit/push ผ่าน **GitHub Desktop** (ผู้ใช้ไม่พิมพ์ git เอง)
- **เวลา:** อยู่ในคาบ 3 ชั่วโมง ต้องจบด้วยระบบที่รันได้

---

## 5. Approaches ที่พิจารณา

| ทาง | ข้อดี | ข้อเสีย | สรุป |
|---|---|---|---|
| **A. Flask + Jinja + CSS + unittest** | ตรงกับสิ่งที่ใบงานวัด (HTTP form → route → module → template), เรียนรู้เร็ว, ไม่มี build step | ต้องจัดการ form state เอง | ✅ **เลือก** |
| B. FastAPI + HTMLResponse | ทันสมัย, auto docs | ใบงานวัด Flask route/template โดยตรง, Jinja ต้องตั้งเพิ่ม | ❌ |
| C. React SPA + JSON API | UI ลื่น | เกินเวลา, ซ่อน HTTP form flow ที่ต้องการสอน, ต้องมี Node | ❌ |
| D. Streamlit / Gradio | เขียนน้อย | ไม่แยก template/static/backend จริง ขัด learning outcome | ❌ |

**เหตุผลที่เลือก A:** เป็นทางเดียวที่แยก Frontend / Backend / Template / Static /
Tests ออกจากกันได้ชัดเจนตามเกณฑ์ A1–A7 และจบได้ในเวลาคาบ

---

## 6. Design

### 6.1 โครงสร้างไฟล์

```
BJT DC Bias Web App/
├── app.py                      # Flask app + routes เท่านั้น
├── dc_bias.py                  # สมการวิศวกรรมล้วน (ไม่ import flask)
├── templates/
│   └── index.html              # ฟอร์ม + ผลลัพธ์ (Jinja2)
├── static/
│   └── style.css
├── tests/
│   ├── test_dc_bias.py         # unit tests ของสมการ
│   └── test_web.py             # Flask test client
├── requirements.txt
├── README.md
├── AGENTS.md
├── .gitignore
└── docs/
    ├── design-note.md
    ├── validation.md
    └── reflection.md
```

**กติกาการแยกชั้น (สำคัญต่อการตรวจ):**

- `dc_bias.py` **ห้าม** import flask, ห้ามรู้จัก HTML/HTTP — รับ float คืน dict/dataclass
- `app.py` **ห้าม** มีสมการฟิสิกส์ — ทำแค่ parse request → เรียก `dc_bias` → render
- `templates/index.html` **ห้าม** มีสมการฟิสิกส์ — แสดงค่าที่ได้รับมาเท่านั้น
- แก้สมการใน `dc_bias.py` แล้ว **ไม่ต้องแก้ HTML**

### 6.2 แบบจำลอง (Forward-Active Approximation, β และ VBE คงที่)

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

**หน่วยภายใน:** Ω, V, A ทั้งหมด → แปลงเป็น mA/mA ตอนแสดงผลเท่านั้น

**ค่าอ้างอิงสำหรับตรวจ (VCC=12, R1=100k, R2=22k, RC=2.2k, RE=1k, β=100, VBE=0.70):**

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

### 6.3 กติกา Validation (ข้อความภาษาไทย)

Validation แบ่งเป็น **2 ชั้น** ตามความรับผิดชอบของแต่ละไฟล์:

**ชั้นที่ 1 — `app.py` (รู้จัก HTTP/form):** แปลง string → float

| เงื่อนไข | ผลลัพธ์ |
|---|---|
| ค่าว่าง | `"กรุณากรอก {ชื่อ field}"` |
| ไม่ใช่ตัวเลข | `"กรุณากรอก {ชื่อ field} เป็นตัวเลข"` |
| ไม่มี field ใน request | ถือเป็นค่าว่าง |

**ชั้นที่ 2 — `dc_bias.calculate()` (รับ float เท่านั้น):** ตรวจความสมเหตุสมผลทางฟิสิกส์

| เงื่อนไข | ผลลัพธ์ |
|---|---|
| `VCC ≤ 0` | `ValueError("VCC ต้องมากกว่า 0")` |
| `R1, R2, RC, RE ≤ 0` | `ValueError("ค่า {R} ต้องมากกว่า 0")` |
| `β ≤ 0` | `ValueError("β ต้องมากกว่า 0")` |
| `β < 1` (เตือน ไม่บล็อก) | warning: ค่า β ต่ำผิดปกติ |
| `VBE ≤ 0 หรือ VBE ≥ VCC` | `ValueError("VBE ต้องอยู่ระหว่าง 0 ถึง VCC")` |
| `R1 + R2 = 0` | `ValueError("R1 + R2 ต้องมากกว่า 0")` |
| ผลลัพธ์เป็น `inf` / `nan` | `ValueError("ค่าอินพุตทำให้ผลลัพธ์ไม่สมเหตุสมผล")` |

**รูปแบบ:** `dc_bias` raise `ValueError` พร้อมข้อความไทย → `app.py` จับแล้ว
ส่งกลับไปแสดงในหน้าเดิม (HTTP 200) ไม่ปล่อย 500

### 6.4 การตรวจ Operating Region

**ลำดับการตัดสิน (precedence) สำคัญ — ต้องเช็คจากบนลงล่าง:**

| ลำดับ | เงื่อนไข | Region | การแสดงผล |
|---|---|---|---|
| 1 | `VTH ≤ VBE` | **Cutoff** | ⚠️ ทรานซิสเตอร์ไม่นำกระแส สมการ Forward-Active ใช้ไม่ได้ |
| 2 | `VCE < 0.3 V` | **Saturation** | ⚠️ ไม่อยู่ใน Forward Active สมการประมาณใช้ไม่ได้ |
| 3 | อื่น ๆ | **Forward Active** | ✅ ใช้แบบจำลองได้ |

> **หมายเหตุทางวิศวกรรม:** ภายใต้สมการนี้ `VTH < VBE` ทำให้ `IB < 0` และ
> `VCE > VCC` เสมอ ดังนั้นเงื่อนไข `VCE > VCC` **ไม่ใช่ region แยก** — มันคือ
> Cutoff นั่นเอง จึงตัด region `Invalid` ออก และใช้ guard `inf/nan` ใน 6.3 แทน
> ส่วน `VCE` ติดลบมาก ๆ ถูกจัดเป็น Saturation ตามเงื่อนไขข้อ 2

> ยังคำนวณและแสดงตัวเลขทุกกรณี แต่ต้องมี Warning กำกับชัดเจน (เกณฑ์ A5)
> วิธีแสดงตัวเลขในกรณี Cutoff/Saturation กำหนดในหัวข้อ 6.6.1

### 6.5 HTTP Contract

| Method | Path | พฤติกรรม |
|---|---|---|
| `GET` | `/` | แสดงฟอร์มว่าง + ค่า default (VCC=12, R1=100, R2=22, RC=2.2, RE=1, β=100, VBE=0.70 หน่วย kΩ) |
| `POST` | `/calculate` | รับ form → เรียก `dc_bias` → render หน้าเดิมพร้อมผลลัพธ์หรือ error |
| — | อื่น ๆ | 404 ตาม default ของ Flask |

- ชื่อ field: `vcc`, `r1`, `r2`, `rc`, `re`, `beta`, `vbe`, `r_unit` (`ohm` | `kohm`)
- หน่วยตัวต้านทาน: dropdown กลาง 1 ตัวคูณทั้ง R1–RE (kΩ = ×1000)
- ไม่ใช้ session / redirect หลัง POST (POST-redirect-GET ไม่จำเป็นในขอบเขตนี้)

### 6.6 UI (หน้าจอเดียว)

```
┌──────────────────────────────────────────────┐
│  BJT DC Bias Calculator — Voltage Divider    │
├──────────────────────┬───────────────────────┤
│  อินพุต              │  ผลลัพธ์ DC Bias      │
│  VCC   [ 12    ] V   │  VB   = 1.942 V       │
│  R1    [ 100   ]     │  VE   = 1.242 V       │
│  R2    [ 22    ]     │  VC   = 9.294 V       │
│  RC    [ 2.2   ] kΩ  │  VCE  = 8.052 V       │
│  RE    [ 1     ]     │  IC   = 1.230 mA      │
│  β     [ 100   ]     │  IB   = 12.30 µA      │
│  VBE   [ 0.70  ] V   │  IE   = 1.242 mA      │
│  หน่วย [kΩ ▾]        │  ✅ Forward Active    │
│  [ คำนวณ DC Bias ]   │                       │
└──────────────────────┴───────────────────────┘
```

- Layout 2 คอลัมน์บนจอกว้าง, ยุบเป็นคอลัมน์เดียวที่ `< 720px`
- ค่าที่ผู้ใช้กรอกต้องคงอยู่ในฟอร์มหลัง POST (sticky values)
- Error แสดงเป็นกล่องแดงเหนือผลลัพธ์, Warning เป็นกล่องเหลือง/ส้ม
- ไม่ใช้ JS ใด ๆ

### 6.6.1 การแสดงผลเมื่อออกนอก Forward Active

**Cutoff (`VTH ≤ VBE`)** — แสดง **ค่าจริงทางกายภาพของวงจร** ไม่ใช่ผลจากสมการ
Forward-Active (เพราะทรานซิสเตอร์ไม่นำกระแส):

| ปริมาณ | ค่า |
|---|---|
| IB, IC, IE | `0` |
| VE | `0` |
| VB | `VTH` (แรงดัน divider ขณะไม่มีกระแสเบส) |
| VC | `VCC` (ไม่มีกระแส collector → ไม่มีแรงดันตกคร่อม RC) |
| VCE | `VCC` |

พร้อมป้าย ⚠️ ชัดเจนว่า *"ค่าที่แสดงเป็นค่าจริงของวงจรในสภาวะ Cutoff ซึ่งไม่ได้มาจาก
สมการ Forward-Active"*

**Saturation (`VCE < 0.3 V`)** — แสดงค่าที่คำนวณได้จากสมการตามปกติ พร้อมป้าย ⚠️
ว่า *"ไม่อยู่ใน Forward Active — สมการประมาณใช้ไม่ได้ ผลอาจคลาดเคลื่อน"*
(ค่า `VCE` อาจติดลบได้ ให้แสดงตามจริง ไม่ clamp)

**สัญญา (`contract`) ของ `dc_bias.calculate()`:** คืน dict ที่มี
`vth, rth, ib, ic, ie, vb, ve, vc, vce, region, model_applies, warnings`
โดย `model_applies = (region == "Forward Active")` และเมื่อ `region == "Cutoff"`
ค่าที่คืนเป็นค่าทางกายภาพตามตารางข้างบน

> เหตุผล: เกณฑ์ให้คะแนน "DC Bias ถูกหลักวงจร" — การแสดง `IC = −1.2 mA` ในสภาวะ
> Cutoff จะดูผิดในรายงาน แม้จะตรงกับสมการก็ตาม

### 6.7 Tests

**`tests/test_dc_bias.py`** (≥3 เคส):
1. ค่าอ้างอิง Lab (ข้างบน) → ตรวจ VB, VE, VC, VCE, IC ด้วย `assertAlmostEqual` (tolerance 1e-3)
2. `β` สูงขึ้น → IC สูงขึ้น (monotonic sanity)
3. Region detection: Cutoff (`VTH ≤ VBE`) และ Saturation (`VCE < 0.3`)
4. Validation: `R1 = 0` → `ValueError`, `β = 0` → `ValueError`

**`tests/test_web.py`** (≥1 เคส):
1. `GET /` → 200 และมี `name="vcc"` ใน HTML
2. `POST /calculate` ด้วยค่าอ้างอิง → 200 และ HTML มี `1.230` (IC) — พิสูจน์ว่าเป็นค่าจาก backend
3. `POST /calculate` ด้วย `r1=0` → 200 และมีข้อความ error ไทย

รันด้วย `python -m unittest discover -s tests -v`

### 6.8 Acceptance Mapping

| เกณฑ์ใบงาน | ส่วนที่รองรับ |
|---|---|
| A1 `GET /` | `app.py::index`, `templates/index.html` |
| A2 `POST /calculate` | `app.py::calculate` เรียก `dc_bias.calculate` |
| A3 Engineering Reference | `tests/test_dc_bias.py` เทียบค่าอ้างอิง |
| A4 Validation | `dc_bias` raise `ValueError` + error block ใน template |
| A5 Outside Active Region | `dc_bias.detect_region()` + warning block |
| A6 Unit + HTTP Tests | `tests/` ทั้งสองไฟล์ |
| A7 Reproducibility | `README.md`, `requirements.txt`, `.gitignore` |

---

## 7. สิ่งที่เจ้าของงานตัดสินใจเอง

- ขอบเขต **DC Bias เท่านั้น** — ไม่มี AC/Transient/Bode/Signal Gen/Overlay/SPICE
- ใช้ **GitHub Desktop** เป็นเครื่องมือ commit/push (ไม่พิมพ์ git เอง)
- อนุมัติแนวทาง A (Flask + Jinja + CSS + unittest)

---

## 8. Calls ที่ผู้เขียน design ตัดสินใจแทน (แก้ได้)

| เรื่อง | ที่เลือก | เหตุผล |
|---|---|---|
| แยก route | `GET /` + `POST /calculate` | ตรง A1/A2 และ test แยกได้ชัด |
| หน่วยตัวต้านทาน | dropdown กลาง 1 ตัว (Ω/kΩ) | ตรงข้อ "แปลง kΩ → Ω" โดยไม่รกหน้าจอ |
| ภาษา UI | ไทย + ศัพท์วิศวกรรมอังกฤษ | ตรงกับใบงาน |
| Error handling | `ValueError` + ข้อความไทย | test ง่าย, ไม่ต้องมี error class หลายตัว |
| POST แล้วไม่ redirect | render หน้าเดิม | ลดความซับซ้อน, ยังคง sticky form |
| ไม่ใช้ Blueprint | `app.py` ไฟล์เดียว | ขอบเขตเล็ก ไม่คุ้มแยก module |
| Tolerance ของ test | `places=3` (mA/V) | กัน floating point |
| Region precedence | Cutoff → Saturation → Forward Active (ตัด `Invalid` ออก) | `VCE > VCC` เป็น subset ของ Cutoff ภายใต้สมการนี้ จึงแยกไม่ได้จริง |
| ชั้น parsing | `app.py` แปลง string→float, `dc_bias` รับ float เท่านั้น | รักษากติกา "`dc_bias` ไม่รู้จัก HTTP" และแยก test ได้ชัด |
| ผลนอก Active Region | Cutoff → ค่าจริงทางกายภาพ (IC=0, VE=0, VC=VCC, VCE=VCC, VB=VTH) · Saturation → ค่าจากสมการ + warning | **เจ้าของงานเลือกเอง** — กันไม่ให้รายงานแสดง IC ติดลบ |

---

## 9. สิ่งที่เหลือให้ผู้ลงมือตัดสินใจ

- รายละเอียดหน้าตา CSS (สี, ฟอนต์, ระยะห่าง) — ขอให้อ่านง่ายและพิมพ์ดี
- ถ้อยคำของข้อความ error/warning ให้อ่านเป็นธรรมชาติ (ต้องสื่อความหมายเดิม)
- จำนวนและชื่อ test เพิ่มเติม
- เนื้อหา README/docs ที่เป็นภาษาไทย
