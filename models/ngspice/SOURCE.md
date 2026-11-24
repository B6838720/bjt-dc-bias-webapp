# BJT model provenance — PN2222.mod

ไฟล์ `PN2222.mod` ในโฟลเดอร์นี้ **คัดลอกมาจาก ngspice source repository โดยตรง** ไม่ได้เขียนหรือเดาค่าขึ้นมาเอง

| รายการ | ค่า |
|---|---|
| โมเดล | `.model PN2222 NPN(...)` |
| ต้นทาง | ngspice GitHub repository |
| path ต้นทาง | `examples/tclspice/tcl-testbench1/PN2222.mod` |
| commit ของ repo ต้นทาง | `032b1c32c4dbad45ff132bcfac1dbecadbd8abb0` |
| blob sha | `d683d374e82704e64fc10884941de711e8bdfb3c` |
| raw URL | https://raw.githubusercontent.com/ngspice/ngspice/032b1c32c4dbad45ff132bcfac1dbecadbd8abb0/examples/tclspice/tcl-testbench1/PN2222.mod |
| วันที่คัดลอก | 2026-11-24 |
| ขนาด | 353 bytes |

หมายเหตุของ model card ต้นทางระบุว่าเป็น Fairchild `PN2222`, `pid=19`, `case=TO92`

**สำคัญ:** โมเดลนี้มาจากตัวอย่างที่จัดอยู่ใน ngspice source tree ตามที่ผู้ใช้งานอนุญาตให้ใช้ "ข้อ 2: model จาก ngspice library" ไม่ใช่ Starter Kit ที่อาจารย์แจก และไม่ได้แทนที่ข้อกำหนดเดิมของใบงานโดยอัตโนมัติ ต้องระบุ provenance นี้ใน `docs/validation.md` ทุกครั้งที่รายงานผล B2–B6
