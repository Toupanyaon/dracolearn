"""
i18n.py
-------
แปลข้อความในเกมตาม "ภาษาของเมนู" (content.UI_LANG): คอร์สเรียนอังกฤษ -> เมนูไทย (ข้อความต้นฉบับ), คอร์สเรียนไทย -> เมนูอังกฤษ

วิธีทำงาน (ไม่ต้องแก้ทุกจุดที่วาดข้อความ): ฟอนต์ทุกตัวจาก config.get_font() ถูกห่อด้วย TFont ซึ่งแปลข้อความผ่าน tr() ก่อน
render()/size() เสมอ ดังนั้นปุ่ม/ป้าย/toast ทุกอย่างที่วาดด้วยฟอนต์ของเกมจะถูกแปลอัตโนมัติ
 - TEXT     : ข้อความตายตัว ไทย -> อังกฤษ
 - PATTERNS : ข้อความที่มีตัวเลข/ชื่อแทรก ใช้ {} เป็นช่องว่าง เช่น "ข้อ {}/{}" -> "Question {}/{}"
 - ไม่มีคำแปล = แสดงข้อความเดิม (ห้ามพัง) ดังนั้นเนื้อหาโจทย์ภาษาไทยของคอร์สไทยผ่านไปตามเดิม
   (มีเทสต์ตรวจว่าเนื้อหาคอร์สไม่ไปชนกับคีย์ในตารางนี้)
"""

import re

from . import content

