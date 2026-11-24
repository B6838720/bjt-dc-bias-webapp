# Lab 04 — คำตอบคำถามสั้นสำหรับตรวจรายบุคคล

อ้างอิงโค้ดจริงใน repo นี้ (`spice_engine.py`, `app.py`, `templates/index.html`) และผลที่ตรวจใน `docs/validation.md` ข้อ 11

---

## 1. โปรแกรม Python ส่งอะไรให้ ngspice และรับผลกลับมาอย่างไร?

`spice_engine.py` สร้าง **netlist ข้อความ** สำหรับ one circuit อ้างอิง แล้วเขียนลงไฟล์ `.cir` ใน `TemporaryDirectory` แยกต่อรอบ เนื้อหาที่ส่งมี:

- ส่วนประกอบจริง: `VCC`, `R1`, `R2`, `RC`, `RE`, `RL`, `Cin`, `Cout`, `Vin`
- ทรานซิสเตอร์: `Q1 collector base emitter PN2222`
- model card ที่อ่านจาก `models/ngspice/PN2222.mod` (มี provenance ใน `SOURCE.md`)
- directive ตาม analysis ที่เลือก: `.op` / `.ac DEC 20 1 10000000` / `.tran 1e-06 0.005`
- คำสั่งพิมพ์ผล: `.print ac vdb(output) vdb(input) vp(output) vp(input)` หรือ `.print tran v(input) v(output)`

จากนั้นเรียกจริงด้วย argv list (ไม่ใช้ `shell=True`) :

```text
ngspice_con.exe -b -o <run.log> <circuit.cir>
```

มี `timeout` และ working directory แยกต่อรอบ หลังจบ Python อ่าน **log ข้อความที่ ngspice เขียนผ่าน `-o`** แล้ว parse:

- `.op` → node voltage (`vcc/base/emitter/collector`) แล้ว derive `VCE = VC − VE`, `IC = (VCC − VC)/RC` พร้อมป้าย derivation
- `.ac` → join ตาราง `vdb` กับ `vp` ด้วย frequency, คำนวณ `Gain(dB)=vdb(out)−vdb(in)`, แปลง `vp` จาก radian เป็นองศา, หา −3 dB ด้วย interpolation ใน log(f)
- `.tran` → ตัดคอลัมน์ `Index` ออก, อ่าน `time / v(input) / v(output)`, หา peak และ correlation เพื่อบอก inverted/non-inverted

ผลถูกรวมเป็น dict `values`, `series`, `warnings`, `derived`, `netlist`, `log_excerpt` ส่งไป `app.py` เพื่อ render **ไม่ได้อ่าน raw binary** และไม่ใช้ mock เป็นหลักฐานผลจริง

---

## 2. เหตุใดกราฟ `.ac` และ `.tran` จึงไม่ใช่สิ่งเดียวกัน?

เพราะทั้งสองตอบคำถามคนละแบบแม้ใช้วงจรเดียวกัน:

| | `.ac` | `.tran` |
|---|---|---|
| โดเมน | ความถี่ (Frequency, Hz) | เวลา (Time, s) |
| ลักษณะ | small-signal linearization รอบ DC operating point | แก้สมการไม่เชิงเส้นตามเวลาจริง พร้อม capacitor charge/discharge |
| แกน/ค่าที่อ่าน | Gain (dB) และ Phase (°) จาก `vdb/vp` | `v(input)`, `v(output)` ที่แต่ละ instant |
| สิ่งที่เห็น | Bode plot, gain @ 1 kHz, −3 dB point | waveform, peak, ทิศทางเฟส/phase relation, startup transient |

`.ac` บอกว่าวงจรขยายเท่าไหร่ที่ความถี่หนึ่ง ๆ แต่ไม่บอกว่าสัญญาณใช้เวลาเท่าไหร่ถึงจะเสถียร `.tran` บอกพฤติกรรมตามเวลา (เช่น inversion, charging) แต่ไม่ได้ให้ Bode plot โดยตรง ต้องทำ FFT เพิ่ม

ในรันจริงของโปรเจกต์นี้:

- `.ac` → `Gain @ 1 kHz = 4.90 dB`, `Phase @ 1 kHz = -179.9 °`, `−3 dB ≈ 1.78 Hz`
- `.tran` ที่ 10 mV / 1 kHz → `Vin peak 0.0100 V`, `Vout peak 0.0176 V`, `Phase relation inverted`

คำว่า “inverted” ใน `.tran` มาจาก correlation ของ waveform **ไม่ใช่**การวัดเฟสเชิงความถี่แบบ `.ac` จึงเขียนคำอธิบายนี้ไว้ใต้กราฟด้วย

---

## 3. ถ้าเปลี่ยน Amplitude แต่กราฟไม่เปลี่ยน คุณจะตรวจข้อมูลตรงไหนก่อน?

ไล่ตามลำดับข้อมูลตั้งแต่ฟอร์มไปถึงกราฟ:

