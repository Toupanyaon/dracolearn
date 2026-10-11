"""
content.py
----------
โครงสร้างข้อมูล (dataclasses) และเนื้อหาบทเรียน/คำถาม/Achievement ทั้งหมด
แยกออกจากไฟล์ตรรกะเกม เพื่อให้แก้ไข/เพิ่มเนื้อหาได้ง่ายในที่เดียว
"""

import colorsys
import re
from typing import List

from .models import Question, Lesson, Unit, Achievement  # noqa: F401  (re-export ให้ content.Question ฯลฯ ใช้ได้เหมือนเดิม)
from .bank_lessons_extra import EXTRA_QUESTIONS, EXTRA_LESSON_QUESTION_IDS
from .bank_listening import LISTENING_QUESTIONS, LISTENING_LESSON_QUESTION_IDS
from .bank_challenger import CHALLENGER_QUESTIONS


# ---------------------------------------------------------------------------
# คลังคำถาม  (ทั้งหมดรวมอยู่ใน QUESTIONS ลิสต์เดียว ท้ายส่วนนี้จะต่อคลังเพิ่มเติมเข้ามาให้)
#   - ไฟล์นี้      : q1-q20 (โจทย์ไทย) + e1-e35 (โจทย์อังกฤษ)  = 55 ข้อ  -> บทเรียนปกติ
#   - bank_lessons_extra.py : q21-q65 + e36-e78                = 88 ข้อ  -> บทเรียนปกติ (เพิ่มให้ทุกบทมี ~10 ข้อ)
#   - bank_listening.py     : l1-l60  (โจทย์ฟังแล้วตอบ listen_mcq/listen_type) = 60 ข้อ -> บทเรียนปกติ บทละ 4 ข้อ
#   - bank_challenger.py    : c1-c77 (ระดับ 4-10)              = 77 ข้อ  -> โหมด Challenger เท่านั้น
# ---------------------------------------------------------------------------
QUESTIONS: List[Question] = [
    # --- Unit 1: Greetings ---
    Question("q1", "mcq", 'คำว่า "สวัสดี" ตรงกับข้อใด?', "Hello",
             options=["Hello", "Goodbye", "Please", "Sorry"],
             explanation='"Hello" แปลว่า สวัสดี ใช้ทักทายทั่วไป', vocab="Hello"),
    Question("q2", "mcq", 'คำว่า "ลาก่อน" ตรงกับข้อใด?', "Goodbye",
             options=["Goodbye", "Thank you", "Welcome", "Please"],
             explanation='"Goodbye" ใช้กล่าวลา', vocab="Goodbye"),
    Question("q3", "word_order", "เรียงคำให้เป็นประโยค: สวัสดีตอนเช้าค่ะ/ครับ", "Good morning",
             word_bank=["morning", "Good", "night", "Bad"],
             explanation='"Good morning" แปลว่า สวัสดีตอนเช้า', vocab="Good morning"),
    Question("q4", "translate_type", 'แปลเป็นภาษาอังกฤษ: "ขอบคุณ"', "Thank you",
             alt_answers=["Thanks", "Thank you very much", "Thanks a lot"],
             explanation='"Thank you" แปลว่า ขอบคุณ', vocab="Thank you"),
    Question("q5", "mcq", 'คำว่า "ขอโทษ" ตรงกับข้อใด?', "Sorry",
             options=["Sorry", "Please", "Excuse", "Welcome"],
             explanation='"Sorry" ใช้ขอโทษ', vocab="Sorry"),

    # --- Unit 2: Introductions ---
    Question("q6", "mcq", '"ฉันชื่อเบลซ" ตรงกับข้อใด?', "My name is Blaze",
             options=["My name is Blaze", "I am from Blaze", "Blaze is here", "Call me at Blaze"],
             explanation='"My name is ..." ใช้บอกชื่อตัวเอง', vocab="My name is"),
    Question("q7", "translate_type", 'แปลเป็นภาษาอังกฤษ: "ยินดีที่ได้รู้จัก"', "Nice to meet you",
             alt_answers=["Pleased to meet you", "Glad to meet you", "It is nice to meet you"],
             explanation='"Nice to meet you" ใช้ตอนเจอกันครั้งแรก', vocab="Nice to meet you"),
    Question("q8", "word_order", "เรียงคำ: คุณมาจากไหน?", "Where are you from",
             word_bank=["from", "Where", "you", "are"],
             explanation='"Where are you from?" แปลว่า คุณมาจากไหน', vocab="Where are you from"),
    Question("q9", "mcq", '"อายุเท่าไหร่" ตรงกับข้อใด?', "How old are you",
             options=["How old are you", "How are you", "What time is it", "Who are you"],
             explanation='"How old are you?" ใช้ถามอายุ', vocab="How old are you"),

    # --- Unit 3: Family ---
    Question("q10", "mcq", 'คำว่า "แม่" ตรงกับข้อใด?', "Mother",
             options=["Mother", "Father", "Sister", "Brother"],
             explanation='"Mother" แปลว่า แม่', vocab="Mother"),
    Question("q11", "mcq", 'คำว่า "พ่อ" ตรงกับข้อใด?', "Father",
             options=["Father", "Mother", "Uncle", "Aunt"],
             explanation='"Father" แปลว่า พ่อ', vocab="Father"),
    Question("q12", "translate_type", 'แปลเป็นภาษาอังกฤษ: "นี่คือน้องสาวของฉัน"', "This is my sister",
             alt_answers=["This is my younger sister", "This is my little sister", "She is my sister", "She is my younger sister", "She is my little sister"],
             explanation='"This is my sister" แปลว่า นี่คือน้องสาวของฉัน', vocab="Sister"),
    Question("q13", "word_order", "เรียงคำ: ครอบครัวของฉันมีสี่คน", "My family has four people",
             word_bank=["has", "My", "family", "four", "people"],
             explanation='"My family has four people" แปลว่า ครอบครัวของฉันมีสี่คน', vocab="Family"),

    # --- Unit 4: Food and Drinks ---
    Question("q14", "mcq", 'คำว่า "น้ำ" ตรงกับข้อใด?', "Water",
             options=["Water", "Rice", "Milk", "Juice"],
             explanation='"Water" แปลว่า น้ำ', vocab="Water"),
    Question("q15", "mcq", 'คำว่า "ข้าว" ตรงกับข้อใด?', "Rice",
             options=["Rice", "Bread", "Noodle", "Fruit"],
             explanation='"Rice" แปลว่า ข้าว', vocab="Rice"),
    Question("q16", "translate_type", 'แปลเป็นภาษาอังกฤษ: "ฉันหิวน้ำ"', "I am thirsty",
             alt_answers=["I am very thirsty", "I am so thirsty", "I feel thirsty"],
             explanation='"I am thirsty" แปลว่า ฉันหิวน้ำ', vocab="Thirsty"),
    Question("q17", "word_order", "เรียงคำ: ฉันชอบกินผลไม้", "I like eating fruit",
             word_bank=["eating", "I", "like", "fruit"],
             explanation='"I like eating fruit" แปลว่า ฉันชอบกินผลไม้', vocab="Fruit"),

    # --- Unit 5: Daily Activities ---
    Question("q18", "mcq", 'คำว่า "ตื่นนอน" ตรงกับข้อใด?', "Wake up",
             options=["Wake up", "Go to bed", "Take a bath", "Brush teeth"],
             explanation='"Wake up" แปลว่า ตื่นนอน', vocab="Wake up"),
    Question("q19", "translate_type", 'แปลเป็นภาษาอังกฤษ: "ฉันไปโรงเรียนทุกวัน"', "I go to school every day",
             alt_answers=["I go to school everyday", "Every day I go to school", "Everyday I go to school", "I go to school daily"],
             explanation='"I go to school every day" แปลว่า ฉันไปโรงเรียนทุกวัน', vocab="School"),
    Question("q20", "word_order", "เรียงคำ: เขาทำการบ้านตอนเย็น", "He does homework in the evening",
             word_bank=["homework", "He", "does", "in", "the", "evening"],
             explanation='"He does homework in the evening" แปลว่า เขาทำการบ้านตอนเย็น', vocab="Homework"),

    # =======================================================================
    # โจทย์ภาษาอังกฤษ (prompt_lang="en") บทละ 2-3 ข้อ — คำตอบเป็นภาษาอังกฤษทั้งหมด
    # =======================================================================

    # --- Unit 1: Greetings ---
    Question("e1", "mcq", "Which word is polite when you ask for something?", "Please",
             options=["Please", "Goodbye", "Hello", "Sorry"],
             explanation='"Please" makes a request polite (กรุณา)', vocab="Please", prompt_lang="en"),
    Question("e2", "word_order", "Put the words in order to ask about feelings.", "How are you",
             word_bank=["are", "How", "you", "is"],
             explanation='"How are you?" is a common greeting (สบายดีไหม)', vocab="How are you", prompt_lang="en"),
    Question("e3", "mcq", "What do you say before you go to sleep?", "Good night",
             options=["Good night", "Good morning", "Hello", "Welcome"],
             explanation='"Good night" is said before sleeping (ราตรีสวัสดิ์)', vocab="Good night", prompt_lang="en"),
    Question("e4", "translate_type", "Type the missing word: Good ______! (after sunset)", "evening",
             alt_answers=["Good evening"],
             explanation='"Good evening" is used in the evening (สวัสดีตอนเย็น)', vocab="Good evening", prompt_lang="en"),
    Question("e5", "mcq", "Someone helps you. What do you say?", "Thank you",
             options=["Thank you", "Sorry", "Good night", "Goodbye"],
             explanation='We say "Thank you" to show thanks', prompt_lang="en"),
    Question("e6", "word_order", "Put the words in order to reply to \"Thank you\".", "You're welcome",
             word_bank=["welcome", "You're", "sorry"],
             explanation='"You\'re welcome" is the reply to "Thank you" (ยินดี)', vocab="You're welcome", prompt_lang="en"),

    # --- Unit 2: Introductions ---
    Question("e7", "mcq", "Complete: My ____ is Blaze.", "name",
             options=["name", "age", "from", "family"],
             explanation='"My name is ..." tells your name', vocab="Name", prompt_lang="en"),
    Question("e8", "translate_type", "Type the missing word: Nice to ______ you.", "meet",
             explanation='"Nice to meet you" is said when we first meet', vocab="Meet", prompt_lang="en"),
    Question("e9", "mcq", "Complete: I am ____ Thailand.", "from",
             options=["from", "at", "on", "of"],
             explanation='"I am from ..." tells your country', vocab="From", prompt_lang="en"),
    Question("e10", "word_order", "Put the words in order: say where you are from.", "I am from Thailand",
             word_bank=["from", "I", "Thailand", "am", "is"],
             explanation='"I am from Thailand" (ฉันมาจากประเทศไทย)', vocab="Thailand", prompt_lang="en"),
    Question("e11", "translate_type", "Type the missing word: I ____ from Japan.", "am",
             explanation='Use "am" with "I": I am from Japan', prompt_lang="en"),
    Question("e12", "mcq", 'Which is the correct answer to "How old are you?"', "I am ten years old",
             options=["I am ten years old", "I am ten years", "I have ten years old", "I am ten year old"],
             explanation='Say "I am ... years old"', vocab="Years old", prompt_lang="en"),
    Question("e13", "translate_type", "Type the missing word: I am twelve ______ old.", "years",
             explanation='"Years old" tells your age', prompt_lang="en"),

    # --- Unit 3: Family ---
    Question("e14", "mcq", "Who is your mother's sister?", "Aunt",
             options=["Aunt", "Uncle", "Grandmother", "Cousin"],
             explanation="Your mother's sister is your aunt (ป้า/น้า)", vocab="Aunt", prompt_lang="en"),
    Question("e15", "mcq", "Complete: My father and mother are my ____.", "parents",
             options=["parents", "cousins", "friends", "teachers"],
             explanation='"Parents" means father and mother (พ่อแม่)', vocab="Parents", prompt_lang="en"),
    Question("e16", "mcq", "Your mother's other son is your ____.", "brother",
             options=["brother", "uncle", "cousin", "father"],
             explanation='"Brother" is a boy in your family with the same parents (พี่/น้องชาย)', vocab="Brother", prompt_lang="en"),
    Question("e17", "word_order", "Put the words in order to introduce a boy in your family.", "He is my brother",
             word_bank=["is", "He", "my", "brother", "sister"],
             explanation='"He is my brother" (เขาคือพี่/น้องชายของฉัน)', prompt_lang="en"),
    Question("e18", "translate_type", "Type the missing word: My mother's mother is my ______.", "grandmother",
             alt_answers=["grandma", "granny"],
             explanation='"Grandmother" means your mother\'s or father\'s mother (ยาย/ย่า)', vocab="Grandmother", prompt_lang="en"),
    Question("e19", "mcq", "Dad, Mom and me. How many people are in the family?", "Three",
             options=["Two", "Three", "Four", "Five"],
             explanation="Dad + Mom + me = three", vocab="Three", prompt_lang="en"),
    Question("e20", "word_order", "Put the words in order to say how you feel about your family.", "I love my family",
             word_bank=["love", "I", "my", "family", "hate"],
             explanation='"I love my family" (ฉันรักครอบครัวของฉัน)', vocab="Love", prompt_lang="en"),

    # --- Unit 4: Food and Drinks ---
    Question("e21", "mcq", "Which one is a drink?", "Milk",
             options=["Milk", "Rice", "Bread", "Noodle"],
             explanation='"Milk" is a drink (นม)', vocab="Milk", prompt_lang="en"),
    Question("e22", "mcq", "Which food is made from wheat?", "Bread",
             options=["Bread", "Rice", "Water", "Milk"],
             explanation='"Bread" is made from wheat flour (ขนมปัง)', vocab="Bread", prompt_lang="en"),
    Question("e23", "mcq", "You want to eat food. You say: I am ____.", "hungry",
             options=["hungry", "thirsty", "sleepy", "angry"],
             explanation='"Hungry" means you want to eat (หิวข้าว)', vocab="Hungry", prompt_lang="en"),
    Question("e24", "translate_type", "Type the missing word: I am hungry, so I want to ____.", "eat",
             explanation='"Eat" means กิน', vocab="Eat", prompt_lang="en"),
    Question("e25", "word_order", "Put the words in order to ask for a drink.", "I want some water",
             word_bank=["want", "I", "some", "water", "eat"],
             explanation='"I want some water" (ฉันอยากได้น้ำ)', prompt_lang="en"),
    Question("e26", "mcq", "Which one is a fruit?", "Banana",
             options=["Banana", "Rice", "Milk", "Bread"],
             explanation='"Banana" is a fruit (กล้วย)', vocab="Banana", prompt_lang="en"),
    Question("e27", "translate_type", "Type the missing word: An ______ a day keeps the doctor away.", "apple",
             explanation='A famous saying: "An apple a day keeps the doctor away"', vocab="Apple", prompt_lang="en"),

    # --- Unit 5: Daily Activities ---
    Question("e28", "mcq", "What do you do at night when you are sleepy?", "Go to bed",
             options=["Go to bed", "Wake up", "Do homework", "Go to school"],
             explanation='"Go to bed" means เข้านอน', vocab="Go to bed", prompt_lang="en"),
    Question("e29", "word_order", "Put the words in order: say when you get up.", "I wake up at six",
             word_bank=["wake", "I", "up", "at", "six", "bed"],
             explanation='"I wake up at six" (ฉันตื่นนอนตอนหกโมง)', prompt_lang="en"),
    Question("e30", "translate_type", "Type the missing word: I brush my ______ every morning.", "teeth",
             explanation='"Teeth" is the plural of "tooth" (ฟัน)', vocab="Teeth", prompt_lang="en"),
    Question("e31", "mcq", "Who learns at school?", "Student",
             options=["Student", "Doctor", "Farmer", "Pilot"],
             explanation='A "student" learns at school (นักเรียน)', vocab="Student", prompt_lang="en"),
    Question("e32", "word_order", "Put the words in order to say where you go every day.", "We go to school",
             word_bank=["go", "We", "to", "school", "at"],
             explanation='"We go to school" (เราไปโรงเรียน)', prompt_lang="en"),
    Question("e33", "translate_type", "Type the missing word: Students study in a c________.", "classroom",
             alt_answers=["class room"],
             explanation='"Classroom" is the room where students study (ห้องเรียน)', vocab="Classroom", prompt_lang="en"),
    Question("e34", "mcq", "Complete: He ____ homework in the evening.", "does",
             options=["does", "do", "doing", "done"],
             explanation='Use "does" with he/she/it', vocab="Does", prompt_lang="en"),
    Question("e35", "word_order", "Put the words in order to talk about a hobby.", "She reads a book",
             word_bank=["reads", "She", "a", "book", "read"],
             explanation='"She reads a book" (เธออ่านหนังสือ)', vocab="Read", prompt_lang="en"),
]

