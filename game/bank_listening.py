"""
bank_listening.py
-----------------
โจทย์ "ฟังแล้วตอบ" (listening) สำหรับโหมดปกติ รวม 60 ข้อ (รหัส l1 - l60) บทละ 4 ข้อ ต่อท้ายข้อเดิมของทุกบท
ทำให้ทุกบทมี 14 ข้อ (เดิม 10) เกมจะอ่านข้อความภาษาอังกฤษใน audio_text ออกเสียงให้ฟังเอง ผู้เล่นกดฟังซ้ำได้ไม่จำกัด

ชนิดโจทย์ (บทละ 4 ข้อ ตามลำดับนี้):
  1. listen_mcq  ฟังแล้ว "เลือกคำ/ประโยคที่ได้ยิน"   ตัวเลือกเป็นภาษาอังกฤษ  correct_answer = audio_text
  2. listen_mcq  ฟังแล้ว "เลือกความหมาย"            ตัวเลือกเป็นภาษาไทย    correct_answer = ความหมายภาษาไทย
  3. listen_type ฟังแล้ว "พิมพ์ตามที่ได้ยิน" (dictation)                  correct_answer = audio_text
  4. listen_type ฟังแล้ว "พิมพ์ตามที่ได้ยิน"

หลักการเขียนโจทย์ฟัง (สำคัญ - TTS อ่านเสียงอย่างเดียว แยกตัวสะกดไม่ได้):
  - ห้ามใช้คำพ้องเสียงเป็นคำตอบหรือตัวเลือก (two/to/too, no/know, one/won, four/for, eight/ate ฯลฯ)
  - ตัวเลือกต้อง "ฟังแล้วต่างกันชัด" ไม่ใช่แค่สะกดต่างกัน
  - ข้อพิมพ์ตามที่ได้ยิน ถ้ามีตัวเลขให้ใส่ alt_answers เป็นตัวเลขอารบิกด้วย
  - ตัวโจทย์ (prompt) เป็นแค่คำสั่งสั้น ๆ ห้ามบอกคำตอบ เพราะเกมจะไม่อ่านโจทย์ออกเสียง
  - ถ้าเครื่องเล่นเสียงไม่ได้ (ปิดเสียง/ไม่มี TTS) หน้าจอจะโชว์ audio_text เป็นข้อความแทน ผู้เล่นจะได้ไม่ติดตอบไม่ได้
"""

from .models import Question

P_CHOOSE = "ฟังแล้วเลือกคำที่ได้ยิน"
P_MEANING = "ฟังแล้วเลือกความหมายที่ถูกต้อง"
P_TYPE = "ฟังแล้วพิมพ์สิ่งที่ได้ยิน"


def _lm(qid, audio, options, expl, vocab=None):
    """ฟังแล้วเลือกคำที่ได้ยิน (ตัวเลือกอังกฤษ)"""
    return Question(qid, "listen_mcq", P_CHOOSE, audio, options=options, explanation=expl,
                    vocab=vocab, audio_text=audio)


def _lmt(qid, audio, answer_th, options, expl, vocab=None):
    """ฟังแล้วเลือกความหมายภาษาไทย (ตัวเลือกไทย)"""
    return Question(qid, "listen_mcq", P_MEANING, answer_th, options=options, explanation=expl,
                    vocab=vocab, audio_text=audio)


def _lt(qid, audio, expl, alt=None, vocab=None):
    """ฟังแล้วพิมพ์ตามที่ได้ยิน (dictation)"""
    return Question(qid, "listen_type", P_TYPE, audio, alt_answers=alt or [], explanation=expl,
                    vocab=vocab, audio_text=audio)


