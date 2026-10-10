"""
bank_challenger.py
------------------
คลังโจทย์ "เฉพาะโหมด Challenger" ระดับ 4-10 รวม 77 ข้อ (รหัส c1 - c77) ไม่อยู่ในบทเรียนปกติ
ทุกข้อกำหนด difficulty เอง ไล่จากง่ายไปยากตามระดับภาษา CEFR คร่าว ๆ:

    ระดับ 4  Pre-Intermediate        (A2+)  past simple, เปรียบเทียบ, คำบุพบท, countable/uncountable   (c1  - c10)
    ระดับ 5  Intermediate            (B1)   present perfect, conditional 1, passive, phrasal verbs      (c11 - c20)
    ระดับ 6  Upper-Intermediate      (B1+)  conditional 2, reported speech, relative clause, gerund      (c21 - c30)
    ระดับ 7  Advanced                (B2)   conditional 3, past perfect, linking words, collocation      (c31 - c40)
    ระดับ 8  Expert                  (B2+)  subjunctive, inversion, passive แบบทางการ, idioms           (c41 - c50, c77)
    ระดับ 9  Master                  (C1)   หาข้อผิด, สำนวน/ศัพท์ขั้นสูง, โครงสร้างประโยคซับซ้อน        (c51 - c60, c75)
    ระดับ 10 Legend                  (C2)   ศัพท์หายาก, สำนวนลึก, ไวยากรณ์เชิงวรรณกรรม                 (c61 - c74, c76)

ระดับ 1-3 ของโหมด Challenger ใช้โจทย์บทเรียนปกติ (คำนวณอัตโนมัติ ดู content.py)

หมายเหตุสำหรับคนเพิ่มโจทย์:
  - mcq ต้องมีคำตอบที่ถูก "ข้อเดียว" ชัดเจน (เลี่ยงตัวเลือกที่ถูกได้สองแบบ)
  - translate_type ต้องมีคำตอบเดียว หรือใส่ alt_answers ให้ครบทุกแบบที่ถูก
  - word_order ถ้าเรียงได้หลายแบบที่ถูก ต้องใส่ alt_answers ด้วย และไม่ควรเกิน 8 คำ
"""

from .models import Question


def _q(qid, qtype, prompt, answer, level, explanation, options=None, word_bank=None, alt=None, vocab=None):
    """ตัวช่วยสร้างโจทย์ Challenger (ทุกข้อเป็นโจทย์อังกฤษ, กำหนดระดับความยากเอง)"""
    return Question(qid, qtype, prompt, answer, options=options or [], word_bank=word_bank or [],
                    explanation=explanation, vocab=vocab, alt_answers=alt or [], prompt_lang="en",
                    difficulty=level)