BASE_QUESTION_COUNT = len(QUESTIONS)
QUESTIONS += EXTRA_QUESTIONS + LISTENING_QUESTIONS + CHALLENGER_QUESTIONS

QUESTION_MAP = {q.id: q for q in QUESTIONS}
CHALLENGER_QUESTION_IDS = frozenset(q.id for q in CHALLENGER_QUESTIONS)


# ---------------------------------------------------------------------------
# ตรวจคำตอบ: รองรับคำตอบหลายรูปแบบ
#   - ไม่สนตัวพิมพ์เล็ก-ใหญ่, ช่องว่างเกิน, เครื่องหมายวรรคตอน (. , ! ?) และ ' แบบโค้ง (’)
#   - ตัวย่อ (I'm, you're, he's ...) ถือว่าเท่ากับแบบเต็ม (I am, you are, he is ...)
#   - alt_answers ของแต่ละข้อ ใช้ใส่คำตอบทางเลือก เช่น "Thanks" แทน "Thank you"
# ---------------------------------------------------------------------------
_CONTRACTIONS = {
    "i'm": "i am", "you're": "you are", "he's": "he is", "she's": "she is",
    "it's": "it is", "we're": "we are", "they're": "they are",
    "that's": "that is", "what's": "what is", "there's": "there is",
    "where's": "where is", "who's": "who is", "here's": "here is",
}


