@echo off
chcp 65001 >nul
rem ดับเบิลคลิกไฟล์นี้เพื่อ commit + push ขึ้น GitHub (ต้องทำขั้นตอนครั้งแรกใน GITHUB.md ก่อน)
set /p MSG=ข้อความบอกว่าแก้อะไร (กด Enter = update): 
if "%MSG%"=="" set MSG=update
git add .
git commit -m "%MSG%"
git push
pause