# --------------------------- ข้อความตายตัว (ไทย -> อังกฤษ) ---------------------------
TEXT = {
    # ทั่วไป
    "< กลับ": "< Back", "ปิด": "Close", "ยืนยัน": "Confirm", "ยกเลิก": "Cancel", "บันทึก": "Save",
    "ออก": "Exit", "ผู้เล่น": "Player", "ตั้งค่า": "Settings", "โปรไฟล์": "Profile",
    # หน้าแรก / ล็อกอิน
    "เริ่มผจญภัย!": "Start the adventure!", "กรุณาพิมพ์ชื่อก่อนเริ่มเรียนนะ!": "Please type your name first!",
    "เรียนภาษาอังกฤษไปกับเบลซ มังกรน้อยผู้ใจดี": "Learn languages with Blaze, the kind little dragon",
    "ชื่อเดิม+รหัสเดิม = เล่นต่อ  /  ชื่อใหม่+ตั้งรหัสใหม่ = เริ่มโปรไฟล์ใหม่":
        "Same name + same password = continue  /  New name + new password = new player",
    "ชื่อผู้เล่น": "Player name", "รหัสผ่าน": "Password", "พิมพ์ชื่อของคุณที่นี่...": "Type your name here...",
    "พิมพ์รหัสผ่านที่นี่...": "Type your password here...",
    "ชื่อนี้มีรหัสผ่านแล้ว กรุณาใส่รหัสผ่านด้วย": "This name already has a password. Please enter it.",
    "รหัสผ่านไม่ถูกต้อง กรุณาลองใหม่": "Wrong password. Please try again.",
    # แดชบอร์ด
    "ไปเส้นทางเรียน": "Learning path", "เรียนต่อบทถัดไป": "Next lesson", "โหมด Challenger": "Challenger mode",
    "อันดับ": "Ranking", "แต่งตัวมาสคอต": "Dress up Blaze", "สถิติการเรียน": "Learning stats",
    "ภารกิจวันนี้": "Today's quests", "ตอบถูก 5 ข้อ": "Answer 5 correctly", "เรียนจบ 1 บท": "Finish 1 lesson",
    "ตารางคะแนน": "Leaderboard", "ยังไม่มีผู้เล่นในตาราง": "No players on the board yet",
    "คุณเรียนจบทุกบทแล้ว เก่งมาก!": "You finished every lesson. Great job!",
    "กด \"แต่งตัวมาสคอต\" เพื่อสวม": "Press \"Dress up Blaze\" to wear it",
    "เส้นทางการเรียนรู้": "Learning path",
    "ภาษาที่เรียน: อังกฤษ (กดเพื่อเปลี่ยน)": "Learning: English (tap to switch)",
    "ภาษาที่เรียน: ไทย (กดเพื่อเปลี่ยน)": "Learning: Thai (tap to switch)",
    # บทเรียน
    "ตรวจคำตอบ": "Check", "ข้อถัดไป": "Next", "ฟังเสียง": "Listen", "   ฟังเสียง": "   Listen",
    "ฟังโจทย์": "Hear question", "   ฟังโจทย์": "   Hear question", "   ฟังอีกครั้ง": "   Listen again",
    "🔥 ฝึกฝนเพื่อฟื้นฟูหัวใจ": "Practice to regain a heart", "กลับไปพักหัวใจก่อน": "Rest and come back later",
    "พิมพ์คำตอบภาษาอังกฤษ...": "Type your answer...", "พิมพ์คำตอบเป็นภาษาอังกฤษ:": "Type your answer:",
    "พิมพ์คำแปลเป็นภาษาอังกฤษ:": "Type the translation:",
    "ถูกต้อง!": "Correct!", "ยังไม่ถูกนะ": "Not quite", "กลับไปเรียนต่อ": "Back to the lesson",
    "อ่านคำที่กด: เปิด": "Read tapped words: on", "อ่านคำที่กด: ปิด": "Read tapped words: off",
    "(เล่นเสียงไม่ได้ จึงแสดงเป็นข้อความแทน)": "(Audio unavailable, showing text instead)",
    "หัวใจหมดแล้ว!": "Out of hearts!", "หรือพักไว้ก่อน หัวใจจะเต็มใหม่เองในวันถัดไป":
        "Or take a break: your hearts refill tomorrow.",
    "เสียงถูกปิดอยู่ (สามารถเปิดเสียงได้ที่หน้าตั้งค่า)": "Sound is off (turn it on in Settings).",
    "เสียงถูกปิดอยู่ จึงแสดงคำที่ต้องฟังเป็นข้อความแทน": "Sound is off, so the word is shown as text.",
    "ไม่พบระบบเสียงพูดในเครื่องนี้ (ลองติดตั้ง pyttsx3)": "No text-to-speech found on this device (try installing pyttsx3).",
    "ไม่พบระบบเสียงพูดในเครื่องนี้ จึงแสดงคำที่ต้องฟังเป็นข้อความแทน":
        "No text-to-speech found, so the word is shown as text.",
    "เครื่องนี้ไม่มีเสียงพูดภาษาไทยติดตั้งไว้ จึงอ่านโจทย์ภาษาไทยไม่ได้ ":
        "This device has no Thai voice installed, so Thai audio cannot be played. ",
    "(ลองเพิ่มที่ Windows Settings > Time & Language > Speech)":
        "(Add one in Windows Settings > Time & Language > Speech)",
    # สรุปผล
    "เรียนซ้ำ": "Repeat lesson", "กลับ Dashboard": "Back to Dashboard",
    "คำศัพท์ที่ได้เรียน (กดฟังเสียงได้เลย):": "Words you learned (tap to hear):",
    # Challenger
    "เล่น Challenger": "Play Challenger", "ตารางคะแนน Challenger": "Challenger leaderboard",
    "เรียงตามจำนวนข้อที่ตอบถูกมากที่สุดในหนึ่งรอบ": "Ranked by most correct answers in a single run",
    "ยังไม่มีใครทำสถิติ มาเป็นคนแรกกันเลย!": "No scores yet. Be the first!",
    "คุณยังไม่มีสถิติในโหมดนี้ ลองเล่นดูสิ!": "You have no score in this mode yet. Give it a try!",
    "แช่แข็ง": "Freeze", "ข้าม": "Skip", "เล่นอีกครั้ง": "Play again", "ดูผลคะแนน": "See results",
    "แพ้บอส!": "Boss defeated you!", "บอส: ห้ามใช้ไอเท็ม": "Boss: no items allowed",
    "ข้ามข้อนี้": "Question skipped", "50:50 ตัดตัวเลือกผิด 2 ข้อ": "50:50 removed 2 wrong options",
    "หมดเวลา! คุณตายแล้ว": "Time is up! You died", "สถิติใหม่!": "New record!", "ตอบถูกสูงสุด": "Best score",
    " (แพ้บอส)": " (lost to the boss)", "โหมดจับเวลา": "Timed mode",
    # สถิติ
    "XP 7 วันล่าสุด": "XP in the last 7 days", "ความแม่นยำแต่ละ Unit": "Accuracy by Unit",
    "หัวข้อที่ผิดบ่อย": "Most missed topics", "ยังไม่มีข้อมูล": "No data yet",
    "ยังไม่มี XP ใน 7 วันนี้ ไปเรียนกันเถอะ!": "No XP in the last 7 days. Let's learn!",
    "ยังไม่มีข้อที่ตอบผิด — เยี่ยมมาก! ทำต่อไปเลย": "No wrong answers yet. Excellent, keep going!",
    # โปรไฟล์
    "ความสำเร็จ": "Achievements", "(กดที่การ์ดเพื่อดูวิธีปลดล็อก)": "(tap a card to see how to unlock)",
    "รีเซ็ตความก้าวหน้า": "Reset progress", "ยืนยัน รีเซ็ต": "Yes, reset",
    "ยืนยันการรีเซ็ตความก้าวหน้า?": "Reset all progress?",
    "การกระทำนี้จะลบ XP, Streak, บทเรียนที่เรียนจบ และรหัสผ่านทั้งหมด":
        "This deletes your XP, streak, finished lessons and password.",
    "รีเซ็ตความก้าวหน้าเรียบร้อยแล้ว": "Progress has been reset.",
    "ปลดล็อกแล้ว!": "Unlocked!", "ยังไม่ปลดล็อก": "Locked",
    "เงื่อนไขที่ทำสำเร็จแล้ว:": "Completed requirement:", "วิธีปลดล็อก:": "How to unlock:",
    # ตั้งค่า
    "   ทดสอบเสียง": "   Test voice", "เปลี่ยนรหัสผ่าน": "Change password", "ออกจากเกม": "Quit game",
    "ออกจากระบบ (Log out)": "Log out", "เสียงทั้งหมด": "All sound", "เปิดอยู่": "On", "ปิดอยู่": "Off",
    "เสียงพื้นหลัง": "Music", "เสียงเอฟเฟกต์": "Sound effects", "เสียงโจทย์": "Voice",
    "(เสียงพูดอ่านคำ/โจทย์)": "(spoken words and questions)", "ไม่พบระบบเสียงพูด": "No speech engine found",
    "ความเร็วเสียงพูด": "Voice speed", "ตั้งไว้แล้ว": "Set", "ยังไม่ได้ตั้ง": "Not set",
    "รหัสผ่านเดิม (เว้นว่างได้ถ้ายังไม่เคยตั้ง)": "Current password (leave blank if none)",
    "รหัสผ่านใหม่": "New password", "ยืนยันรหัสผ่านใหม่อีกครั้ง": "Confirm new password",
    "รหัสผ่านเดิม": "Current password", "ยืนยันรหัสผ่านใหม่": "Confirm new password",
    "รหัสผ่านเดิมไม่ถูกต้อง": "Current password is wrong", "รหัสผ่านใหม่ทั้งสองช่องไม่ตรงกัน": "The new passwords do not match",
    "เปลี่ยนรหัสผ่านเรียบร้อยแล้ว": "Password changed",
    "ต้องการออกจากเกมใช่หรือไม่?": "Quit the game?", "ต้องการออกจากระบบใช่หรือไม่?": "Log out?",
    "ความคืบหน้าจะถูกบันทึกไว้ก่อนปิดเกม": "Your progress is saved before closing.",
    "จะกลับไปหน้าแรก (หน้าล็อกอิน) ความคืบหน้าถูกบันทึกแล้ว": "Returns to the login screen. Progress is saved.",
    "ไม่ทราบสาเหตุ": "Unknown reason",
    "เสียงไทย: มี": "Thai voice: installed",
    "เสียงไทย: ไม่มี (อ่านได้แค่คำอังกฤษ)": "Thai voice: not installed (Thai audio is shown as text)",
    # ตู้เสื้อผ้า
    "สุ่มชุด": "Random", "ถอดทั้งหมด": "Remove all", "ตู้เสื้อผ้าของเบลซ": "Blaze's wardrobe",
    "ถอดของแต่งตัวทั้งหมดแล้ว (สีตัวยังเหมือนเดิม)": "Removed all accessories (body color unchanged)",
    "กดที่การ์ดเพื่อสวม": "Tap a card to wear it", "ไม่สวม": "None", "สวมอยู่": "Worn", "ใส่ได้เลย": "Ready to wear",
    "หมวก": "Hats", "แว่นตา": "Glasses", "เครื่องประดับ": "Accessories", "สีตัว": "Body color",
    "หมวกปาร์ตี้": "Party hat", "หมวกแก๊ป": "Cap", "หมวกเชฟ": "Chef hat", "หมวกพ่อมด": "Wizard hat",
    "หมวกโจรสลัด": "Pirate hat", "มงกุฎราชา": "King's crown", "เขาปีศาจ": "Devil horns", "มงกุฎเพลิง": "Flame crown",
    "แว่นกลม": "Round glasses", "แว่นกันแดด": "Sunglasses", "โกเกิลนักรบ": "Warrior goggles", "แว่นดาว": "Star glasses",
    "โบว์ไท": "Bow tie", "ผ้าพันคอ": "Scarf", "เหรียญเกียรติยศ": "Medal of honor", "ผ้าคลุมฮีโร่": "Hero cape",
    "ส้มไฟ": "Fire orange", "ฟ้าน้ำแข็ง": "Ice blue", "เขียวมิ้นต์": "Mint green", "ชมพูบลอสซัม": "Blossom pink",
    "ม่วงราตรี": "Night purple", "ทองคำ": "Gold",
    # ความสำเร็จ
    "ก้าวแรกของมังกร": "Dragon's first step", "เรียนจบบทแรกของคุณ": "Finish your first lesson",
    "ไฟลุกต่อเนื่อง": "Keeping the fire", "เรียนต่อเนื่อง 3 วัน": "Learn 3 days in a row",
    "นักผจญภัยระดับกลาง": "Mid-level adventurer", "ไปถึง Level 5": "Reach Level 5",
    "ไร้ที่ติ": "Flawless", "เรียนจบบทโดยไม่เสียหัวใจเลย": "Finish a lesson without losing a heart",
    "ขยันขันแข็ง": "Hard worker", "เรียนจบครบ 5 บทเรียน": "Finish 5 lessons",
    "จอมปราชญ์ผู้สำเร็จการศึกษา": "Graduated sage", "เรียนจบครบทุกบทเรียนในเกม": "Finish every lesson in the course",
    "ไฟลุกทั้งสัปดาห์": "A week on fire", "เรียนต่อเนื่องครบ 7 วัน": "Learn 7 days in a row",
    "นักสะสม XP ตัวยง": "XP collector", "สะสม XP ให้ครบ 1,000": "Collect 1,000 XP",
    "ตำนานผู้พิชิต Challenger": "Challenger legend",
    "ไปถึงระดับความยาก 10 (Legend) ในโหมด Challenger": "Reach difficulty level 10 (Legend) in Challenger mode",
    "นักสะสมแฟชั่นตัวยง": "Fashion collector", "ปลดล็อกของแต่งตัวให้ครบทุกชิ้นในตู้เสื้อผ้า":
        "Unlock every item in the wardrobe",
}