def normalize_answer(text: str) -> str:
    t = text.strip().lower().replace("\u2019", "'").replace("\u2018", "'")
    # ตัดเครื่องหมายวรรคตอน (เก็บ ' ไว้ให้ตัวย่อ) และ "ต้องเก็บอักษรไทยทั้งบล็อกไว้": สระบน/วรรณยุกต์ (ิ ้ ์ ั) ไม่นับเป็น \w
    # ถ้าไม่ยกเว้นไว้ จะถูกตัดทิ้งจน "สวัสดี" กลายเป็น "สว สด" แล้วตรวจคำตอบภาษาไทยผิดทั้งหมด
    t = re.sub(r"[^\w\s'\u0e00-\u0e7f]", " ", t)
    words = [_CONTRACTIONS.get(w, w) for w in t.split()]
    return " ".join(words)


def is_correct_answer(question: "Question", given: str) -> bool:
    """True ถ้าคำตอบตรงกับคำตอบหลักหรือคำตอบทางเลือกข้อใดข้อหนึ่ง (หลัง normalize)"""
    accepted = {normalize_answer(question.correct_answer)}
    accepted.update(normalize_answer(a) for a in question.alt_answers)
    return normalize_answer(given) in accepted


def prompt_for_speech(text: str) -> str:
    """แปลงโจทย์เป็นข้อความสำหรับให้ TTS อ่าน: ช่องว่างที่เป็นขีดล่าง (____) อ่านว่า "blank"
    เช่น "My ____ is Blaze." -> "My blank is Blaze." (แสดงบนหน้าจอยังเป็น ____ เหมือนเดิม)"""
    spoken = re.sub(r"_{2,}", " blank ", text)
    return re.sub(r"\s+", " ", spoken).replace(" .", ".").replace(" ,", ",").replace(" !", "!").strip()


