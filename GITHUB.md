# วิธีเอาโปรเจกต์ขึ้น GitHub

## ทำครั้งแรกครั้งเดียว
1. สมัครบัญชีที่ https://github.com
2. ติดตั้ง Git: https://git-scm.com (กด Next ไปเรื่อย ๆ)
3. บน GitHub กด **New repository** ตั้งชื่อ `dracolearn` (เลือก Private ถ้าไม่อยากให้คนอื่นเห็น) **ไม่ต้องติ๊ก** Add README
4. เปิด Terminal ในโฟลเดอร์เกมนี้ แล้วรันทีละบรรทัด:

```bash
git config --global user.name "ชื่อคุณ"
git config --global user.email "อีเมลที่สมัคร GitHub"
git init
git add .
git commit -m "first version"
git branch -M main
git remote add origin https://github.com/ชื่อผู้ใช้/dracolearn.git
git push -u origin main
```

(ครั้งแรกจะมีหน้าต่างให้ล็อกอิน GitHub)

## ครั้งต่อไปที่แก้โค้ด
ดับเบิลคลิก `push_to_github.bat` หรือพิมพ์เอง:

```bash
git add .
git commit -m "เพิ่มอะไรบ้าง"
git push
```

## ดาวน์โหลดโปรเจกต์ไปเครื่องอื่น
```bash
git clone https://github.com/ชื่อผู้ใช้/dracolearn.git
pip install -r requirements.txt
python main.py
```

## หมายเหตุ
- `.gitignore` กันไม่ให้ `save_data.json` (ไฟล์เซฟ/บัญชีผู้เล่น) ขึ้น GitHub
- ถ้าเผลอ push ไฟล์เซฟขึ้นไปแล้ว ให้เปลี่ยนรหัสผ่านผู้เล่นเหล่านั้น
