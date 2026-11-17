# Lab 03 — Baseline ก่อนแก้โปรแกรม (Voltage Divider Bias)

> บันทึกเมื่อ 2026-11-17 ตามขั้นตอนที่ 1 ของใบงาน Lab 03
> **ยังไม่มีการแก้ไฟล์ใด ๆ** — ค่าในเอกสารนี้คือผลจากโค้ด Lab 02 เดิม

---

## 1. สภาพแวดล้อมก่อนรัน

| รายการ | ค่า |
|---|---|
| โปรเจกต์ | `C:\Users\B6838720\Documents\GitHub\BJT DC Bias Web App` |
| `git status --short --branch` | `## main...origin/main` (สะอาด ไม่มีไฟล์แก้ไข) |
| Python (venv) | 3.15.2 (`.venv\Scripts\python.exe`) |
| Flask | 3.1.3 |
| คำสั่งรัน | `.venv\Scripts\python.exe -m flask --app app run --debug` |
| URL | `http://127.0.0.1:5000/` |
| ชื่อหน้าเว็บที่เห็น | `BJT DC Bias Calculator — Voltage Divider` |
| วิธีตรวจ | **OpenCode Browser** (`browser_tabs.open`, `browser_snapshot`, `browser_click`) |

---

## 2. อินพุตที่กรอก (กรณี A1 ของ Lab 03 / ค่าอ้างอิงเดิมของ Lab 02)

หน่วยตัวต้านทานที่เลือก: **kΩ** (ฟอร์มแปลงเป็น Ω ใน `app.py`)

| ช่อง | ค่า |
|---|---|
| VCC (V) | 12 |
| R1 (VCC → Base) (kΩ) | 100 |
| R2 (Base → GND) (kΩ) | 22 |
| RC (VCC → Collector) (kΩ) | 2.2 |
| RE (Emitter → GND) (kΩ) | 1 |
| β (hFE) | 100 |
| VBE (V) | 0.70 |

---

## 3. ผลที่เห็นจริงบนหน้าเว็บก่อนแก้

ป้ายสถานะ: **✅ Forward Active — ใช้แบบจำลองได้**

| ปริมาณ | ผลที่แสดง | หน่วย |
|---|---|---|
| VB | 1.942 | V |
| VE | 1.242 | V |
| VC | 9.294 | V |
| VCE | 8.052 | V |
| IC | 1.230 | mA |
| IB | 12.30 | µA |
| IE | 1.242 | mA |
| VTH | 2.164 | V |
| RTH | 18,033 | Ω |

ผลนี้ตรงกับตารางค่าอ้างอิงใน `README.md` ข้อ 1 และ `docs/validation.md` ข้อ 2 ทุกประการ
→ ใช้เป็น **ค่าฐาน (baseline)** สำหรับเทียบหลังเพิ่ม Fixed Bias / Emitter Bias ใน A1

---

## 4. หมายเหตุ

- ไม่ได้รัน `unittest` ในขั้นตอนนี้ (ใบงาน Lab 03 ตรวจผ่าน Browser) แต่สถานะ Git สะอาดก่อนเริ่ม
- ภาพหน้าจอ (screenshot) ไม่สามารถเก็บได้ในรอบนี้เพราะหน้าต่าง Desktop ไม่ได้อยู่ในโหมดมองเห็น
  หลักฐานที่ใช้จึงเป็น **accessibility snapshot** ของหน้าเว็บหลังกดปุ่ม `คำนวณ DC Bias`
- ไฟล์ภาพที่แนบมาในแชท (`image.png`) ไม่สามารถอ่านเนื้อหาได้จากโมเดลนี้ → ยังไม่สามารถสรุป
  "การสาธิตเชื่อม Playwright MCP สั้น ๆ" ที่อยู่ในภาพได้ ต้องให้เจ้าของงานอธิบายหรือพิมพ์ข้อความมาให้
- ในโปรเจกต์นี้ยังไม่มี `opencode.json` / `opencode.jsonc` และเซสชันนี้ไม่พบ MCP resource ที่ชื่อ `playwright`
  → ยังไม่สามารถยืนยันการเชื่อม Playwright MCP ได้ในขั้นตอนที่ 1 (จะทำในขั้นตอนที่ 5 ตามใบงาน)