def get_questions(ids: List[str]) -> List[Question]:
    return [QUESTION_MAP[i] for i in ids]


# ---------------------------------------------------------------------------
# หน่วยการเรียน (Unit) และบทเรียน (Lesson) - 5 Unit, อย่างน้อย Unit ละ 3 บท
# ---------------------------------------------------------------------------
UNITS: List[Unit] = [
    Unit("u1", "Greetings", "คำทักทายเบื้องต้น", [
        Lesson("u1l1", "ทักทายง่าย ๆ", ["q1", "q2", "e1", "e2"]),
        Lesson("u1l2", "สวัสดีตอนเช้า", ["q3", "q4", "e3", "e4"]),
        Lesson("u1l3", "ขอบคุณและขอโทษ", ["q5", "q1", "q4", "e5", "e6"]),
    ]),
    Unit("u2", "Introductions", "แนะนำตัวเอง", [
        Lesson("u2l1", "บอกชื่อตัวเอง", ["q6", "q7", "e7", "e8"]),
        Lesson("u2l2", "ถามที่มา", ["q8", "e9", "e10", "e11"]),
        Lesson("u2l3", "ถามอายุ", ["q9", "q6", "e12", "e13"]),
    ]),
    Unit("u3", "Family", "ครอบครัว", [
        Lesson("u3l1", "พ่อแม่", ["q10", "q11", "e14", "e15"]),
        Lesson("u3l2", "พี่น้อง", ["q12", "e16", "e17", "e18"]),
        Lesson("u3l3", "สมาชิกครอบครัว", ["q13", "q10", "q11", "e19", "e20"]),
    ]),
    Unit("u4", "Food and Drinks", "อาหารและเครื่องดื่ม", [
        Lesson("u4l1", "อาหารพื้นฐาน", ["q14", "q15", "e21", "e22"]),
        Lesson("u4l2", "รู้สึกหิว-กระหาย", ["q16", "e23", "e24", "e25"]),
        Lesson("u4l3", "ผลไม้โปรด", ["q17", "q14", "e26", "e27"]),
    ]),
    Unit("u5", "Daily Activities", "กิจวัตรประจำวัน", [
        Lesson("u5l1", "ตื่นเช้า", ["q18", "e28", "e29", "e30"]),
        Lesson("u5l2", "ไปโรงเรียน", ["q19", "e31", "e32", "e33"]),
        Lesson("u5l3", "การบ้านตอนเย็น", ["q20", "q18", "e34", "e35"]),
    ]),
]

