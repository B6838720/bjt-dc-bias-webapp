# Reflection — คำถามรายบุคคล (Lab 02)

> ตอบคำถามท้ายใบงาน 4 ข้อ โดยอ้างอิงโค้ดจริงในโปรเจกต์นี้

---

## 1. ทำไมเปิด `templates/index.html` ตรง ๆ ด้วย Browser จึงไม่เท่ากับการรัน Flask

เพราะ `index.html` เป็น **Jinja2 template** ไม่ใช่ HTML สมบูรณ์ในตัวเอง
ข้างในมี syntax ที่ Browser ไม่รู้จัก เช่น

```jinja
{{ form.vcc }}
{% if result %}
{{ result.vb|voltage }}
```

ถ้าเปิดด้วย `file://`:

- `{{ ... }}` จะแสดงเป็นข้อความดิบ ไม่ถูกแทนค่าด้วยตัวเลขจริง
- `{% if %}` จะไม่ทำงาน ผลลัพธ์จึงไม่ถูกซ่อน/แสดงตามเงื่อนไข
- `url_for('static', filename='style.css')` ไม่ถูกแปลงเป็น path จริง → CSS ไม่โหลด
- ไม่มี Python รันอยู่เลย → **ไม่มีการคำนวณใด ๆ**

การรัน Flask (`python -m flask --app app run`) ทำให้เกิดลำดับนี้:
Browser → HTTP request → Flask route → `render_template()` → Jinja2 แทนค่า
ด้วยข้อมูลจริงจาก `dc_bias.calculate()` → ส่ง HTML ที่สมบูรณ์กลับไป

**สรุป:** `index.html` เป็น "แม่แบบ" ส่วน Flask + Jinja2 เป็น "เครื่องพิมพ์"
ที่เติมข้อมูลและสร้าง HTML จริงให้ Browser

---

## 2. ฟอร์มส่งข้อมูลไปยัง Python อย่างไร

1. ฟอร์มใน `templates/index.html` ประกาศ:

   ```html
   <form method="post" action="/calculate">
   ```

2. เมื่อผู้ใช้กด **คำนวณ DC Bias** Browser รวมค่าทุกช่องเป็น
   `application/x-www-form-urlencoded` แล้วส่ง **HTTP POST** ไปที่ `/calculate`
   เช่น

   ```
   vcc=12&r1=100&r2=22&rc=2.2&re=1&beta=100&vbe=0.70&r_unit=kohm
   ```

3. Flask route ใน `app.py` รับข้อมูล:

   ```python
   @app.post("/calculate")
   def calculate_route():
       form = {field: request.form.get(field, "") for field in FIELD_LABELS}
   ```

4. `_parse_form()` แปลง string → float และคูณหน่วย kΩ → Ω

5. เรียก `dc_bias.calculate(**values)` → ได้ dict ผลลัพธ์

6. `render_template("index.html", form=form, result=result, error=None)`
   ส่งค่ากลับไปแสดงบนหน้าเดิม

**จุดสำคัญ:** การคำนวณเกิดขึ้นที่ **ฝั่ง Server (Python)** ทั้งหมด
Browser ทำหน้าที่เพียงส่งค่าและแสดงผล ไม่มี JavaScript คำนวณ

---

## 3. ถ้าแก้สมการใน `dc_bias.py` ต้องแก้ HTML ด้วยไหม

**ไม่ต้อง** — นี่คือประโยชน์หลักของการแยกชั้น

- `dc_bias.py` รับผิดชอบ **ตัวเลข** (สมการ, validation, region)
- `templates/index.html` รับผิดชอบ **การแสดงผล** ผ่านชื่อคีย์ เช่น
  `{{ result.vb|voltage }}`, `{{ result.ic|current }}`

ถ้าแก้แค่ **สูตรภายใน** (เช่น เปลี่ยนวิธีคำนวณ `IB`) แต่ยังคืนคีย์เดิม
(`vth, rth, ib, ic, ie, vb, ve, vc, vce, region, model_applies, warnings`)
HTML จะแสดงค่าใหม่ทันทีโดยไม่ต้องแก้ไข

ต้องแก้ HTML เฉพาะเมื่อ:

- เพิ่ม/เปลี่ยน **ชื่อคีย์** ที่จะแสดง (เช่น เพิ่ม `power_dissipation`)
- เปลี่ยน **หน่วยหรือรูปแบบ** การแสดงผล
- เปลี่ยน **โครงหน้า** (เพิ่มการ์ด, เปลี่ยนป้าย region)

ต้องแก้ test ด้วยถ้าเปลี่ยนพฤติกรรม (เช่น ค่าอ้างอิงหรือเงื่อนไข region)
— แต่ไม่ใช่เพราะ HTML

---

## 4. ทำไมผลที่ออกนอก Operating Region ต้องมี Warning

เพราะสมการที่ใช้เป็น **Forward-Active approximation** ซึ่งมีสมมติฐานว่า
ทรานซิสเตอร์อยู่ในสภาวะนำกระแสปกติ (`VBE ≈ 0.7 V`, `IC = β·IB`, `VCE > 0.3 V`)
ถ้าผลลัพธ์ออกนอกสภาวะนั้น สมการยังคำนวณเลขได้ แต่ **ความหมายทางวิศวกรรมหายไป**

| Region | เกิดอะไรขึ้น | ถ้าไม่มี warning |
|---|---|---|
| **Cutoff** (`VTH ≤ VBE`) | ทรานซิสเตอร์ไม่นำกระแส สมการให้ `IB/IC/IE` ติดลบ | ผู้ใช้อาจเข้าใจว่ามีกระแสไหลย้อน ซึ่งเป็นไปไม่ได้ |
| **Saturation** (`VCE < 0.3 V`) | ทรานซิสเตอร์อิ่มตัว สมการ Forward-Active ใช้ไม่ได้ | ผู้ใช้อาจนำค่า `IC`, `VCE` ไปออกแบบต่อทั้งที่คลาดเคลื่อนมาก |

ในโปรเจกต์นี้จัดการเพิ่มเติม:

- **Cutoff** → แสดง **ค่าจริงทางกายภาพ** (`IC = IE = 0`, `VE = 0`,
  `VC = VCC`, `VCE = VCC`, `VB = VTH`) พร้อม warning ว่าค่าไม่ได้มาจาก
  สมการ Forward-Active
- **Saturation** → แสดงค่าจากสมการตามจริง (อาจติดลบ) พร้อม warning ว่า
  ผลอาจคลาดเคลื่อน

**สรุป:** Warning ไม่ใช่การทำให้โปรแกรม "ดูดี" แต่เป็นการป้องกันการตีความ
ผลลัพธ์ผิด ซึ่งเป็นอันตรายมากกว่าการที่โปรแกรมไม่แสดงอะไรเลย
(เกณฑ์ A5 ในใบงานกำหนดให้ต้องมี warning ในกรณีนอก active region)