1. **POST body จริง** — ใช้ `network.list`/`network.get` ดู `/simulate` ว่ามี `sim_amp=20` หรือยังค้าง `10` อยู่
2. **ค่าใน input หลัง render** — `evaluate` อ่าน `document.querySelector('[name="sim_amp"]').value` ว่าตามที่พิมพ์หรือไม่
3. **บรรทัด source ใน netlist** — เปิด `<details> Netlist ที่ส่งให้ ngspice` ต้องเห็น
   `Vin input 0 DC 0 AC 0.02 SIN(0 0.02 500)` หลังเปลี่ยนจาก 10 mV/1 kHz เป็น 20 mV/500 Hz  
   ถ้ายังเป็น `0.01 ... 1000` แปลว่าแปลงหน่วย mV → V ผิด (`app.py` ต้องหาร 1000)
4. **log ที่ ngspice พิมพ์** — ดู `<details> ngspice log excerpt` ว่ามีแถว waveform เปลี่ยนจริง
5. **series → polyline** — ตรวจว่า chart ใช้ `sim_result.series` ที่ parse ใหม่ ไม่ใช่ array คงที่ใน template; ดู `points` ของ `.line-vin` ว่าต่างจากรอบก่อน

ใน B6 ที่ตรวจจริง เปลี่ยน `Amplitude=20 mV, Frequency=500 Hz` แล้ว netlist เปลี่ยนเป็น `AC 0.02 SIN(0 0.02 500)` และ `Vin peak` เปลี่ยน `0.0100 → 0.0200 V`, `Vout peak` เปลี่ยน `0.0176 → 0.0353 V` จึงยืนยันว่าไม่ใช่กราฟค้าง

---

## 4. Impeccable เปลี่ยนอะไรได้ และไม่ควรเปลี่ยนอะไร?

**เปลี่ยนได้ (UI/UX):**
- layout, spacing, typography, color/contrast, responsive breakpoint
- ความอ่านง่ายของฟอร์ม, badge status, ตารางผล, legend และ chart styling
- accessibility และ perceived performance (เช่น ลดการ render ที่ไม่จำเป็น)

**ไม่ควรเปลี่ยน (physics/data/integrity):**
- netlist, directive `.op/.ac/.tran`, model card, provenance
- การแปลงหน่วย kΩ/µF/mV/µs/ms → SI
- สมการ derive `IC`, `VCE`, gain, phase, cutoff, correlation
- กติกา status/error: engine fail ต้องแสดง `Simulation Error` และไม่โชว์ success/c่าค้าง
- ผล Analytical กับ SPICE ต้องแยกป้ายเสมอ
- ห้ามใส่ค่าหรือ grid ที่เป็น mock data ลงใน HTML/CSS

ในงานนี้ Impeccable ใช้ปรับเฉพาะ `static/style.css` (และโครงสร้างแสดงผลเล็กน้อยใน `templates/index.html`) ผล detector รอบสุดท้ายเป็น `[]` และมี screenshot ก่อน/หลังที่ `docs/evidence/lab04-before/` กับ `lab04-after/`

---

## 5. คุณรู้ได้อย่างไรว่า Bode Plot เป็นผลจำลองจริง ไม่ใช่ Mock Data?

ตรวจได้จากร่องรอย End-to-End 5 ชั้น:

1. **มี engine จริง** — ใช้ `ngspice-41` console (`ngspice_con.exe`) เรียกด้วย `-b -o` และคำสั่งปรากฏใน `spice_engine.py` ไม่ใช่ฟังก์ชันสุ่มค่า
2. **มี netlist จริงในหน้าเว็บ** — `<details> Netlist ที่ส่งให้ ngspice` แสดง `.ac DEC 20 1 10000000` และ `.print ac vdb(output) vdb(input) vp(output) vp(input)` พร้อม model `PN2222`
3. **มี log ดิบจริง** — `<details> ngspice log excerpt` แสดงตารางเช่น
   `60  1.000000e+03  -3.51007e+01  -4.00000e+01` (vdb) และ
   `60  1.000000e+03  -3.13938e+00  0.000000e+00` (vp) ซึ่งเป็นรูปแบบที่ ngspice batch พิมพ์จริง
4. **กราฟมาจาก series ที่ parse ได้** — polyline มี 141 จุดจาก `series` ที่ join ด้วย frequency ไม่มีตัวเลขฝังใน template; gain @ 1 kHz `4.90 dB` ตรงกับ `-35.1007 − (−40)`
5. **ตรวจซ้ำและ error gating** — เปลี่ยน RE/amplitude/frequency แล้วค่ากราฟเปลี่ยนจริง (B3, B6); ใส่ `RE=0` แล้วไม่มี badge `success` และไม่มีค่าค้าง (B7)

unit test ที่ใช้ fake runner เป็นเพียงการพิสูจน์โครง/parser **ไม่ใช่หลักฐานผลจำลอง** หลักฐานผลจริงคือ browser run + log excerpt + screenshot ใน `docs/validation.md` ข้อ 11 และ `docs/evidence/lab04-after/b1-b8/b4-ac-spice.png`
