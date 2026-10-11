"""
course_th.py
------------
คอร์ส "เรียนภาษาไทย" สำหรับผู้เรียนที่ใช้ภาษาอังกฤษ (โจทย์/คำอธิบายเป็นภาษาอังกฤษ, คำตอบเป็นภาษาไทย)

เหตุผลที่โจทย์เป็นภาษาอังกฤษ: ผู้เรียนภาษาไทยคือคนที่ยังอ่านไทยไม่ออก จึงต้องสอนผ่านภาษาที่เขารู้อยู่แล้ว
(เหมือนคอร์สอังกฤษที่โจทย์เป็นภาษาไทย) ส่วนคำตอบ/ตัวเลือก/แผ่นคำเป็นอักษรไทย และมีคำอ่านแบบทับศัพท์ (romanization) กำกับ

ข้อมูลเขียนเป็นตาราง (คำไทย, คำอ่าน, ความหมาย) แล้ว "สร้างโจทย์อัตโนมัติ" ด้วยฟังก์ชันเดียวกันทุกบท
ทำให้รูปแบบสม่ำเสมอ และเพิ่มคำใหม่ได้ง่าย (ดู LESSON_DATA ด้านล่าง)
 - ไม่ใช้ข้อพิมพ์ตอบ (translate_type): การพิมพ์ภาษาไทยต้องมีคีย์บอร์ดไทย ผู้เรียนส่วนใหญ่ไม่มี
 - ใช้ข้อเลือกตอบ / เรียงคำ (แผ่นคำภาษาไทย) / ฟังแล้วเลือก (เสียงอ่านภาษาไทยจาก TTS)
"""

from typing import Dict, List, Tuple

from .models import Question, Lesson, Unit

# (id หน่วย, ชื่อหน่วย, คำอธิบายหน่วย)
UNIT_META = [
    ("tu1", "Greetings", "Say hello and be polite"),
    ("tu2", "Introductions", "Talk about yourself"),
    ("tu3", "Family", "People in your family"),
    ("tu4", "Food and Drinks", "What to eat and drink"),
    ("tu5", "Numbers and Daily Life", "Count and talk about your day"),
]