# ต่อโจทย์เพิ่มท้ายแต่ละบทเรียน (ต่อท้ายลิสต์เดิม ลำดับข้อเดิมไม่เปลี่ยน)
for _unit in UNITS:
    for _lesson in _unit.lessons:
        _lesson.question_ids = (list(_lesson.question_ids) + EXTRA_LESSON_QUESTION_IDS.get(_lesson.id, [])
                               + LISTENING_LESSON_QUESTION_IDS.get(_lesson.id, []))

def unit_id_of_question(qid: str) -> str:
    """Unit ที่ข้อนี้สังกัด; ข้อที่ไม่อยู่ในบทเรียน (คลัง Challenger) คืน "challenger" """
    home = QUESTION_HOME.get(qid)
    return home[0].id if home else "challenger"

def lesson_questions() -> List[Question]:
    """โจทย์ทั้งหมดที่อยู่ในบทเรียนปกติ (ไม่รวมโจทย์เฉพาะโหมด Challenger)"""
    return [q for q in QUESTIONS if q.id in LESSON_QUESTION_IDS]


# ---------------------------------------------------------------------------
# ระดับความยากของโจทย์ (ใช้ในโหมด Challenger) - 10 ระดับ ไล่จากง่ายไปยาก
#  - ระดับ 1-3  (AUTO_LEVELS): โจทย์บทเรียนปกติ (A1) ที่ไม่ได้ใส่ difficulty ระบบคิดคะแนนความยากให้เอง แล้วแบ่ง
#        เป็น 3 ระดับเท่า ๆ กัน: Unit ที่โจทย์อยู่ (ยิ่งหลังยิ่งยาก) + ชนิดข้อ (เลือกตอบ < เรียงคำ < พิมพ์เอง)
#        + โจทย์ภาษาอังกฤษยากกว่าโจทย์ไทยนิดหน่อย + คำตอบยิ่งยาวยิ่งยาก
#  - ระดับ 4-10: โจทย์ใน bank_challenger.py ที่กำหนด difficulty เองทุกข้อ (A2+ -> C2)
#  - ข้อไหนอยากกำหนดเอง ใส่ difficulty=1..10 ได้เลย (ชนะการคำนวณอัตโนมัติ)
# ---------------------------------------------------------------------------
DIFFICULTY_LEVELS = 10
AUTO_LEVELS = 3   # ระดับที่โจทย์บทเรียนปกติ (คำนวณอัตโนมัติ) จะถูกแบ่งลงไป: ระดับ 1..AUTO_LEVELS
_QTYPE_WEIGHT = {"mcq": 0.0, "listen_mcq": 0.5, "word_order": 1.5, "listen_type": 2.5, "translate_type": 3.0}

