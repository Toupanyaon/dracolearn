"""ตรวจความถูกต้องของเนื้อหาใน game/content.py  (รัน: python -m unittest test_content -v)"""
import unittest
from collections import Counter

from game import content


class ContentIntegrityTests(unittest.TestCase):
    def test_unique_question_ids(self):
        ids = [q.id for q in content.QUESTIONS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_lesson_question_exists(self):
        for unit in content.UNITS:
            for lesson in unit.lessons:
                for qid in lesson.question_ids:
                    self.assertIn(qid, content.QUESTION_MAP, f"{lesson.id} อ้างถึง {qid} ที่ไม่มี")

    def test_mcq_correct_answer_in_options(self):
        for q in content.QUESTIONS:
            if q.qtype == "mcq":
                lowered = [o.strip().lower() for o in q.options]
                self.assertIn(q.correct_answer.strip().lower(), lowered, q.id)
                self.assertEqual(len(lowered), len(set(lowered)), f"{q.id} มีตัวเลือกซ้ำ")

    def test_word_order_bank_can_build_answer(self):
        for q in content.QUESTIONS:
            if q.qtype == "word_order":
                need = Counter(w.lower() for w in q.correct_answer.split())
                have = Counter(w.lower() for w in q.word_bank)
                self.assertFalse(need - have, f"{q.id}: word_bank สร้างประโยคไม่ครบ")

    def test_english_questions_in_every_lesson(self):
        # บทละ ~10 ข้อ ต้องมีทั้งโจทย์ไทยและโจทย์อังกฤษ (อังกฤษอย่างน้อย 2 ข้อ ไทยอย่างน้อย 2 ข้อ)
        for unit in content.UNITS:
            for lesson in unit.lessons:
                qs = content.get_questions(lesson.question_ids)
                en = [q for q in qs if q.prompt_lang == "en"]
                th = [q for q in qs if q.prompt_lang == "th"]
                self.assertGreaterEqual(len(en), 2, f"{lesson.id} มีโจทย์อังกฤษ {len(en)} ข้อ")
                self.assertGreaterEqual(len(th), 2, f"{lesson.id} มีโจทย์ไทย {len(th)} ข้อ")

    def test_every_lesson_has_at_least_ten_questions(self):
        for unit in content.UNITS:
            for lesson in unit.lessons:
                self.assertGreaterEqual(len(lesson.question_ids), 10, lesson.id)

    def test_lesson_question_ids_have_no_duplicates(self):
        for unit in content.UNITS:
            for lesson in unit.lessons:
                self.assertEqual(len(lesson.question_ids), len(set(lesson.question_ids)), lesson.id)

    def test_every_lesson_mixes_all_five_question_types(self):
        for unit in content.UNITS:
            for lesson in unit.lessons:
                kinds = {q.qtype for q in content.get_questions(lesson.question_ids)}
                self.assertEqual(kinds, {"mcq", "word_order", "translate_type", "listen_mcq", "listen_type"}, lesson.id)

    def test_every_lesson_has_14_questions_including_4_listening(self):
        for unit in content.UNITS:
            for lesson in unit.lessons:
                qs = content.get_questions(lesson.question_ids)
                self.assertEqual(len(qs), 14, lesson.id)
                self.assertEqual(sorted(q.qtype for q in qs if q.qtype.startswith("listen")),
                                 ["listen_mcq", "listen_mcq", "listen_type", "listen_type"], lesson.id)

    def test_no_two_questions_share_the_same_prompt_and_answer(self):
        seen = {}
        for q in content.QUESTIONS:
            key = (q.prompt.strip().lower(), q.correct_answer.strip().lower(), q.audio_text.strip().lower())
            self.assertNotIn(key, seen, f"{q.id} ซ้ำกับ {seen.get(key)}")
            seen[key] = q.id

    def test_every_question_has_explanation(self):
        for q in content.QUESTIONS:
            self.assertTrue(q.explanation.strip(), q.id)

    def test_word_order_sentences_fit_on_screen(self):
        # ประโยคเรียงคำยาวเกิน 8 คำ / 9+ แผ่นคำ จะล้นกรอบบนหน้าจอ
        for q in content.QUESTIONS:
            if q.qtype == "word_order":
                self.assertLessEqual(len(q.correct_answer.split()), 8, q.id)
                self.assertLessEqual(len(q.word_bank), 9, q.id)

    def test_alt_answers_of_word_order_use_same_words(self):
        for q in content.QUESTIONS:
            if q.qtype == "word_order":
                base = Counter(content.normalize_answer(q.correct_answer).split())
                for alt in q.alt_answers:
                    self.assertEqual(Counter(content.normalize_answer(alt).split()), base, f"{q.id}: {alt}")

    def test_english_prompts_have_english_answers_only(self):
        for q in content.QUESTIONS:
            if q.prompt_lang == "en":
                self.assertTrue(q.correct_answer.isascii(), q.id)
                self.assertTrue(all(o.isascii() for o in q.options), q.id)

    def test_blank_is_spoken_as_word_blank(self):
        self.assertEqual(content.prompt_for_speech("Complete: My ____ is Blaze."),
                         "Complete: My blank is Blaze.")
        self.assertEqual(content.prompt_for_speech("Type the missing word: Nice to ______ you."),
                         "Type the missing word: Nice to blank you.")
        self.assertEqual(content.prompt_for_speech("Which one is a drink?"), "Which one is a drink?")
        for q in content.QUESTIONS:
            self.assertNotIn("_", content.prompt_for_speech(q.prompt), q.id)

    def test_contraction_and_case_and_punctuation_accepted(self):
        q = content.QUESTION_MAP["q16"]  # I am thirsty
        for ok in ["I am thirsty", "I'm thirsty", "i'm thirsty.", "  I\u2019m   Thirsty! ", "I am very thirsty"]:
            self.assertTrue(content.is_correct_answer(q, ok), ok)
        for bad in ["I thirsty", "I am hungry", "thirsty", ""]:
            self.assertFalse(content.is_correct_answer(q, bad), bad)

    def test_alt_answers_accepted(self):
        self.assertTrue(content.is_correct_answer(content.QUESTION_MAP["q4"], "Thanks"))
        self.assertTrue(content.is_correct_answer(content.QUESTION_MAP["e18"], "grandma"))
        self.assertTrue(content.is_correct_answer(content.QUESTION_MAP["q19"], "I go to school everyday"))
        self.assertFalse(content.is_correct_answer(content.QUESTION_MAP["q4"], "Sorry"))

    def test_word_order_contraction_still_correct(self):
        q = content.QUESTION_MAP["e6"]  # You're welcome
        self.assertTrue(content.is_correct_answer(q, "You're welcome"))

    def test_alt_answers_not_duplicating_wrong_meaning(self):
        # คำตอบทางเลือกของข้อหนึ่งต้องไม่ชนกับคำตอบหลักของข้ออื่นที่ใช้โจทย์คนละความหมายในบทเดียวกัน
        for unit in content.UNITS:
            for lesson in unit.lessons:
                qs = content.get_questions(lesson.question_ids)
                for a in qs:
                    for b in qs:
                        if a.id != b.id and a.qtype == b.qtype == "translate_type":
                            self.assertFalse(
                                content.normalize_answer(b.correct_answer) in
                                {content.normalize_answer(x) for x in a.alt_answers}
                                and a.correct_answer != b.correct_answer, (a.id, b.id))

    # ---------------- โจทย์ฟังแล้วตอบ (listen_mcq / listen_type) ----------------
    HOMOPHONES = {"two", "to", "too", "no", "know", "one", "won", "four", "for", "eight", "ate", "see", "sea",
                  "write", "right", "meet", "meat", "blue", "blew", "by", "buy", "bye", "here", "hear",
                  "there", "their", "wear", "where", "so", "sew", "tea", "tee", "son", "sun", "bear", "bare"}

    def _listening(self):
        return [q for q in content.QUESTIONS if q.qtype in ("listen_mcq", "listen_type")]

    def test_listening_bank_size_and_ids(self):
        ids = [q.id for q in self._listening()]
        self.assertEqual(ids, [f"l{n}" for n in range(1, 61)])

    def test_listening_questions_have_english_audio(self):
        for q in self._listening():
            self.assertTrue(q.audio_text.strip(), q.id)
            self.assertTrue(q.audio_text.isascii(), q.id)   # เสียงอ่านเป็นอังกฤษล้วน (ไม่ต้องพึ่งเสียงไทยในเครื่อง)

    def test_listening_prompt_never_leaks_the_answer(self):
        for q in self._listening():
            self.assertNotIn(q.audio_text.lower(), q.prompt.lower(), q.id)
            self.assertNotIn(q.correct_answer.lower(), q.prompt.lower(), q.id)

    def test_listen_mcq_has_four_unique_options_with_the_answer(self):
        for q in self._listening():
            if q.qtype == "listen_mcq":
                self.assertEqual(len(q.options), 4, q.id)
                self.assertEqual(len(set(o.lower() for o in q.options)), 4, q.id)
                self.assertIn(q.correct_answer, q.options, q.id)

    def test_listen_mcq_english_options_answer_equals_audio(self):
        # ตัวเลือกอังกฤษ = "ฟังแล้วเลือกคำที่ได้ยิน" เฉลยต้องเป็นคำที่ถูกอ่านจริง / ตัวเลือกไทย = "เลือกความหมาย" เฉลยเป็นไทย
        for q in self._listening():
            if q.qtype == "listen_mcq":
                if q.correct_answer.isascii():
                    self.assertEqual(q.correct_answer, q.audio_text, q.id)
                    self.assertTrue(all(o.isascii() for o in q.options), q.id)
                else:
                    self.assertFalse(any(o.isascii() for o in q.options), q.id)

    def test_listen_type_answer_is_the_audio_text(self):
        for q in self._listening():
            if q.qtype == "listen_type":
                self.assertEqual(q.correct_answer, q.audio_text, q.id)
                self.assertTrue(content.is_correct_answer(q, q.audio_text.upper() + "."), q.id)  # พิมพ์ตัวใหญ่/มีจุดก็ถูก

    def test_listen_type_numbers_accept_digits(self):
        words = {"twelve": "12", "thirteen": "13", "one": "1", "three": "3"}
        for q in self._listening():
            if q.qtype == "listen_type":
                for w, d in words.items():
                    if w in q.audio_text.lower().split():
                        alt = {content.normalize_answer(a) for a in q.alt_answers}
                        self.assertIn(content.normalize_answer(q.audio_text.lower().replace(w, d)), alt, q.id)

    def test_listening_answers_avoid_homophones(self):
        # TTS ออกเสียงอย่างเดียว คำพ้องเสียงที่เป็นคำตอบ/ตัวเลือกเดี่ยว ๆ จะแยกไม่ได้ (เช่น two/to/too)
        for q in self._listening():
            # เช็กเฉพาะ "คำที่เป็นเฉลย" (ตัวหลอกที่ไม่มีคู่พ้องเสียงอยู่ในตัวเลือกด้วยกันไม่ทำให้กำกวม)
            if len(q.audio_text.split()) == 1 and (q.qtype == "listen_type" or q.correct_answer.isascii()):
                self.assertNotIn(q.audio_text.lower(), self.HOMOPHONES, q.id)
            if q.qtype == "listen_mcq" and q.correct_answer.isascii():
                heard = q.audio_text.lower()
                for o in q.options:
                    if o.lower() != heard and len(o.split()) == 1:
                        self.assertFalse({heard, o.lower()} <= {"son", "sun"} or {heard, o.lower()} <= {"two", "too", "to"},
                                         q.id)

    def test_listening_questions_are_not_duplicated_across_a_lesson(self):
        for unit in content.UNITS:
            for lesson in unit.lessons:
                audios = [q.audio_text.lower() for q in content.get_questions(lesson.question_ids) if q.audio_text]
                self.assertEqual(len(audios), len(set(audios)), lesson.id)

    def test_listening_questions_are_not_in_challenger_hard_levels(self):
        for q in self._listening():
            self.assertLessEqual(content.QUESTION_LEVEL[q.id], content.AUTO_LEVELS, q.id)

    def test_challenger_bank_is_not_in_any_lesson(self):
        in_lessons = {qid for u in content.UNITS for l in u.lessons for qid in l.question_ids}
        self.assertFalse(in_lessons & content.CHALLENGER_QUESTION_IDS)
        self.assertEqual(in_lessons, content.LESSON_QUESTION_IDS)
        self.assertEqual(len(content.CHALLENGER_QUESTION_IDS), 77)

    def test_challenger_questions_are_english_only(self):
        for q in content.QUESTIONS:
            if q.id in content.CHALLENGER_QUESTION_IDS:
                self.assertEqual(q.prompt_lang, "en", q.id)
                self.assertTrue(q.correct_answer.isascii(), q.id)
                self.assertTrue(all(o.isascii() for o in q.options), q.id)
                self.assertGreaterEqual(q.difficulty, 4, q.id)

    def test_challenger_mcq_have_four_options(self):
        for q in content.QUESTIONS:
            if q.id in content.CHALLENGER_QUESTION_IDS and q.qtype == "mcq":
                self.assertEqual(len(q.options), 4, q.id)

    def test_practice_fallback_pool_excludes_challenger(self):
        ids = {q.id for q in content.lesson_questions()}
        self.assertFalse(ids & content.CHALLENGER_QUESTION_IDS)

    def test_prompt_lang_valid(self):
        for q in content.QUESTIONS:
            self.assertIn(q.prompt_lang, ("th", "en"), q.id)


if __name__ == "__main__":
    unittest.main()