# --------------------------- ข้อความที่มีค่าแทรก ({} = ส่วนที่เปลี่ยนไป) ---------------------------
PATTERNS = [
    ("สวัสดี {}!  (Level {})", "Hello {}!  (Level {})"),
    ("โหมด Challenger ({} ข้อ)", "Challenger mode ({} correct)"),
    ("ปลดล็อกของแต่งตัวใหม่ {} ชิ้น! เช่น \"{}\" กด \"แต่งตัวมาสคอต\" เพื่อสวม",
     "Unlocked {} new outfit items! e.g. \"{}\" Press \"Dress up Blaze\" to wear them"),
    ("ปลดล็อกของแต่งตัวใหม่ {} ชิ้น! \"{}\" กด \"แต่งตัวมาสคอต\" เพื่อสวม",
     "Unlocked {} new outfit items! \"{}\" Press \"Dress up Blaze\" to wear it"),
    ("ปลดล็อกของแต่งตัวใหม่ {} ชิ้น! เช่น \"{}\"", "Unlocked {} new outfit items! e.g. \"{}\""),
    ("ปลดล็อกความสำเร็จ: {}!", "Achievement unlocked: {}!"),
    ("ปลดล็อกแล้ว {}/{} ชิ้น", "Unlocked {}/{} items"),
    ("{} ยังล็อกอยู่: {}", "{} is still locked: {}"),
    ("ถึงเลเวล {}", "Reach level {}"), ("เรียนจบ {} บท", "Finish {} lessons"),
    ("แช่แข็ง x{d}", "Freeze x{d}"), ("ข้าม x{d}", "Skip x{d}"),
    ("Challenger ถึงระดับ {} ({})", "Reach Challenger level {} ({})"), ("ได้ความสำเร็จ \"{}\"", "Earn the achievement \"{}\""),
    ("ปลดล็อกความสำเร็จ", "Unlock an achievement"),
    ("ข้อ {d}/{d}", "Question {d}/{d}"),
    ("🔥 ฝึกฝนฟื้นฟูหัวใจ: ตอบถูกแล้ว {}/{}", "Heart practice: {}/{} correct"),
    ("ฝึกทบทวนคำที่เคยตอบผิด ตอบถูกครบ {} ข้อ รับหัวใจคืนทันที!",
     "Review words you got wrong. Answer {} correctly to win a heart back!"),
    ("ฟื้นฟูหัวใจสำเร็จ! ได้หัวใจคืนมา {} ดวง 💛", "Heart restored! You got {} heart back."),
    ("เรียนจบบท \"{}\"!", "Lesson \"{}\" complete!"),
    ("ตอบถูก {} ข้อ / ตอบผิด {} ข้อ", "{} correct / {} wrong"),
    ("ตอบถูก {} ข้อ / ตอบผิด {} ข้อ (แม่นยำ {}%)", "{} correct / {} wrong ({}% accuracy)"),
    ("ความแม่นยำ: {}%", "Accuracy: {}%"), ("XP ที่ได้รับ: +{} XP", "XP earned: +{} XP"),
    ("เวลาที่ใช้: {} วินาที", "Time spent: {} seconds"),
    ("คำศัพท์ที่ได้เรียน (แสดง {} จาก {} คำ):", "Words you learned (showing {} of {}):"),
    ("ระดับ {d}/{d}", "Level {d}/{d}"), ("{d} ข้อ", "{d} correct"),
    ("คุณอยู่อันดับที่ {} จาก {} คน ({} ข้อ)", "You are ranked {} of {} ({} correct)"),
    ("ระดับ {}! {}", "Level {}! {}"), ("BOSS มาแล้ว! ตอบถูกติดกัน {} ข้อ", "A BOSS appears! Answer {} in a row"),
    ("+{d} วินาที", "+{d} seconds"), ("-{d} วินาที", "-{d} seconds"),
    ("ชนะบอส! +{} วินาที + {}", "Boss defeated! +{} seconds + {}"), ("เวลาหยุด {} วินาที", "Time frozen for {} seconds"),
    ("เหลือเวลา {} วินาที", "{} seconds left"), ("แช่แข็งเวลา! {} วินาที (เหลือ {})", "Time frozen! {} s (left: {})"),
    ("ระดับ {}/{} {}   ตอบถูก {} ข้อ", "Level {}/{} {}   {} correct"),
    ("ถูกต้อง! +{} วินาที", "Correct! +{} seconds"), ("ถูกต้อง! +{} วินาที (คอมโบ x{} +{})", "Correct! +{} seconds (combo x{} +{})"),
    ("ถูกต้อง! +{} วินาที (คอมโบ x{})", "Correct! +{} seconds (combo x{})"),
    ("ยังไม่ถูกนะ -{} วินาที", "Not quite -{} seconds"), ("ยังไม่ถูกนะ -{} วินาที (แพ้บอส)", "Not quite -{} seconds (lost to the boss)"),
    ("ไปถึงระดับความยาก {}/{} ({})", "Reached difficulty {}/{} ({})"), ("สถิติสูงสุด: {} ข้อ", "Best score: {}"),
    ("อันดับที่ {} จาก {} คนในตาราง Challenger", "Rank {} of {} on the Challenger board"),
    ("คอมโบสูงสุด x{} · ล้มบอส {} ตัว", "Best combo x{} · bosses beaten: {}"),
    ("BOSS  ด่าน {}/{}", "BOSS  stage {}/{}"), ("คอมโบ x{d}", "Combo x{d}"), ("อีก {} ข้อ โบนัสเวลา +1", "{} more for +1 s bonus"),
    ("รวม {} · เฉลี่ย {}/วัน", "Total {} · avg {}/day"), ("รวมทุกโหมด {}%", "All modes {}%"), ("ผิด {}/{}", "Wrong {}/{}"),
    ("XP สะสม: {}", "Total XP: {}"), ("Streak: {} วัน", "Streak: {} days"), ("บทเรียนที่เรียนจบ: {} บท", "Lessons finished: {}"),
    ("ต่อเนื่อง {} วันแล้ว! สู้ๆ", "{} days in a row! Keep it up!"), ("ยินดีต้อนรับกลับมา {}!", "Welcome back, {}!"),
    ("ชื่อนี้ยังไม่เคยเล่น กรุณาตั้งรหัสผ่านอย่างน้อย {} ตัวอักษร", "New name: please set a password of at least {} characters."),
    ("รหัสผ่านใหม่ต้องมีอย่างน้อย {} ตัวอักษร", "The new password needs at least {} characters"),
    ("กำลังพูดทดสอบผ่าน {}... ฟังออกไหม?", "Testing voice via {}... can you hear it?"),
    ("เอนจิน: {}", "Engine: {}"), ("เสียงไทย: {}", "Thai voice: {}"),
    ("ไม่พบระบบเสียงพูดในเครื่องนี้: {}", "No speech engine on this device: {}"), ("เสียงพูดล้มเหลวจริง: {}", "Speech really failed: {}"),
]