# ชื่อประจำระดับ (ดัชนี 0 = ระดับ 1) - ตั้งตามความโหดของระดับ ยิ่งสูงยิ่งโหด แสดงบนหน้าจอโหมด Challenger
LEVEL_NAMES = [
    "Baby Chick",          # 1  ลูกเจี๊ยบ
    "Naughty Kitten",      # 2  ลูกแมวซน
    "Rookie Fighter",      # 3  นักสู้มือใหม่
    "Apprentice Hunter",   # 4  นักล่าฝึกหัด (เริ่มเข้าสู่ A2+)
    "Frontline Warrior",   # 5  นักรบสายลุย (B1)
    "Ruthless",            # 6  จอมโหด (B1+)
    "Wicked Demon",        # 7  ปีศาจร้าย (B2)
    "Hell King",           # 8  ราชันย์นรก (B2+)
    "Grim Reaper",         # 9  มัจจุราช (C1)
    "God of Destruction",  # 10 เทพเจ้าแห่งความพินาศ (C2)
]
# ระดับภาษา CEFR คร่าว ๆ ของแต่ละระดับ (ใช้เป็นข้อมูลอ้างอิง/เอกสาร)
LEVEL_CEFR = ["A1", "A1", "A1", "A2+", "B1", "B1+", "B2", "B2+", "C1", "C2"]


def level_name(level: int) -> str:
    """ชื่อเรียกของระดับความยาก (1..DIFFICULTY_LEVELS) เช่น 7 -> 'Advanced'"""
    return LEVEL_NAMES[max(1, min(DIFFICULTY_LEVELS, level)) - 1]