LISTENING_QUESTIONS = [
    # ===================== Unit 1: Greetings =====================
    # u1l1 ทักทายง่าย ๆ
    _lm("l1", "Hello", ["Hello", "Goodbye", "Welcome", "Sorry"], '"Hello" แปลว่า สวัสดี', "Hello"),
    _lmt("l2", "Goodbye", "ลาก่อน", ["ลาก่อน", "สวัสดี", "ขอบคุณ", "ขอโทษ"], '"Goodbye" แปลว่า ลาก่อน', "Goodbye"),
    _lt("l3", "Nice to meet you", '"Nice to meet you" แปลว่า ยินดีที่ได้รู้จัก', vocab="Nice to meet you"),
    _lt("l4", "See you tomorrow", '"See you tomorrow" แปลว่า เจอกันพรุ่งนี้', vocab="See you tomorrow"),
    # u1l2 สวัสดีตอนเช้า
    _lm("l5", "Good morning", ["Good morning", "Good afternoon", "Good evening", "Good night"],
        '"Good morning" แปลว่า สวัสดีตอนเช้า', "Good morning"),
    _lmt("l6", "Good night", "ราตรีสวัสดิ์",
         ["สวัสดีตอนเช้า", "สวัสดีตอนบ่าย", "สวัสดีตอนเย็น", "ราตรีสวัสดิ์"], '"Good night" แปลว่า ราตรีสวัสดิ์', "Good night"),
    _lt("l7", "Good afternoon", '"Good afternoon" แปลว่า สวัสดีตอนบ่าย', vocab="Good afternoon"),
    _lt("l8", "How are you", '"How are you" แปลว่า คุณสบายดีไหม', vocab="How are you"),
    # u1l3 ขอบคุณและขอโทษ
    _lm("l9", "Thank you", ["Thank you", "Sorry", "Excuse me", "Please"], '"Thank you" แปลว่า ขอบคุณ', "Thank you"),
    _lmt("l10", "Excuse me", "ขอทางหน่อย", ["ขอทางหน่อย", "ขอบคุณมาก", "ไม่เป็นไร", "ยินดีต้อนรับ"],
         '"Excuse me" ใช้ขอทางหรือขอเรียกความสนใจอย่างสุภาพ', "Excuse me"),
    _lt("l11", "I am sorry", '"I am sorry" แปลว่า ฉันขอโทษ', vocab="Sorry"),
    _lt("l12", "Thank you very much", '"Thank you very much" แปลว่า ขอบคุณมาก', vocab="Thank you very much"),

    # ===================== Unit 2: Introductions =====================
    # u2l1 บอกชื่อตัวเอง
    _lm("l13", "My name is Anna", ["My name is Anna", "My name is Emma", "My name is Linda", "My name is Sara"],
        'ประโยคที่ได้ยินคือ "My name is Anna" (ฉันชื่อแอนนา)', "My name is"),
    _lmt("l14", "What is your name", "คุณชื่ออะไร", ["คุณชื่ออะไร", "คุณมาจากไหน", "คุณอายุเท่าไร", "คุณสบายดีไหม"],
         '"What is your name" แปลว่า คุณชื่ออะไร', "What is your name"),
    _lt("l15", "I am Tom", '"I am Tom" แปลว่า ฉันคือทอม', alt=["Im Tom"]),
    _lt("l16", "This is my friend", '"This is my friend" แปลว่า นี่คือเพื่อนของฉัน', vocab="Friend"),
    # u2l2 ถามที่มา
    _lm("l17", "England", ["England", "Thailand", "Japan", "China"], '"England" แปลว่า ประเทศอังกฤษ', "England"),
    _lmt("l18", "Where are you from", "คุณมาจากไหน", ["คุณมาจากไหน", "คุณชื่ออะไร", "คุณอายุเท่าไร", "คุณทำอะไร"],
         '"Where are you from" แปลว่า คุณมาจากไหน', "Where are you from"),
    _lt("l19", "I am from Thailand", '"I am from Thailand" แปลว่า ฉันมาจากประเทศไทย', vocab="Thailand"),
    _lt("l20", "She is from Japan", '"She is from Japan" แปลว่า เธอมาจากญี่ปุ่น', vocab="Japan"),
    # u2l3 ถามอายุ
    _lm("l21", "fifteen", ["fifteen", "fifty", "fourteen", "sixteen"], '"Fifteen" คือ 15 (สิบห้า)', "Fifteen"),
    _lmt("l22", "How old are you", "คุณอายุเท่าไร", ["คุณอายุเท่าไร", "คุณมาจากไหน", "คุณชื่ออะไร", "คุณสบายดีไหม"],
         '"How old are you" แปลว่า คุณอายุเท่าไร', "How old are you"),
    _lt("l23", "I am twelve years old", '"I am twelve years old" แปลว่า ฉันอายุสิบสองปี',
        alt=["I am 12 years old", "I am 12"], vocab="Twelve"),
    _lt("l24", "thirteen", '"Thirteen" คือ 13 (สิบสาม)', alt=["13"], vocab="Thirteen"),

    # ===================== Unit 3: Family =====================
    # u3l1 พ่อแม่
    _lm("l25", "mother", ["mother", "father", "brother", "sister"], '"Mother" แปลว่า แม่', "Mother"),
    _lmt("l26", "grandfather", "ปู่ หรือ ตา", ["ปู่ หรือ ตา", "ย่า หรือ ยาย", "ลุง หรือ อา", "พี่ชาย"],
         '"Grandfather" แปลว่า ปู่ หรือ ตา', "Grandfather"),
    _lt("l27", "This is my father", '"This is my father" แปลว่า นี่คือพ่อของฉัน', vocab="Father"),
    _lt("l28", "I love my parents", '"I love my parents" แปลว่า ฉันรักพ่อแม่ของฉัน', vocab="Parents"),
    # u3l2 พี่น้อง
    _lm("l29", "brother", ["brother", "mother", "sister", "father"], '"Brother" แปลว่า พี่ชายหรือน้องชาย', "Brother"),
    _lmt("l30", "older sister", "พี่สาว", ["พี่สาว", "น้องสาว", "พี่ชาย", "น้องชาย"],
         '"Older sister" แปลว่า พี่สาว', "Older sister"),
    _lt("l31", "She is my older sister", '"She is my older sister" แปลว่า เธอคือพี่สาวของฉัน', vocab="Older sister"),
    _lt("l32", "I have one brother", '"I have one brother" แปลว่า ฉันมีพี่ชายหรือน้องชายหนึ่งคน', alt=["I have 1 brother"]),
    # u3l3 สมาชิกครอบครัว
    _lm("l33", "daughter", ["daughter", "son", "sister", "aunt"], '"Daughter" แปลว่า ลูกสาว', "Daughter"),
    _lmt("l34", "My family is big", "ครอบครัวของฉันใหญ่",
         ["ครอบครัวของฉันใหญ่", "ครอบครัวของฉันเล็ก", "ครอบครัวของฉันมีความสุข", "ครอบครัวของฉันอยู่ไกล"],
         '"My family is big" แปลว่า ครอบครัวของฉันใหญ่', "Big"),
    _lt("l35", "I have three sisters", '"I have three sisters" แปลว่า ฉันมีพี่สาวหรือน้องสาวสามคน',
        alt=["I have 3 sisters"]),
    _lt("l36", "I have a big family", '"I have a big family" แปลว่า ฉันมีครอบครัวใหญ่', vocab="Family"),

    # ===================== Unit 4: Food and Drinks =====================
    # u4l1 อาหารพื้นฐาน
    _lm("l37", "rice", ["rice", "milk", "egg", "fish"], '"Rice" แปลว่า ข้าว', "Rice"),
    _lmt("l38", "water", "น้ำ", ["น้ำ", "นม", "ชา", "น้ำผลไม้"], '"Water" แปลว่า น้ำดื่ม', "Water"),
    _lt("l39", "I eat rice and fish", '"I eat rice and fish" แปลว่า ฉันกินข้าวกับปลา'),
    _lt("l40", "I drink milk", '"I drink milk" แปลว่า ฉันดื่มนม', vocab="Milk"),
    # u4l2 รู้สึกหิว-กระหาย
    _lm("l41", "hungry", ["hungry", "thirsty", "angry", "happy"], '"Hungry" แปลว่า หิวข้าว', "Hungry"),
    _lmt("l42", "I am thirsty", "ฉันหิวน้ำ", ["ฉันหิวน้ำ", "ฉันหิวข้าว", "ฉันอิ่มแล้ว", "ฉันง่วงนอน"],
         '"Thirsty" แปลว่า หิวน้ำ', "Thirsty"),
    _lt("l43", "I am hungry", '"I am hungry" แปลว่า ฉันหิวข้าว', vocab="Hungry"),
    _lt("l44", "Are you thirsty", '"Are you thirsty" แปลว่า คุณหิวน้ำไหม', vocab="Thirsty"),
    # u4l3 ผลไม้โปรด
    _lm("l45", "banana", ["banana", "apple", "orange", "mango"], '"Banana" แปลว่า กล้วย', "Banana"),
    _lmt("l46", "strawberry", "สตรอว์เบอร์รี", ["สตรอว์เบอร์รี", "องุ่น", "แตงโม", "มะม่วง"],
         '"Strawberry" แปลว่า สตรอว์เบอร์รี', "Strawberry"),
    _lt("l47", "I like mango", '"I like mango" แปลว่า ฉันชอบมะม่วง', vocab="Mango"),
    _lt("l48", "My favorite fruit is apple", '"My favorite fruit is apple" แปลว่า ผลไม้โปรดของฉันคือแอปเปิล',
        alt=["My favorite fruit is an apple", "My favourite fruit is apple", "My favourite fruit is an apple"]),

    # ===================== Unit 5: Daily Activities =====================
    # u5l1 ตื่นเช้า
    _lm("l49", "I brush my teeth",
        ["I brush my teeth", "I wash my face", "I eat breakfast", "I go to school"],
        'ประโยคที่ได้ยินคือ "I brush my teeth" (ฉันแปรงฟัน)', "Brush teeth"),
    _lmt("l50", "I wake up at six", "ฉันตื่นนอนตอนหกโมง",
         ["ฉันตื่นนอนตอนหกโมง", "ฉันตื่นนอนตอนเจ็ดโมง", "ฉันเข้านอนตอนหกโมง", "ฉันกินข้าวตอนหกโมง"],
         '"I wake up at six" แปลว่า ฉันตื่นนอนตอนหกโมง', "Wake up"),
    _lt("l51", "I wake up early", '"I wake up early" แปลว่า ฉันตื่นนอนเช้า', vocab="Early"),
    _lt("l52", "I take a shower", '"I take a shower" แปลว่า ฉันอาบน้ำ', vocab="Take a shower"),
    # u5l2 ไปโรงเรียน
    _lm("l53", "teacher", ["teacher", "student", "doctor", "driver"], '"Teacher" แปลว่า ครู', "Teacher"),
    _lmt("l54", "I go to school by bus", "ฉันไปโรงเรียนโดยรถบัส",
         ["ฉันไปโรงเรียนโดยรถบัส", "ฉันไปโรงเรียนโดยรถยนต์", "ฉันไปตลาดโดยรถบัส", "ฉันกลับบ้านโดยรถบัส"],
         '"I go to school by bus" แปลว่า ฉันไปโรงเรียนโดยรถบัส', "Bus"),
    _lt("l55", "Open your book", '"Open your book" แปลว่า เปิดหนังสือของคุณ', vocab="Book"),
    _lt("l56", "She goes to school", '"She goes to school" แปลว่า เธอไปโรงเรียน', vocab="School"),
    # u5l3 การบ้านตอนเย็น
    _lm("l57", "homework", ["homework", "dinner", "bedroom", "teacher"], '"Homework" แปลว่า การบ้าน', "Homework"),
    _lmt("l58", "I go to bed at ten", "ฉันเข้านอนตอนสี่ทุ่ม",
         ["ฉันเข้านอนตอนสี่ทุ่ม", "ฉันตื่นนอนตอนสี่ทุ่ม", "ฉันเข้านอนตอนสามทุ่ม", "ฉันกินข้าวตอนสี่ทุ่ม"],
         '"I go to bed at ten" แปลว่า ฉันเข้านอนตอนสี่ทุ่ม (22:00 น.)', "Go to bed"),
    _lt("l59", "She watches TV at night", '"She watches TV at night" แปลว่า เธอดูทีวีตอนกลางคืน', vocab="Watch TV"),
    _lt("l60", "I do my homework", '"I do my homework" แปลว่า ฉันทำการบ้าน', vocab="Homework"),
]

# รหัสข้อฟังที่ต่อท้ายแต่ละบทเรียน (ต่อท้ายข้อเดิม + ข้อเพิ่มของ bank_lessons_extra.py)
LISTENING_LESSON_QUESTION_IDS = {
    lesson_id: [f"l{n}" for n in range(start, start + 4)]
    for lesson_id, start in zip(
        ["u1l1", "u1l2", "u1l3", "u2l1", "u2l2", "u2l3", "u3l1", "u3l2", "u3l3",
         "u4l1", "u4l2", "u4l3", "u5l1", "u5l2", "u5l3"],
        range(1, 61, 4))
}