_COMPILED = []
for _th, _en in PATTERNS:
    # {} = ข้อความอะไรก็ได้, {d} = ตัวเลขล้วน (ใช้กับรูปแบบสั้น ๆ ที่เสี่ยงไปชนข้อความอื่น เช่น "{d} ข้อ")
    _rx = "^" + re.escape(_th).replace(r"\{\}", "(.+?)").replace(r"\{d\}", r"(\d+)") + "$"
    _COMPILED.append((re.compile(_rx, re.S), _en.replace("{d}", "{}")))

_THAI = re.compile(r"[฀-๿]")


def ui_lang() -> str:
    return content.UI_LANG


def tr(text):
    """แปลข้อความเมนูเป็นภาษาของเมนูปัจจุบัน ไม่มีคำแปล/ไม่ใช่ข้อความ = คืนของเดิมเสมอ"""
    if content.UI_LANG != "en" or not isinstance(text, str) or not _THAI.search(text):
        return text
    hit = TEXT.get(text)
    if hit is not None:
        return hit
    for rx, en in _COMPILED:
        m = rx.match(text)
        if m:
            try:
                return en.format(*[tr(g) for g in m.groups()])
            except (IndexError, KeyError, ValueError):
                return text
    return text


def pick(th: str, en: str) -> str:
    """เลือกข้อความตามภาษาเมนู (ใช้กับคำที่ชนกับคำศัพท์ในคอร์ส เช่น "วันนี้" จึงใส่ใน TEXT ไม่ได้)"""
    return en if content.UI_LANG == "en" else th


class TFont:
    """ห่อ pygame.font.Font: แปลข้อความก่อน render/size (เมธอดอื่นส่งต่อให้ฟอนต์จริง)"""

    def __init__(self, font):
        self._font = font

    def render(self, text, *args, **kwargs):
        return self._font.render(tr(text), *args, **kwargs)

    def size(self, text):
        return self._font.size(tr(text))

    def __getattr__(self, name):
        return getattr(self._font, name)