CHALLENGER_QUESTIONS = [
    # =====================================================================
    # ระดับ 4 - Pre-Intermediate (A2+)
    # =====================================================================
    _q("c1", "mcq", "Choose the correct past tense: Yesterday I ____ to the market.", "went", 4,
       '"Go" is irregular: go - went - gone (ไป)',
       options=["went", "go", "goes", "gone"]),
    _q("c2", "mcq", "Complete: She is ____ than her sister. (tall)", "taller", 4,
       'Short adjective + -er + than: taller than (สูงกว่า)',
       options=["taller", "tallest", "more tall", "tall"]),
    _q("c3", "translate_type", "Type the past tense: Last night we ______ (eat) pizza.", "ate", 4,
       '"Eat" is irregular: eat - ate - eaten (กิน)'),
    _q("c4", "mcq", "Choose the correct preposition: The meeting is ____ Monday.", "on", 4,
       'Use "on" with days: on Monday (ในวันจันทร์)',
       options=["on", "in", "at", "by"]),
    _q("c5", "word_order", "Put the words in order to ask about yesterday.", "Where did you go yesterday", 4,
       'Past question: Where + did + subject + base verb (เมื่อวานไปไหนมา)',
       word_bank=["did", "Where", "you", "go", "yesterday", "went"]),
    _q("c6", "mcq", "Choose the correct sentence.", "There isn't any milk", 4,
       'Negatives use "any", not "some": There isn\'t any milk (ไม่มีนมเลย)',
       options=["There isn't any milk", "There isn't some milk", "There aren't any milk", "There not any milk"]),
    _q("c7", "translate_type", "Type the missing word: How ______ water do you drink every day?", "much", 4,
       'Water is uncountable, so use "How much" (น้ำนับไม่ได้)'),
    _q("c8", "mcq", "Which word means the opposite of \"expensive\"?", "cheap", 4,
       '"Cheap" is the opposite of "expensive" (ถูก ตรงข้ามกับ แพง)',
       options=["cheap", "heavy", "empty", "quiet"]),
    _q("c9", "mcq", "Complete: You ____ park here. It is not allowed.", "mustn't", 4,
       '"Mustn\'t" = it is forbidden (ห้ามทำ)',
       options=["mustn't", "must", "may", "need"]),
    _q("c10", "word_order", "Put the words in order to compare two cities.", "This city is bigger than mine", 4,
       'Comparative + than: bigger than (ใหญ่กว่า)',
       word_bank=["bigger", "This", "city", "is", "than", "mine", "biggest"],
       alt=["Mine is bigger than this city"]),

    # =====================================================================
    # ระดับ 5 - Intermediate (B1)
    # =====================================================================
    _q("c11", "mcq", "Complete: I ____ never been to Japan.", "have", 5,
       'Present perfect: have/has + past participle (ไม่เคยไป)',
       options=["have", "has", "am", "did"]),
    _q("c12", "translate_type", "Type the correct form: She has already ______ (finish) her work.", "finished", 5,
       'Present perfect = has/have + past participle: has finished'),
    _q("c13", "mcq", "Complete the first conditional: If it rains tomorrow, we ____ at home.", "will stay", 5,
       'If + present simple, will + base verb (ถ้าฝนตก เราจะอยู่บ้าน)',
       options=["will stay", "would stay", "stayed", "staying"]),
    _q("c14", "mcq", "Choose the correct phrasal verb: Please ____ the light. It's too bright.", "turn off", 5,
       '"Turn off" = stop a light or machine (ปิด)',
       options=["turn off", "turn on", "turn up", "turn into"]),
    _q("c15", "word_order", "Put the words in order to ask about experience.", "Have you ever eaten sushi", 5,
       'Have you ever + past participle? (เคยกินซูชิไหม)',
       word_bank=["Have", "you", "ever", "eaten", "sushi", "ate"]),
    _q("c16", "mcq", "Choose the correct sentence.", "I was reading when she called", 5,
       'Past continuous (was reading) + past simple (called) (กำลังอ่านตอนที่เธอโทรมา)',
       options=["I was reading when she called", "I read when she was calling",
                "I am reading when she called", "I reading when she called"]),
    _q("c17", "mcq", "Complete the passive: This bridge ____ in 1998.", "was built", 5,
       'Passive past: was/were + past participle (ถูกสร้าง)',
       options=["was built", "built", "is built", "has built"]),
    _q("c18", "translate_type", "Type the missing word: I haven't seen him ______ last Friday.", "since", 5,
       '"Since" + a point in time (ตั้งแต่ วันศุกร์ที่แล้ว)'),
    _q("c19", "mcq", "Which sentence uses \"used to\" correctly?", "I used to play football every weekend", 5,
       '"Used to" + base verb = a past habit (เคยทำ)',
       options=["I used to play football every weekend", "I used to playing football every weekend",
                "I use to play football every weekend", "I am used to play football every weekend"]),
    _q("c20", "mcq", "Choose the best word: There are ____ people in the room, so it is very crowded.", "a lot of", 5,
       '"A lot of" works with plural nouns in positive sentences (มากมาย)',
       options=["a lot of", "a little", "much", "any"]),

    # =====================================================================
    # ระดับ 6 - Upper-Intermediate (B1+)
    # =====================================================================
    _q("c21", "mcq", "Complete the second conditional: If I ____ you, I would apologize.", "were", 6,
       'Second conditional: If + past (were), would + verb (ถ้าฉันเป็นคุณ)',
       options=["were", "am", "will be", "have been"]),
    _q("c22", "translate_type", "Type the correct form: He said that he ______ (be) tired.", "was", 6,
       'Reported speech shifts the tense back: is -> was',
       alt=["had been"]),
    _q("c23", "mcq", "Complete: The woman ____ lives next door is a doctor.", "who", 6,
       '"Who" is the subject relative pronoun for people (ผู้หญิงที่อาศัยอยู่)',
       options=["who", "which", "whose", "whom"]),
    _q("c24", "mcq", "Complete: She enjoys ____ novels in her free time.", "reading", 6,
       '"Enjoy" is followed by the -ing form (enjoy reading)',
       options=["reading", "to read", "read", "reads"]),
    _q("c25", "word_order", "Put the words in order to make a polite request.", "Could you tell me the time", 6,
       'Polite request: Could you + base verb (ช่วยบอกเวลาได้ไหม)',
       word_bank=["Could", "you", "tell", "me", "the", "time", "told"]),
    _q("c26", "mcq", "Complete: I wish I ____ more free time.", "had", 6,
       '"Wish" + past simple talks about an unreal present (ถ้าฉันมี...)',
       options=["had", "have", "would have", "will have"]),
    _q("c27", "translate_type", "Type the missing word: The report must ______ finished by Friday.", "be", 6,
       'Passive with a modal: must + be + past participle'),
    _q("c28", "mcq", "Complete: He decided ____ the job offer.", "to accept", 6,
       '"Decide" is followed by a to-infinitive (decide to accept)',
       options=["to accept", "accepting", "accept", "accepted"]),
    _q("c29", "mcq", "Choose the sentence with the correct word order.", "She asked me where I lived", 6,
       'In reported questions, use normal word order (no did): where I lived',
       options=["She asked me where I lived", "She asked me where did I live",
                "She asked me where I did live", "She asked me where lived I"]),
    _q("c30", "mcq", "Choose the word closest in meaning to \"huge\".", "enormous", 6,
       '"Enormous" means very, very big (ใหญ่โตมาก)',
       options=["enormous", "tiny", "ordinary", "rapid"]),

    # =====================================================================
    # ระดับ 7 - Advanced (B2)
    # =====================================================================
    _q("c31", "mcq", "Complete the third conditional: If she had studied harder, she ____ the exam.", "would have passed",
       7, 'Third conditional: If + past perfect, would have + past participle',
       options=["would have passed", "would pass", "will pass", "had passed"]),
    _q("c32", "translate_type", "Type the correct form: When we got there, the film had already ______ (begin).",
       "begun", 7, 'Past perfect: had + past participle. begin - began - begun'),
    _q("c33", "mcq", "Choose the correct linking word: ____ it was raining, we went for a walk.", "Although", 7,
       '"Although" shows contrast (แม้ว่า)',
       options=["Although", "Because", "So", "Unless"]),
    _q("c34", "mcq", "Complete: She is really good ____ solving problems.", "at", 7,
       'The adjective "good" goes with "at": good at (เก่งใน...)',
       options=["at", "in", "on", "for"]),
    _q("c35", "mcq", "Complete: I'm not used to ____ up so early.", "getting", 7,
       '"Be used to" is followed by -ing (ไม่คุ้นกับการ...)',
       options=["getting", "get", "got", "gets"]),
    _q("c36", "word_order", "Put the words in order to express regret.", "I should have called you", 7,
       'should have + past participle = regret about the past (น่าจะโทรหาคุณ)',
       word_bank=["I", "should", "have", "called", "you", "calling"]),
    _q("c37", "translate_type", "Type the missing word: Hardly had I sat down ______ the phone rang.", "when", 7,
       'Inversion with "Hardly had ... when/before ..."',
       alt=["before"]),
    _q("c38", "mcq", "Choose the correct verb: She ____ a lot of money by selling her art.", "made", 7,
       'Collocation: make money (หาเงิน)',
       options=["made", "did", "took", "gave"]),
    _q("c39", "mcq", "Choose the sentence that is grammatically correct.", "The number of visitors has increased", 7,
       '"The number of" takes a singular verb (has), "a number of" takes plural',
       options=["The number of visitors has increased", "The number of visitors have increased",
                "A number of visitors has increased", "The numbers of visitor has increased"]),
    _q("c40", "mcq", "Choose the word closest in meaning to \"reluctant\".", "unwilling", 7,
       '"Reluctant" = not wanting to do something (ไม่เต็มใจ)',
       options=["unwilling", "eager", "delighted", "careless"]),

    # =====================================================================
    # ระดับ 8 - Expert (B2+)
    # =====================================================================
    _q("c41", "mcq", "Complete: It is essential that he ____ on time.", "be", 8,
       'Subjunctive after "essential that": base form (be), not "is"',
       options=["be", "is", "will be", "was"]),
    _q("c42", "word_order", "Put the words in order to report a rumour.", "The suspect is said to have left", 8,
       'Passive reporting: is said to have + past participle (ว่ากันว่า...ได้ออกไปแล้ว)',
       word_bank=["The", "suspect", "is", "said", "to", "have", "left"]),
    _q("c43", "translate_type", "Type the missing word: He told a joke to break the ______ at the party.", "ice", 8,
       'Idiom: break the ice = ทำลายความอึดอัดตอนเริ่มพูดคุย'),
    _q("c44", "mcq", "Complete: Not only ____ late, but he also forgot the documents.", "was he", 8,
       'Negative adverbial at the start causes inversion: Not only was he ...',
       options=["was he", "he was", "did he", "he is"]),
    _q("c45", "translate_type", "Type the correct form: Having ______ (complete) the report, she went home.",
       "completed", 8, 'Perfect participle clause: Having + past participle'),
    _q("c46", "translate_type", "Type the missing word: It was the manager ______ made the final decision.", "who", 8,
       'Cleft sentence: It was + noun + who ...', alt=["that"]),
    _q("c47", "mcq", "Which word is the most formal synonym of \"get\" in \"get a visa\"?", "obtain", 8,
       '"Obtain" is a formal word for "get" (ได้รับ)',
       options=["obtain", "grab", "catch", "borrow"]),
    _q("c48", "mcq", "Choose the best option: Had I known about the traffic, I ____ earlier.", "would have left", 8,
       'Inverted third conditional: Had I known = If I had known',
       options=["would have left", "would leave", "had left", "left"]),
    _q("c49", "mcq", "\"The deal fell through.\" What does it mean?", "It did not happen", 8,
       'Phrasal verb: fall through = fail to happen (ล้มเหลว)',
       options=["It did not happen", "It was signed quickly", "It became cheaper", "It was discussed again"]),
    _q("c50", "translate_type", "Type the missing word: She is in charge ______ the new project.", "of", 8,
       'Fixed phrase: in charge of (รับผิดชอบ)'),

    # =====================================================================
    # ระดับ 9 - Master (C1)
    # =====================================================================
    _q("c51", "mcq", "Find the mistake: \"Despite of the rain, we enjoyed the trip.\"", "Despite of", 9,
       'Correct: "Despite the rain" or "In spite of the rain" (ไม่มี of หลัง despite)',
       options=["Despite of", "the rain", "we enjoyed", "the trip"]),
    _q("c52", "mcq", "Choose the best word: Her argument was so ____ that nobody could disagree.", "compelling", 9,
       '"Compelling" = very convincing (น่าเชื่อถือมาก)',
       options=["compelling", "shallow", "vague", "tedious"]),
    _q("c53", "translate_type", "Type the correct form: Little ______ (do) she know that a surprise was waiting.",
       "did", 9, 'Inversion after "Little": Little did she know ...'),
    _q("c54", "mcq", "Choose the correct formal sentence.", "Should you need any help, please contact us", 9,
       'Formal inversion: Should you need = If you should need',
       options=["Should you need any help, please contact us", "Should you will need any help, please contact us",
                "If should you need help, contact us", "Should you needed any help, please contact us"]),
    _q("c55", "mcq", "What does \"ubiquitous\" mean?", "found everywhere", 9,
       '"Ubiquitous" = seen or present everywhere (มีอยู่ทุกหนแห่ง)',
       options=["found everywhere", "extremely rare", "very expensive", "hard to see"]),
    _q("c56", "word_order", "Put the words in order to start a formal complaint.",
       "I am writing to express my dissatisfaction", 9,
       'A formal letter opening (ขอแสดงความไม่พอใจ)',
       word_bank=["I", "am", "writing", "to", "express", "my", "dissatisfaction"]),
    _q("c57", "translate_type", "Type the missing word: Nobody wants to discuss the money problem. It is the ______ in the room.",
       "elephant", 9, 'Idiom: the elephant in the room = an obvious problem everyone ignores'),
    _q("c58", "mcq", "Choose the best word: The new policy will have far-reaching ____ for small businesses.",
       "implications", 9, '"Far-reaching implications" = wide consequences (ผลกระทบวงกว้าง)',
       options=["implications", "invitations", "inhabitants", "indications"]),
    _q("c59", "translate_type", "Type the missing word: Not until she opened the letter ______ she realise what had happened.",
       "did", 9, 'Inversion after "Not until": ... did she realise'),
    _q("c60", "mcq", "Choose the sentence with correct parallel structure.", "She likes hiking, swimming, and cycling", 9,
       'Keep the same form in a list: hiking, swimming, cycling',
       options=["She likes hiking, swimming, and cycling", "She likes hiking, to swim, and cycling",
                "She likes to hike, swimming, and to cycle", "She likes hiking, swimming, and to cycle"]),

    # =====================================================================
    # ระดับ 10 - Legend (C2)
    # =====================================================================
    _q("c61", "mcq", "Choose the best word: His ____ remarks offended everyone in the room.", "disparaging", 10,
       '"Disparaging" = showing that you think something is worthless (ดูถูก)',
       options=["disparaging", "laudatory", "innocuous", "eloquent"]),
    _q("c62", "translate_type", "Type the missing word: I can't decide yet, so I'm still on the ______.", "fence", 10,
       'Idiom: on the fence = undecided (ยังไม่ตัดสินใจ)'),
    _q("c63", "mcq", "Choose the correct word: The scientist's findings were ____ by further research.",
       "corroborated", 10, '"Corroborate" = confirm with more evidence (ยืนยัน)',
       options=["corroborated", "corrugated", "corroded", "coordinated"]),
    _q("c64", "translate_type", "Type the missing word: Neither the teacher nor the students ______ aware of the change. (be, present)",
       "are", 10, 'The verb agrees with the nearer subject: students -> are'),
    _q("c65", "mcq", "Which sentence is correct?", "Whoever finishes first will receive a prize", 10,
       '"Whoever" is the subject of "finishes", so not "whomever"',
       options=["Whoever finishes first will receive a prize", "Whomever finishes first will receive a prize",
                "Whoever finish first will receive a prize", "Whomever finish first will receive prize"]),
    _q("c66", "translate_type", "Type the word that means \"lasting for a very short time\". (e________)", "ephemeral", 10,
       '"Ephemeral" = short-lived (ชั่วคราว ไม่ยั่งยืน)'),
    _q("c67", "word_order", "Put the words in order to praise someone's courage.", "Rarely have I seen such courage", 10,
       'Inversion after "Rarely": Rarely have I seen ...',
       word_bank=["Rarely", "have", "I", "seen", "such", "courage", "saw"]),
    _q("c68", "mcq", "Choose the grammatically correct sentence.", "The colleague with whom I worked has resigned", 10,
       'After a preposition, use "whom": with whom',
       options=["The colleague with whom I worked has resigned", "The colleague with who I worked has resigned",
                "The colleague whom I worked with him has resigned", "The colleague which I worked with has resigned"]),
    _q("c69", "translate_type", "Type the missing word: She was o______ to the idea of moving abroad.", "opposed", 10,
       '"Opposed to" = against (คัดค้าน)'),
    _q("c70", "translate_type", "Type the missing word: Fame is a double-edged ______. It brings good and bad things.", "sword", 10,
       'Idiom: a double-edged sword = has both advantages and disadvantages'),
    _q("c71", "mcq", "Choose the word closest in meaning to \"obsequious\".", "too eager to please", 10,
       '"Obsequious" = too eager to obey or flatter (ประจบประแจง)',
       options=["too eager to please", "rude and aggressive", "calm and wise", "tired and slow"]),
    _q("c72", "mcq", "Choose the correct sentence.", "Only after the vote did they realise their mistake", 10,
       'Inversion after "Only after ...": did they realise',
       options=["Only after the vote did they realise their mistake", "Only after the vote they realised their mistake",
                "Only after the vote they did realise their mistake",
                "Only after the vote realised they their mistake"]),
    _q("c73", "mcq", "What does \"to bite the bullet\" mean?", "to accept something unpleasant bravely", 10,
       'Idiom: face a difficult situation with courage (กัดฟันทนทำ)',
       options=["to accept something unpleasant bravely", "to eat very quickly", "to refuse an offer",
                "to make a loud noise"]),
    _q("c74", "translate_type", "Type the missing word: The CEO's resignation was a bolt from the ______.", "blue", 10,
       'Idiom: a bolt from the blue = a complete surprise (เรื่องที่ไม่คาดคิด)'),

    # --- โจทย์เรียงคำเพิ่ม (ประโยคยาก) ---
    _q("c75", "word_order", "Put the words in order to express a wish about the past.", "If only I had studied harder", 9,
       '"If only + past perfect" = wishing about the past (รู้งี้ขยันเรียนกว่านี้)',
       word_bank=["If", "only", "I", "had", "studied", "harder", "have"]),
    _q("c76", "word_order", "Put the words in order to give a strict warning.", "Under no circumstances should you open it", 10,
       'Negative adverbial + inversion: Under no circumstances should you ...',
       word_bank=["Under", "no", "circumstances", "should", "you", "open", "it", "will"]),
    _q("c77", "word_order", "Put the words in order to say what you prefer someone to do.", "I would rather you stayed here", 8,
       '"Would rather + past simple" = a preference about another person (อยากให้คุณอยู่ที่นี่)',
       word_bank=["I", "would", "rather", "you", "stayed", "here", "stay"]),
]