# คำศัพท์: (ไทย, คำอ่าน, ความหมายอังกฤษ)  ต้องไม่ซ้ำกันทั้งคอร์ส (มีเทสต์ตรวจ) เพื่อไม่ให้ตัวเลือกผิดกลายเป็นถูก
# วลี: (คำที่ต้องเรียงเป็นลิสต์, คำอ่าน, ความหมายอังกฤษ, คำหลอก)
LESSON_DATA: List[dict] = [
    # ----- Unit 1: Greetings -----
    dict(id="tu1l1", unit=0, title="Hello and goodbye", words=[
        ("สวัสดี", "sa-wat-dee", "Hello"), ("ลาก่อน", "laa gon", "Goodbye"),
        ("ขอบคุณ", "khop khun", "Thank you"), ("ขอโทษ", "kho thot", "Sorry"),
        ("ไม่เป็นไร", "mai pen rai", "No problem"), ("ใช่", "chai", "Yes"),
        ("ไม่ใช่", "mai chai", "No, it is not")],
        phrases=[(["สวัสดี", "ครับ"], "sa-wat-dee khrap", "Hello (said by a man)", ["ค่ะ"]),
                 (["ขอบคุณ", "ค่ะ"], "khop khun kha", "Thank you (said by a woman)", ["ครับ"])]),
    dict(id="tu1l2", unit=0, title="Polite words", words=[
        ("ครับ", "khrap", "Polite word for men"), ("ค่ะ", "kha", "Polite word for women"),
        ("กรุณา", "ga-ru-naa", "Please"), ("ยินดีต้อนรับ", "yin dee dton rap", "Welcome"),
        ("สบายดีไหม", "sa-baai dee mai", "How are you?"), ("สบายดี", "sa-baai dee", "I am fine"),
        ("ยินดีที่ได้รู้จัก", "yin dee tee dai roo jak", "Nice to meet you")],
        phrases=[(["ผม", "สบายดี", "ครับ"], "phom sa-baai dee khrap", "I am fine (said by a man)", ["ค่ะ"]),
                 (["ขอบคุณ", "ฉัน", "สบายดี", "ค่ะ"], "khop khun chan sa-baai dee kha",
                  "Thank you, I am fine (said by a woman)", ["ครับ"])]),
    dict(id="tu1l3", unit=0, title="Times of day", words=[
        ("เช้า", "chao", "Morning"), ("บ่าย", "baai", "Afternoon"), ("เย็น", "yen", "Evening"),
        ("กลางคืน", "glaang kheun", "Night"), ("วันนี้", "wan nee", "Today"),
        ("พรุ่งนี้", "phrung nee", "Tomorrow"), ("ราตรีสวัสดิ์", "raa-dtree sa-wat", "Good night")],
        phrases=[(["ราตรีสวัสดิ์", "ครับ"], "raa-dtree sa-wat khrap", "Good night (said by a man)", ["ค่ะ"]),
                 (["พรุ่งนี้", "เจอ", "กัน"], "phrung nee jer gan", "See you tomorrow", ["วันนี้"])]),
    # ----- Unit 2: Introductions -----
    dict(id="tu2l1", unit=1, title="Me and you", words=[
        ("ผม", "phom", "I (said by a man)"), ("ฉัน", "chan", "I (said by a woman)"),
        ("คุณ", "khun", "You"), ("เขา", "khao", "He or she"), ("เรา", "rao", "We"),
        ("ชื่อ", "chue", "Name"), ("อะไร", "a-rai", "What")],
        phrases=[(["ผม", "ชื่อ", "เบลซ"], "phom chue blaze", "My name is Blaze (said by a man)", ["เขา"]),
                 (["คุณ", "ชื่อ", "อะไร"], "khun chue a-rai", "What is your name?", ["เขา"])]),
    dict(id="tu2l2", unit=1, title="Where are you from?", words=[
        ("มาจาก", "maa jaak", "Come from"), ("ประเทศไทย", "bpra-thet thai", "Thailand"),
        ("อเมริกา", "a-me-ri-gaa", "America"), ("อังกฤษ", "ang-grit", "England"),
        ("ญี่ปุ่น", "yee-bpun", "Japan"), ("ที่ไหน", "tee nai", "Where"),
        ("ภาษาไทย", "paa-saa thai", "Thai language")],
        phrases=[(["คุณ", "มาจาก", "ที่ไหน"], "khun maa jaak tee nai", "Where are you from?", ["เขา"]),
                 (["ฉัน", "มาจาก", "ประเทศไทย"], "chan maa jaak bpra-thet thai", "I am from Thailand",
                  ["อเมริกา"])]),
    dict(id="tu2l3", unit=1, title="Age and jobs", words=[
        ("อายุ", "aa-yu", "Age"), ("ปี", "bpee", "Year of age"), ("นักเรียน", "nak rian", "Student"),
        ("ครู", "kroo", "Teacher"), ("หมอ", "mor", "Doctor"), ("ทำงาน", "tham ngaan", "Work"),
        ("เท่าไหร่", "tao rai", "How much")],
        phrases=[(["ผม", "เป็น", "นักเรียน"], "phom pen nak rian", "I am a student (said by a man)", ["ครู"]),
                 (["คุณ", "อายุ", "เท่าไหร่"], "khun aa-yu tao rai", "How old are you?", ["ปี"])]),
    # ----- Unit 3: Family -----
    dict(id="tu3l1", unit=2, title="Parents and home", words=[
        ("พ่อ", "phor", "Father"), ("แม่", "mae", "Mother"), ("พ่อแม่", "phor mae", "Parents"),
        ("ครอบครัว", "khrop khrua", "Family"), ("ลูก", "look", "Child"), ("รัก", "rak", "Love"),
        ("บ้าน", "baan", "House")],
        phrases=[(["ฉัน", "รัก", "แม่"], "chan rak mae", "I love my mother", ["พ่อ"]),
                 (["พ่อ", "อยู่", "บ้าน"], "phor yoo baan", "Father is at home", ["แม่"])]),
    dict(id="tu3l2", unit=2, title="Brothers and sisters", words=[
        ("พี่ชาย", "phee chaai", "Older brother"), ("พี่สาว", "phee saao", "Older sister"),
        ("น้องชาย", "nong chaai", "Younger brother"), ("น้องสาว", "nong saao", "Younger sister"),
        ("พี่น้อง", "phee nong", "Siblings"), ("เพื่อน", "phuean", "Friend"), ("มี", "mee", "Have")],
        phrases=[(["ฉัน", "มี", "น้องสาว"], "chan mee nong saao", "I have a younger sister", ["พี่สาว"]),
                 (["พี่ชาย", "ของ", "ฉัน", "เป็น", "หมอ"], "phee chaai khong chan pen mor",
                  "My older brother is a doctor", ["ครู"])]),
    dict(id="tu3l3", unit=2, title="Grandparents and relatives", words=[
        ("ปู่", "bpoo", "Grandfather (father's side)"), ("ย่า", "yaa", "Grandmother (father's side)"),
        ("ตา", "dtaa", "Grandfather (mother's side)"), ("ยาย", "yaai", "Grandmother (mother's side)"),
        ("ลุง", "lung", "Uncle (older than your parent)"), ("ป้า", "bpaa", "Aunt (older than your parent)"),
        ("หลาน", "laan", "Grandchild")],
        phrases=[(["ยาย", "รัก", "หลาน"], "yaai rak laan", "Grandma loves her grandchild", ["ย่า"]),
                 (["ปู่", "กับ", "ย่า", "อยู่", "บ้าน"], "bpoo gap yaa yoo baan",
                  "Grandpa and grandma are at home", ["ตา"])]),
    # ----- Unit 4: Food and Drinks -----
    dict(id="tu4l1", unit=3, title="Basic food", words=[
        ("ข้าว", "khao", "Rice"), ("ไก่", "gai", "Chicken"), ("หมู", "moo", "Pork"),
        ("ปลา", "bplaa", "Fish"), ("ไข่", "khai", "Egg"), ("ผัก", "phak", "Vegetables"),
        ("อาหาร", "aa-haan", "Food")],
        phrases=[(["ฉัน", "กิน", "ข้าว"], "chan gin khao", "I eat rice", ["ปลา"]),
                 (["ผม", "ชอบ", "ปลา"], "phom chop bplaa", "I like fish (said by a man)", ["ไก่"])]),
    dict(id="tu4l2", unit=3, title="Drinks and fruit", words=[
        ("น้ำ", "naam", "Water"), ("นม", "nom", "Milk"), ("ชา", "chaa", "Tea"),
        ("กาแฟ", "gaa-fae", "Coffee"), ("กล้วย", "gluay", "Banana"), ("มะม่วง", "ma-muang", "Mango"),
        ("ส้ม", "som", "Orange")],
        phrases=[(["ขอ", "น้ำ", "ครับ"], "kho naam khrap", "Water, please (said by a man)", ["ค่ะ"]),
                 (["ฉัน", "ดื่ม", "กาแฟ"], "chan deum gaa-fae", "I drink coffee", ["ชา"])]),
    dict(id="tu4l3", unit=3, title="Taste and hunger", words=[
        ("หิว", "hiu", "Hungry"), ("อิ่ม", "im", "Full"), ("อร่อย", "a-roi", "Delicious"),
        ("เผ็ด", "phet", "Spicy"), ("หวาน", "waan", "Sweet"), ("เปรี้ยว", "bpriao", "Sour"),
        ("กระหายน้ำ", "gra-haai naam", "Thirsty")],
        phrases=[(["อาหาร", "อร่อย", "มาก"], "aa-haan a-roi maak", "The food is very delicious", ["เผ็ด"]),
                 (["ผม", "ไม่", "กิน", "เผ็ด"], "phom mai gin phet", "I do not eat spicy food (said by a man)",
                  ["หวาน"])]),
    # ----- Unit 5: Numbers and Daily Life -----
    dict(id="tu5l1", unit=4, title="Numbers 0 to 5", words=[
        ("ศูนย์", "suun", "Zero"), ("หนึ่ง", "neung", "One"), ("สอง", "song", "Two"),
        ("สาม", "saam", "Three"), ("สี่", "see", "Four"), ("ห้า", "haa", "Five"), ("สิบ", "sip", "Ten")],
        phrases=[(["ห้า", "บาท"], "haa baat", "Five baht", ["สาม"]),
                 (["สาม", "คน"], "saam khon", "Three people", ["สี่"])]),
    dict(id="tu5l2", unit=4, title="Bigger numbers", words=[
        ("หก", "hok", "Six"), ("เจ็ด", "jet", "Seven"), ("แปด", "bpaet", "Eight"), ("เก้า", "gao", "Nine"),
        ("ยี่สิบ", "yee sip", "Twenty"), ("ร้อย", "roi", "Hundred"), ("พัน", "phan", "Thousand")],
        phrases=[(["เจ็ด", "โมง", "เช้า"], "jet mong chao", "Seven o'clock in the morning", ["เย็น"]),
                 (["หนึ่ง", "ร้อย", "บาท"], "neung roi baat", "One hundred baht", ["พัน"])]),
    dict(id="tu5l3", unit=4, title="Daily routine", words=[
        ("ตื่นนอน", "dteun norn", "Wake up"), ("อาบน้ำ", "aap naam", "Take a bath"),
        ("โรงเรียน", "rong rian", "School"), ("ไป", "bpai", "Go"), ("กลับ", "glap", "Return"),
        ("นอน", "norn", "Sleep"), ("เวลา", "we-laa", "Time")],
        phrases=[(["วันนี้", "ฉัน", "ไป", "โรงเรียน"], "wan nee chan bpai rong rian",
                  "Today I go to school", ["กลับ"]),
                 (["ผม", "กลับ", "บ้าน", "ตอน", "เย็น"], "phom glap baan dton yen",
                  "I go home in the evening (said by a man)", ["เช้า"])]),
]