def _build_difficulty_levels() -> dict:
    first_unit = {}
    for unit_index, unit in enumerate(UNITS):
        for lesson in unit.lessons:
            for qid in lesson.question_ids:
                first_unit.setdefault(qid, unit_index)

    def score(q: Question) -> float:
        words = len(q.correct_answer.split())
        return (first_unit.get(q.id, 0)
                + _QTYPE_WEIGHT.get(q.qtype, 0.0)
                + (0.5 if q.prompt_lang == "en" else 0.0)
                + min(words - 1, 4) * 0.4)

    auto = sorted((q for q in QUESTIONS if not q.difficulty), key=score)  # sorted เสถียร: คะแนนเท่ากันคงลำดับเดิม
    levels = {q.id: min(AUTO_LEVELS, i * AUTO_LEVELS // len(auto) + 1) for i, q in enumerate(auto)}
    for q in QUESTIONS:
        if q.difficulty:
            levels[q.id] = max(1, min(DIFFICULTY_LEVELS, q.difficulty))
    return levels


def question_difficulty(question: "Question") -> int:
    """ระดับความยาก 1 (ง่ายสุด) .. DIFFICULTY_LEVELS (ยากสุด) ของโจทย์ข้อนั้น"""
    return QUESTION_LEVEL[question.id]


def questions_at_level(level: int) -> List[Question]:
    """โจทย์ทั้งหมดที่อยู่ในระดับความยากนี้"""
    return [q for q in QUESTIONS if QUESTION_LEVEL[q.id] == level]


# ---------------------------------------------------------------------------
# ธีมสีพาสเทลของพื้นหลัง
#  - ทุกบทเรียนได้ "สีเฉพาะตัว" ไม่ซ้ำกันเลยทั้งเกม: แบ่งวงล้อสีเป็นช่วงเท่า ๆ กันตามจำนวนบทเรียนทั้งหมด
#    (15 บท = ห่างกันบทละ 24 องศา) เรียงต่อเนื่องตาม Unit ทำให้แต่ละ Unit เป็นโทนสีใกล้เคียงกัน 3 เฉด
#    แต่ไม่มีบทไหนใช้สีซ้ำกับบทอื่น (เพิ่ม Unit/บทใหม่ สีก็ยังถูกแบ่งใหม่ให้ไม่ซ้ำอัตโนมัติ)
#  - ในบทเรียนเดียวกัน แต่ละข้อย่อยสลับไปมาระหว่าง 2 โทน (อ่อน / เข้มขึ้นนิด) ของสีบทนั้น
# ---------------------------------------------------------------------------
HUE_OFFSET = 8  # เลื่อนวงล้อสีเล็กน้อย ไม่ให้เริ่มที่แดงสด
# (ความอิ่มสีบน, ความสว่างบน), (ความอิ่มสีล่าง, ความสว่างล่าง) ของแต่ละโทน - อิ่มสีต่ำ + สว่างสูง = พาสเทล
PASTEL_TONES = [
    ((0.26, 1.00), (0.40, 0.96)),  # โทน A: อ่อนใส
    ((0.36, 0.98), (0.48, 0.94)),  # โทน B: เข้มขึ้นเล็กน้อย ให้เห็นการสลับชัดเจน
]


def _pastel(hue: float, sat: float, val: float) -> tuple:
    r, g, b = colorsys.hsv_to_rgb((hue % 360) / 360.0, sat, val)
    return (int(r * 255), int(g * 255), int(b * 255))


def _build_lesson_hues() -> dict:
    lessons = [(u, l) for u in UNITS for l in u.lessons]
    step = 360.0 / max(1, len(lessons))
    return {l.id: (HUE_OFFSET + i * step) % 360 for i, (_, l) in enumerate(lessons)}


def lesson_background(lesson, question_index: int = 0) -> tuple:
    """คืน (สีบน, สีล่าง) พาสเทลของพื้นหลัง ตามบทเรียนและลำดับข้อ (ข้อคี่/คู่สลับโทนกัน)"""
    hue = LESSON_HUE.get(lesson.id, HUE_OFFSET)
    (st, vt), (sb, vb) = PASTEL_TONES[question_index % len(PASTEL_TONES)]
    return _pastel(hue, st, vt), _pastel(hue, sb, vb)


def all_lessons_flat():
    """คืนลิสต์ (unit, lesson) เรียงตามลำดับ ใช้เช็คว่าบทไหนถัดไปควรปลดล็อก"""
    flat = []
    for unit in UNITS:
        for lesson in unit.lessons:
            flat.append((unit, lesson))
    return flat


# ---------------------------------------------------------------------------
# Achievements (อย่างน้อย 5 รายการ)
# ---------------------------------------------------------------------------
ACHIEVEMENTS: List[Achievement] = [
    Achievement("first_lesson", "ก้าวแรกของมังกร", "เรียนจบบทแรกของคุณ", "egg"),
    Achievement("streak_3", "ไฟลุกต่อเนื่อง", "เรียนต่อเนื่อง 3 วัน", "flame"),
    Achievement("level_5", "นักผจญภัยระดับกลาง", "ไปถึง Level 5", "star"),
    Achievement("perfect_lesson", "ไร้ที่ติ", "เรียนจบบทโดยไม่เสียหัวใจเลย", "shield"),
    Achievement("five_lessons", "ขยันขันแข็ง", "เรียนจบครบ 5 บทเรียน", "trophy"),
    # --- เพิ่มใหม่ 5 รายการ ผูกกับฟีเจอร์ที่เพิ่มมาทีหลัง (Challenger, Wardrobe, บทเรียนครบชุด) ---
    Achievement("all_lessons", "จอมปราชญ์ผู้สำเร็จการศึกษา", "เรียนจบครบทุกบทเรียนในเกม", "crown"),
    Achievement("streak_7", "ไฟลุกทั้งสัปดาห์", "เรียนต่อเนื่องครบ 7 วัน", "comet"),
    Achievement("xp_1000", "นักสะสม XP ตัวยง", "สะสม XP ให้ครบ 1,000", "diamond"),
    Achievement("survival_legend", "ตำนานผู้พิชิต Challenger", "ไปถึงระดับความยาก 10 (Legend) ในโหมด Challenger", "medal"),
    Achievement("wardrobe_complete", "นักสะสมแฟชั่นตัวยง", "ปลดล็อกของแต่งตัวให้ครบทุกชิ้นในตู้เสื้อผ้า", "closet"),
]
ACHIEVEMENT_MAP = {a.id: a for a in ACHIEVEMENTS}


# ---------------------------------------------------------------------------
# คอร์สที่เรียน (หลายภาษา)
#   "en" = เรียนภาษาอังกฤษ (โจทย์/เมนูเป็นไทย)  <- ค่าเริ่มต้น  "th" = เรียนภาษาไทย (โจทย์/เมนูเป็นอังกฤษ)
# ข้อมูลของตัวเกม (UNITS, QUESTIONS, QUESTION_MAP ...) เป็นตัวแปรระดับโมดูล เปลี่ยนด้วย set_course() ซึ่งแทนที่ทั้งชุดแล้วคำนวณตารางอนุพันธ์ใหม่
# โค้ดส่วนอื่นเรียก content.UNITS ฯลฯ ตอนใช้งาน (ไม่ import ค่าไปเก็บไว้) จึงเห็นคอร์สปัจจุบันเสมอ
# ---------------------------------------------------------------------------
COURSES = {
    "en": {"name": "English", "learn_lang": "en", "ui_lang": "th"},
    "th": {"name": "Thai", "learn_lang": "th", "ui_lang": "en"},
}
DEFAULT_COURSE = "en"
COURSE = DEFAULT_COURSE
LEARN_LANG = "en"   # ภาษาที่กำลังเรียน: ใช้เลือกเสียง TTS ของคำตอบ/ตัวเลือก
UI_LANG = "th"      # ภาษาของเมนู/คำอธิบายในเกม (i18n.py แปลให้ตามค่านี้)

_EN_DATA = {"QUESTIONS": QUESTIONS, "UNITS": UNITS, "CHALLENGER_QUESTION_IDS": CHALLENGER_QUESTION_IDS,
            "AUTO_LEVELS": AUTO_LEVELS}


def _derive():
    """สร้างตารางอนุพันธ์ทั้งหมดใหม่จาก QUESTIONS/UNITS ปัจจุบัน (เรียกตอน import และทุกครั้งที่เปลี่ยนคอร์ส)"""
    global QUESTION_MAP, UNIT_MAP, QUESTION_HOME, LESSON_QUESTION_IDS, QUESTION_LEVEL, LESSON_HUE
    QUESTION_MAP = {q.id: q for q in QUESTIONS}
    UNIT_MAP = {u.id: u for u in UNITS}
    # qid -> (Unit, Lesson) ของข้อที่อยู่ในบทเรียนปกติ (ข้อที่ซ้ำหลายบทจะเก็บบทแรกที่พบ) ใช้หน้าสถิติ
    QUESTION_HOME = {}
    for u in UNITS:
        for l in u.lessons:
            for qid in l.question_ids:
                QUESTION_HOME.setdefault(qid, (u, l))
    # รหัสข้อทั้งหมดที่ใช้ในบทเรียนปกติ (ไม่รวมคลัง Challenger) - ใช้เป็นคลังสำรองของโหมดฝึกฝนฟื้นฟูหัวใจ
    LESSON_QUESTION_IDS = frozenset(QUESTION_HOME)
    QUESTION_LEVEL = _build_difficulty_levels()
    LESSON_HUE = _build_lesson_hues()
    # สีประจำ Unit = สีของบทเรียนบทกลาง (ใช้ทำป้ายชื่อ Unit ในหน้าเส้นทางการเรียน)
    for u in UNITS:
        u.bg_top, u.bg_bottom = lesson_background(u.lessons[len(u.lessons) // 2], 0)


def set_course(code) -> str:
    """เปลี่ยนคอร์สที่เรียน คืนรหัสคอร์สที่ใช้งานจริง รหัสแปลก ๆ/ค่าเสียหาย (เช่นจากไฟล์เซฟ) ถอยกลับเป็นคอร์สเริ่มต้น ไม่ crash"""
    global QUESTIONS, UNITS, CHALLENGER_QUESTION_IDS, AUTO_LEVELS, COURSE, LEARN_LANG, UI_LANG
    if not isinstance(code, str) or code not in COURSES:
        code = DEFAULT_COURSE
    if code == "th":
        from . import course_th
        data = {"QUESTIONS": course_th.QUESTIONS, "UNITS": course_th.UNITS,
                "CHALLENGER_QUESTION_IDS": course_th.CHALLENGER_QUESTION_IDS, "AUTO_LEVELS": course_th.AUTO_LEVELS}
    else:
        data = _EN_DATA
    QUESTIONS, UNITS = data["QUESTIONS"], data["UNITS"]
    CHALLENGER_QUESTION_IDS, AUTO_LEVELS = data["CHALLENGER_QUESTION_IDS"], data["AUTO_LEVELS"]
    COURSE = code
    LEARN_LANG = COURSES[code]["learn_lang"]
    UI_LANG = COURSES[code]["ui_lang"]
    _derive()
    return code


def course_of_profile(data) -> str:
    """คอร์สที่โปรไฟล์นี้เลือกไว้ (ค่าเสียหาย/ไม่มี = คอร์สเริ่มต้น)"""
    code = data.get("course") if isinstance(data, dict) else None
    return code if isinstance(code, str) and code in COURSES else DEFAULT_COURSE


def next_course(code: str) -> str:
    """คอร์สถัดไปเมื่อกดปุ่มสลับคอร์ส (วนตามลำดับใน COURSES)"""
    keys = list(COURSES)
    return keys[(keys.index(code) + 1) % len(keys)] if code in keys else DEFAULT_COURSE


def detect_lang(text: str):
    """ภาษาของข้อความสำหรับเลือกเสียง TTS: "th" ถ้ามีอักษรไทย, "en" ถ้าเป็น ASCII ล้วน, ไม่งั้น None"""
    if any("\u0e00" <= ch <= "\u0e7f" for ch in text):
        return "th"
    return "en" if text and text.isascii() else None


_derive()