def _pick_distractors(correct: str, pool: List[str], start: int, n: int = 3) -> List[str]:
    """เลือกตัวเลือกหลอกแบบกำหนดตายตัว (ไม่สุ่ม ตอน import) จากตำแหน่ง start วนไปในพูล ไม่ซ้ำและไม่ใช่คำตอบ"""
    out: List[str] = []
    i = 0
    while len(out) < n and i < len(pool) * 2:
        cand = pool[(start + i) % len(pool)]
        if cand != correct and cand not in out:
            out.append(cand)
        i += 1
    return out


def _options(correct: str, pool: List[str], base: int, shift: int) -> List[str]:
    """ตัวเลือก 4 ข้อ: เฉลย + ตัวหลอก 3 ตัวที่อยู่ถัดจากคำนี้ในพูล (ส่วนใหญ่เป็นคำหัวข้อเดียวกัน)
    ตำแหน่งเฉลยหลากหลายตาม shift (ตอนเล่นจริงเกมสลับตำแหน่งอีกชั้น)"""
    opts = _pick_distractors(correct, pool, base + 1 + shift)
    opts.insert(shift % (len(opts) + 1), correct)
    return opts


def _build() -> Tuple[List[Question], List[Unit]]:
    all_words = [w for lesson in LESSON_DATA for w in lesson["words"]]
    questions: List[Question] = []
    units = [Unit(uid, title, sub, []) for uid, title, sub in UNIT_META]
    for lesson in LESSON_DATA:
        words = lesson["words"]
        # พูลตัวเลือกหลอก: คำในหน่วยเดียวกันก่อน (ยากขึ้น เพราะคล้ายหัวข้อกัน) ตามด้วยคำนอกหน่วย
        same_unit = [w for ln in LESSON_DATA if ln["unit"] == lesson["unit"] for w in ln["words"]]
        others = [w for w in all_words if w not in same_unit]
        pool = same_unit + others
        n = [0]

        def qid():
            n[0] += 1
            return f"{lesson['id']}_{n[0]:02d}"

        def th_en(k):
            th, rom, en = words[k]
            pool_en = [w[2] for w in pool]
            return Question(qid(), "mcq", f'What does "{th}" ({rom}) mean?', en,
                            options=_options(en, pool_en, pool_en.index(en), k), prompt_lang="en", audio_text=th,
                            explanation=f'"{th}" ({rom}) means "{en}".', vocab=th)

        def en_th(k):
            th, rom, en = words[k]
            pool_th = [w[0] for w in pool]
            return Question(qid(), "mcq", f'How do you say "{en}" in Thai?', th,
                            options=_options(th, pool_th, pool_th.index(th), k + 1), prompt_lang="en",
                            explanation=f'"{en}" is "{th}" ({rom}) in Thai.', vocab=th)

        def listen_meaning(k):
            th, rom, en = words[k]
            pool_en = [w[2] for w in pool]
            return Question(qid(), "listen_mcq", "Listen and choose the meaning.", en,
                            options=_options(en, pool_en, pool_en.index(en), k + 2), prompt_lang="en", audio_text=th,
                            explanation=f'You heard "{th}" ({rom}), which means "{en}".', vocab=th)

        def listen_word(k):
            th, rom, en = words[k]
            pool_th = [w[0] for w in pool]
            return Question(qid(), "listen_mcq", "Listen and choose the word you hear.", th,
                            options=_options(th, pool_th, pool_th.index(th), k + 3), prompt_lang="en", audio_text=th,
                            explanation=f'You heard "{th}" ({rom}), which means "{en}".', vocab=th)

        def phrase(k):
            tokens, rom, en, extra = lesson["phrases"][k]
            bank = list(tokens) + list(extra)
            # สลับลำดับแผ่นคำแบบกำหนดตายตัวให้ไม่เรียงตามเฉลย (ตอนเล่นจริงเกมสุ่มซ้ำอีกที)
            bank = bank[1:] + bank[:1]
            return Question(qid(), "word_order", f'Put the words in order: "{en}"', " ".join(tokens),
                            word_bank=bank, prompt_lang="en", audio_text=" ".join(tokens),
                            explanation=f'{" ".join(tokens)} ({rom}) = "{en}"', vocab=" ".join(tokens))

        seq = [th_en(0), th_en(1), en_th(0), th_en(2), th_en(3), listen_meaning(2), th_en(4), phrase(0),
               th_en(5), en_th(3), th_en(6), listen_word(4), en_th(6), phrase(1)]
        questions.extend(seq)
        units[lesson["unit"]].lessons.append(Lesson(lesson["id"], lesson["title"], [q.id for q in seq]))
    return questions, units


QUESTIONS, UNITS = _build()
CHALLENGER_QUESTION_IDS = frozenset()   # คอร์สนี้ใช้โจทย์บทเรียนทั้งหมดเป็นคลังของโหมด Challenger (แบ่ง 10 ระดับอัตโนมัติ)
AUTO_LEVELS = 10
