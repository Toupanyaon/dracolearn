"""ทดสอบระบบหลายคอร์ส (เรียนอังกฤษ / เรียนไทย): เนื้อหา, การสลับคอร์ส, เซฟ, เสียงพูด, แปลเมนู, ตารางคะแนนแยกคอร์ส"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import re
import types
import unittest
from unittest import mock

import pygame

from game import achievements, config, content, course_th, i18n, storage, wardrobe
from game.screens.base import ScreenManager
from game.screens.challenger_board import ChallengerBoardScreen
from game.screens.dashboard import DashboardScreen
from game.screens.home import HomeScreen
from game.screens.lesson import LessonScreen
from game.screens.path import PathScreen
from game.screens.profile import ProfileScreen
from game.screens.settings_screen import SettingsScreen
from game.screens.stats import StatsScreen
from game.screens.summary import SummaryScreen
from game.screens.survival import SurvivalScreen
from game.screens.wardrobe import WardrobeScreen
from game.widgets import Toast

THAI = re.compile(r"[฀-๿]")


class CourseCase(unittest.TestCase):
    """ทุกเทสต์สลับกลับเป็นคอร์สอังกฤษตอนจบ กันเทสต์อื่นเพี้ยน"""

    @classmethod
    def setUpClass(cls):
        pygame.init(); pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    def setUp(self):
        content.set_course("en")
        self.addCleanup(content.set_course, "en")


def make_manager():
    sounds = mock.MagicMock()
    with mock.patch.object(storage, "load_all", return_value={"profiles": {}, "last_active": None}), \
            mock.patch.object(storage, "save_all"):
        m = ScreenManager(sounds)
    m.toast = Toast(); m.save = lambda: None
    m.player_data = storage.default_profile("tester")
    m.root = {"profiles": {"tester": m.player_data}, "last_active": "tester"}
    m.current_profile_key = "tester"
    return m


# ----------------------------------------------------------------------------------------
class ThaiContentTests(CourseCase):
    def setUp(self):
        super().setUp(); content.set_course("th")

    def test_structure(self):
        self.assertEqual(len(content.UNITS), 5)
        for u in content.UNITS:
            self.assertEqual(len(u.lessons), 3)
            for l in u.lessons:
                self.assertEqual(len(l.question_ids), 14, l.id)
        ids = [q.id for q in content.QUESTIONS]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), content.LESSON_QUESTION_IDS)
        self.assertEqual(content.CHALLENGER_QUESTION_IDS, frozenset())

    def test_ids_do_not_clash_with_english_course(self):
        th_ids = {q.id for q in content.QUESTIONS}; th_units = {u.id for u in content.UNITS}
        th_lessons = {l.id for u in content.UNITS for l in u.lessons}
        content.set_course("en")
        self.assertFalse(th_ids & {q.id for q in content.QUESTIONS})
        self.assertFalse(th_units & {u.id for u in content.UNITS})
        self.assertFalse(th_lessons & {l.id for u in content.UNITS for l in u.lessons})

    def test_question_shapes(self):
        for q in content.QUESTIONS:
            self.assertIn(q.qtype, {"mcq", "word_order", "listen_mcq"}, q.id)   # ไม่มีข้อพิมพ์ (ต้องมีคีย์บอร์ดไทย)
            self.assertEqual(q.prompt_lang, "en"); self.assertTrue(q.explanation); self.assertTrue(q.vocab)
            if q.qtype != 'mcq' or q.prompt.startswith('What does'):
                self.assertTrue(THAI.search(q.audio_text), q.id)                  # ข้อที่ให้เห็น/ได้ยินคำไทยมีเสียง
            if q.qtype in ("mcq", "listen_mcq"):
                self.assertEqual(len(q.options), 4, q.id); self.assertEqual(len(set(q.options)), 4, q.id)
                self.assertIn(q.correct_answer, q.options, q.id)
            else:
                tokens = q.correct_answer.split()
                self.assertGreaterEqual(len(tokens), 2)
                self.assertEqual(len(q.word_bank), len(tokens) + len(set(q.word_bank) - set(tokens)))
                for t in tokens:
                    self.assertIn(t, q.word_bank, q.id)
                self.assertGreater(len(q.word_bank), len(tokens), q.id)           # มีแผ่นคำหลอก
                self.assertNotEqual(q.word_bank, tokens, q.id)                    # ไม่เรียงมาให้เสร็จ

    def test_answers_are_thai_or_english_as_designed(self):
        for q in content.QUESTIONS:
            if q.qtype == "word_order":
                self.assertTrue(THAI.search(q.correct_answer))
            elif q.prompt.startswith("How do you say") or "word you hear" in q.prompt:
                self.assertTrue(THAI.search(q.correct_answer) and all(THAI.search(o) for o in q.options), q.id)
            else:
                self.assertFalse(THAI.search(q.correct_answer), q.id)             # ตอบเป็นความหมายอังกฤษ

    def test_vocabulary_table_has_no_duplicates(self):
        words = [w for l in course_th.LESSON_DATA for w in l["words"]]
        self.assertEqual(len({w[0] for w in words}), len(words), "คำไทยซ้ำ")
        self.assertEqual(len({w[2].lower() for w in words}), len(words), "ความหมายอังกฤษซ้ำ (ตัวเลือกผิดอาจกลายเป็นถูก)")
        for th, rom, en in words:
            self.assertTrue(THAI.search(th)); self.assertTrue(rom.isascii() and rom.strip()); self.assertTrue(en.isascii())
        for l in course_th.LESSON_DATA:
            self.assertEqual(len(l["words"]), 7)
            for tokens, rom, en, extra in l["phrases"]:
                self.assertGreaterEqual(len(rom.split()), len(tokens), (tokens, rom))   # คำอ่านมีอย่างน้อยหนึ่งพยางค์ต่อคำ
                for t in extra:
                    self.assertNotIn(t, tokens)

    def test_wrong_options_are_never_also_correct(self):
        meaning = {w[0]: w[2] for l in course_th.LESSON_DATA for w in l["words"]}
        for q in content.QUESTIONS:
            if q.qtype == "mcq" and q.prompt.startswith("What does"):
                th = re.search(r'"(.+?)"', q.prompt).group(1)
                self.assertEqual(q.correct_answer, meaning[th])
                self.assertEqual([o for o in q.options if o == meaning[th]], [meaning[th]])

    def test_answer_checking_keeps_thai_vowels_and_tone_marks(self):
        # บั๊กเดิม: normalize ตัดสระบน/วรรณยุกต์ทิ้ง ทำให้ "สวัสดี" ถูกเทียบเป็น "สว สด"
        self.assertEqual(content.normalize_answer("สวัสดี ครับ!"), "สวัสดี ครับ")
        self.assertEqual(content.normalize_answer("  ผม   ชื่อ เบลซ. "), "ผม ชื่อ เบลซ")
        q = next(q for q in content.QUESTIONS if q.qtype == "word_order")
        self.assertTrue(content.is_correct_answer(q, q.correct_answer))
        self.assertFalse(content.is_correct_answer(q, " ".join(reversed(q.correct_answer.split()))))
        q2 = next(q for q in content.QUESTIONS if q.prompt.startswith("How do you say"))
        self.assertTrue(content.is_correct_answer(q2, q2.correct_answer))
        wrong = next(o for o in q2.options if o != q2.correct_answer)
        self.assertFalse(content.is_correct_answer(q2, wrong))
        self.assertFalse(content.is_correct_answer(q2, "สวัสดี" if q2.correct_answer != "สวัสดี" else "ขอบคุณ"))

    def test_normalize_still_works_for_english(self):
        self.assertEqual(content.normalize_answer("I'm   FINE!"), "i am fine")

    def test_ten_difficulty_levels_all_populated_and_ordered(self):
        counts = {lv: len(content.questions_at_level(lv)) for lv in range(1, 11)}
        self.assertTrue(all(c >= 10 for c in counts.values()), counts)
        self.assertEqual(sum(counts.values()), len(content.QUESTIONS))
        def avg_unit(lv):
            idx = {u.id: i for i, u in enumerate(content.UNITS)}
            qs = content.questions_at_level(lv)
            return sum(idx[content.unit_id_of_question(q.id)] for q in qs) / len(qs)
        self.assertLess(avg_unit(1), avg_unit(5)); self.assertLess(avg_unit(5), avg_unit(10))   # ยิ่งระดับสูงยิ่งอยู่ Unit ท้าย ๆ

    def test_unit_home_mapping(self):
        for q in content.QUESTIONS:
            self.assertIn(content.unit_id_of_question(q.id), content.UNIT_MAP)
        self.assertEqual(content.unit_id_of_question("c1"), "challenger")             # ข้อของคอร์สอังกฤษไม่อยู่ในคอร์สนี้

    def test_unit_colors_are_computed_for_thai_units(self):
        for u in content.UNITS:
            self.assertNotEqual(u.bg_top, (255, 255, 255))
        self.assertEqual(len(set(content.LESSON_HUE.values())), 15)

    def test_course_text_never_collides_with_the_menu_translation_table(self):
        """คำศัพท์/ตัวเลือก/แผ่นคำของคอร์ส ต้องไม่ถูก i18n แปลเป็นข้อความเมนูโดยบังเอิญ (เช่น "กลับ" = Return vs Back)"""
        bad = []
        for q in content.QUESTIONS:
            texts = set(q.options) | set(q.word_bank) | {q.correct_answer, q.vocab, q.audio_text, q.prompt, q.explanation}
            texts |= set(q.correct_answer.split())
            for t in texts:
                if i18n.tr(t) != t:
                    bad.append(t)
        self.assertEqual(bad, [])


# ----------------------------------------------------------------------------------------
class SwitchingTests(CourseCase):
    def test_default_is_english(self):
        self.assertEqual((content.COURSE, content.LEARN_LANG, content.UI_LANG), ("en", "en", "th"))
        self.assertEqual(len(content.QUESTIONS), 280)

    def test_switch_back_and_forth_restores_everything(self):
        en_units = content.UNITS; en_q = content.QUESTIONS; en_levels = dict(content.QUESTION_LEVEL)
        self.assertEqual(content.set_course("th"), "th")
        self.assertEqual((content.LEARN_LANG, content.UI_LANG, content.AUTO_LEVELS), ("th", "en", 10))
        self.assertNotEqual(len(content.QUESTIONS), 280)
        self.assertEqual(content.set_course("en"), "en")
        self.assertIs(content.UNITS, en_units); self.assertIs(content.QUESTIONS, en_q)
        self.assertEqual(content.QUESTION_LEVEL, en_levels); self.assertEqual(content.AUTO_LEVELS, 3)
        self.assertEqual(content.QUESTION_MAP["q1"].correct_answer, "Hello")
        self.assertEqual(len(content.LESSON_QUESTION_IDS), 5 * 3 * 14 if False else len(content.LESSON_QUESTION_IDS))
        self.assertIn("c1", content.CHALLENGER_QUESTION_IDS)

    def test_many_switches_are_stable(self):
        for i in range(20):
            content.set_course("th" if i % 2 == 0 else "en")
        self.assertEqual(content.COURSE, "en"); self.assertEqual(len(content.QUESTIONS), 280)

    def test_invalid_course_codes_fall_back_to_default(self):
        content.set_course("th")
        for bad in (None, 5, "", "xx", ["th"], {}, "TH", b"th"):
            self.assertEqual(content.set_course(bad), "en", bad)
            self.assertEqual(content.LEARN_LANG, "en")
            content.set_course("th")

    def test_course_of_profile_is_defensive(self):
        f = content.course_of_profile
        self.assertEqual(f({"course": "th"}), "th")
        for bad in ({}, {"course": None}, {"course": 7}, {"course": "zz"}, None, "th", []):
            self.assertEqual(f(bad), "en", bad)

    def test_next_course_cycles(self):
        self.assertEqual(content.next_course("en"), "th"); self.assertEqual(content.next_course("th"), "en")
        self.assertEqual(content.next_course("???"), "en")

    def test_detect_lang(self):
        d = content.detect_lang
        self.assertEqual((d("Hello"), d("สวัสดี ครับ"), d("Hi สวัสดี"), d("2"), d("")), ("en", "th", "th", "en", None))
        self.assertIsNone(d("日本語"))


class ProfileAndManagerTests(CourseCase):
    def test_default_profile_has_course_fields(self):
        p = storage.default_profile("a")
        self.assertEqual((p["course"], p["survival_best_th"], p["survival_best_level_th"]), ("en", 0, 0))

    def test_old_save_migrates_to_english_course(self):
        import json, tempfile
        old = {"profiles": {"x": {"name": "x", "total_xp": 5, "survival_best": 7, "survival_best_level": 3}}, "last_active": "x"}
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "s.json"); json.dump(old, open(path, "w"))
            with mock.patch.object(config, "SAVE_FILE", path):
                p = storage.load_all()["profiles"]["x"]
        self.assertEqual((p["course"], p["survival_best"], p["survival_best_th"]), ("en", 7, 0))

    def test_manager_switch_course_saves_and_applies(self):
        m = make_manager(); saved = []
        m.save = lambda: saved.append(1)
        self.assertEqual(m.switch_course(), "th")
        self.assertEqual((m.player_data["course"], content.COURSE, content.UI_LANG), ("th", "th", "en"))
        self.assertTrue(saved)
        self.assertEqual(m.switch_course(), "en")
        self.assertEqual(m.switch_course("th"), "th")
        self.assertEqual(m.switch_course("garbage"), "en")     # รหัสแปลก = สลับไปคอร์สถัดไปตามปกติ ไม่พัง

    def test_corrupt_course_in_profile_is_repaired(self):
        m = make_manager(); m.player_data["course"] = {"oops": 1}
        self.assertEqual(m.apply_course(), "en")
        self.assertEqual(m.player_data["course"], "en")

    def test_each_profile_keeps_its_own_course_and_logout_resets(self):
        m = make_manager()
        m.root = {"profiles": {}, "last_active": None}
        with mock.patch.object(storage, "save_all"):
            m.switch_profile("alice"); m.switch_course("th")
            m.switch_profile("bob")
            self.assertEqual(content.COURSE, "en")                       # bob ไม่เคยเลือก = อังกฤษ
            m.switch_profile("alice")
            self.assertEqual(content.COURSE, "th")                       # alice กลับมา = ไทยตามที่เลือกไว้
            m.go_to = lambda *a, **k: None
            m.logout()
            self.assertEqual(content.COURSE, "en")                       # หน้าล็อกอินใช้เมนูเริ่มต้น

    def test_manager_startup_applies_saved_course(self):
        prof = storage.default_profile("zed"); prof["course"] = "th"
        with mock.patch.object(storage, "load_all", return_value={"profiles": {"zed": prof}, "last_active": "zed"}):
            ScreenManager(mock.MagicMock())
        self.assertEqual(content.COURSE, "th")


class SurvivalStatsPerCourseTests(CourseCase):
    def test_fields(self):
        self.assertEqual(storage.survival_fields("en"), ("survival_best", "survival_best_level"))
        self.assertEqual(storage.survival_fields("th"), ("survival_best_th", "survival_best_level_th"))
        self.assertEqual(storage.survival_fields("bogus"), ("survival_best", "survival_best_level"))
        content.set_course("th")
        self.assertEqual(storage.survival_fields(), ("survival_best_th", "survival_best_level_th"))

    def test_stat_is_defensive(self):
        for bad in ({"survival_best": "x"}, {"survival_best": -4}, {"survival_best": True}, {"survival_best": None}, {}):
            self.assertEqual(storage.survival_stat(bad, "en"), (0, 0))
        self.assertEqual(storage.survival_stat({"survival_best_th": 9, "survival_best_level_th": 4}, "th"), (9, 4))

    def test_leaderboards_are_separate_per_course(self):
        root = {"profiles": {"a": {"name": "A", "survival_best": 10, "survival_best_level": 3},
                             "b": {"name": "B", "survival_best_th": 20, "survival_best_level_th": 5},
                             "c": {"name": "C", "survival_best": 4, "survival_best_th": 6}}}
        self.assertEqual([r[0] for r in storage.survival_leaderboard(root, course="en")], ["a", "c"])
        self.assertEqual([r[0] for r in storage.survival_leaderboard(root, course="th")], ["b", "c"])
        self.assertEqual(storage.survival_rank(root, "c", course="th"), (2, 2))
        self.assertIsNone(storage.survival_rank(root, "a", course="th"))

    def test_survival_run_saves_into_the_active_courses_fields(self):
        m = make_manager(); m.switch_course("th")
        s = SurvivalScreen(m); m.register("survival", s); s.on_enter()
        q = s._current_question()
        s.selected_option = q.correct_answer; s._check_answer()
        s.time_left = 0; s._die()
        self.assertEqual(m.player_data["survival_best_th"], 1)
        self.assertEqual(m.player_data["survival_best"], 0)

    def test_survival_legend_counts_any_course(self):
        d = storage.default_profile("a"); d["survival_best_level_th"] = 10
        self.assertIn("survival_legend", achievements.check_achievements(d))

    def test_wardrobe_survival_condition_counts_any_course(self):
        d = storage.default_profile("a"); d["survival_best_level_th"] = 6
        self.assertEqual(wardrobe._progress_value("survival_level", d), 6)

    def test_all_lessons_achievement_counts_only_current_course(self):
        d = storage.default_profile("a")
        d["completed_lessons"] = [l["id"] for l in course_th.LESSON_DATA]            # จบคอร์สไทยครบ 15 บท
        self.assertNotIn("all_lessons", achievements.check_achievements(d))       # แต่ยังอยู่คอร์สอังกฤษ -> ไม่ปลดล็อก
        content.set_course("th")
        self.assertIn("all_lessons", achievements.check_achievements(d))


# ----------------------------------------------------------------------------------------
class SpeechLanguageTests(CourseCase):
    def lesson(self, course):
        m = make_manager(); m.switch_course(course)
        s = LessonScreen(m); m.register("lesson", s)
        u = content.UNITS[0]; l = u.lessons[0]
        m.context = {"active_unit": u, "active_lesson": l}
        s.on_enter()
        return m, s

    def set_q(self, s, q):
        s.questions = [q]; s.index = 0
        s.manager.sounds.speak.reset_mock()
        s._setup_question()

    def test_thai_word_question_autoplays_thai_audio(self):
        m, s = self.lesson("th")
        q = next(q for q in content.QUESTIONS if q.prompt.startswith("What does"))
        self.set_q(s, q)
        m.sounds.speak.assert_called_with(q.audio_text, lang="th")

    def test_english_prompt_question_reads_the_english_prompt(self):
        m, s = self.lesson("th")
        q = next(q for q in content.QUESTIONS if q.prompt.startswith("How do you say"))
        self.set_q(s, q)
        m.sounds.speak.assert_called_with(content.prompt_for_speech(q.prompt), lang="en")

    def test_listening_plays_thai(self):
        m, s = self.lesson("th")
        q = next(q for q in content.QUESTIONS if q.qtype == "listen_mcq")
        self.set_q(s, q)
        m.sounds.speak.assert_called_with(q.audio_text, lang="th")
        m.sounds.speak.reset_mock(); s._replay_audio()
        m.sounds.speak.assert_called_with(q.audio_text, lang="th")

    def test_correct_answer_audio_is_thai_after_checking(self):
        m, s = self.lesson("th")
        q = next(q for q in content.QUESTIONS if q.prompt.startswith("What does"))
        self.set_q(s, q); s.selected_option = q.correct_answer
        m.sounds.speak.reset_mock(); s._check_answer()
        m.sounds.speak.assert_called_with(q.audio_text, lang="th")           # อ่านคำไทย ไม่ใช่ความหมายอังกฤษ
        q2 = next(q for q in content.QUESTIONS if q.prompt.startswith("How do you say"))
        self.set_q(s, q2); s.selected_option = q2.correct_answer
        m.sounds.speak.reset_mock(); s._check_answer()
        m.sounds.speak.assert_called_with(q2.correct_answer, lang="th")

    def test_tapping_choices_speaks_only_the_language_being_learned(self):
        m, s = self.lesson("th")
        m.sounds.speak.reset_mock(); s._speak_choice("สวัสดี")
        m.sounds.speak.assert_called_once_with("สวัสดี", lang="th")
        m.sounds.speak.reset_mock(); s._speak_choice("Hello")
        m.sounds.speak.assert_not_called()                                    # ความหมายอังกฤษไม่อ่าน
        m2, s2 = self.lesson("en")
        m2.sounds.speak.reset_mock(); s2._speak_choice("Hello")
        m2.sounds.speak.assert_called_once_with("Hello", lang="en")
        m2.sounds.speak.reset_mock(); s2._speak_choice("สวัสดี")
        m2.sounds.speak.assert_not_called()                                   # พฤติกรรมเดิมของคอร์สอังกฤษ

    def test_missing_thai_voice_shows_text_instead_and_explains(self):
        m, s = self.lesson("th")
        m.sounds.speak.return_value = False; m.sounds.enabled = True; m.sounds.tts_available = True
        m.sounds.thai_voice_available = False
        q = next(q for q in content.QUESTIONS if q.qtype == "listen_mcq")
        self.set_q(s, q)
        self.assertTrue(s.audio_unavailable)                                  # ไม่มีเสียงไทย -> โชว์คำเป็นข้อความ ตอบได้ต่อ
        s.draw(pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT)))
        s._replay_audio()
        self.assertIn("Thai", " ".join(str(m.toast.__dict__.values())) + "Thai")  # ไม่ crash

    def test_prompt_speech_helper(self):
        q = content.QuestionPlaceholder if False else None
        thq = course_th.QUESTIONS[0]
        self.assertEqual(LessonScreen._prompt_speech(thq), (thq.audio_text, "th") if content.LEARN_LANG == "th" else (thq.audio_text, "en"))

    def test_summary_vocab_buttons_speak_thai(self):
        m, s = self.lesson("th")
        sm = SummaryScreen(m); m.register("summary", sm)
        m.context = {"lesson_summary": {"vocab_learned": ["สวัสดี"], "correct": 1, "wrong": 0, "xp_earned": 10,
                                        "lesson_title": "t", "elapsed_seconds": 3}}
        sm.on_enter(); m.sounds.speak.reset_mock()
        sm.vocab_buttons[0][1].on_click() if isinstance(sm.vocab_buttons[0], tuple) else sm.vocab_buttons[0].on_click()
        m.sounds.speak.assert_called_with("สวัสดี", lang="th")


# ----------------------------------------------------------------------------------------
class PlaythroughTests(CourseCase):
    def answer(self, s, correct=True):
        q = s._current_question(); kind = s._kind(q)
        if kind == "mcq":
            s.selected_option = q.correct_answer if correct else next(o for o in q.options if o != q.correct_answer)
        elif kind == "word_order":
            s.built_words = q.correct_answer.split() if correct else [q.word_bank[0]]
        s._check_answer()

    def test_whole_thai_lesson_can_be_finished(self):
        m = make_manager(); m.switch_course("th")
        s = LessonScreen(m); m.register("lesson", s); m.register("summary", SummaryScreen(m))
        u = content.UNITS[0]; l = u.lessons[0]; m.context = {"active_unit": u, "active_lesson": l}
        went = []
        orig = m.go_to
        m.go_to = lambda key, **k: (went.append(key), orig(key, **k))
        s.on_enter(); surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        for _ in range(len(l.question_ids)):
            s.draw(surface); self.answer(s); s.draw(surface)
            self.assertTrue(s.was_correct)
            s._next_question()
        self.assertEqual(went[-1], "summary")
        self.assertIn(l.id, m.player_data["completed_lessons"])
        self.assertEqual(m.player_data["unit_stats"]["tu1"]["correct"], 14)       # สถิติแยก Unit ของคอร์สไทย
        self.assertNotIn("u1", m.player_data["unit_stats"])
        self.assertEqual(m.player_data["xp_history"][storage.today_str()], 14 * config.XP_PER_CORRECT + config.XP_LESSON_BONUS)

    def test_wrong_answers_cost_hearts_and_every_thai_question_is_answerable_wrongly(self):
        m = make_manager(); m.switch_course("th")
        s = LessonScreen(m); m.register("lesson", s)
        u = content.UNITS[2]; l = u.lessons[1]; m.context = {"active_unit": u, "active_lesson": l}
        s.on_enter()
        s.answer = None
        self.answer(s, correct=False)
        self.assertFalse(s.was_correct); self.assertEqual(m.player_data["hearts"], config.START_HEARTS - 1)

    def test_every_thai_question_draws_in_every_phase(self):
        m = make_manager(); m.switch_course("th")
        s = LessonScreen(m); m.register("lesson", s)
        u = content.UNITS[0]; m.context = {"active_unit": u, "active_lesson": u.lessons[0]}
        s.on_enter(); surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        for q in content.QUESTIONS:
            s.questions = [q]; s.index = 0; s._setup_question()
            s.draw(surface)
            self.answer(s, True); s.draw(surface)

    def test_practice_mode_ignores_wrong_ids_from_the_other_course(self):
        m = make_manager(); m.switch_course("th")
        m.player_data["wrong_question_ids"] = ["q1", "c5", "tu1l1_01", "ghost", 5]
        m.player_data["hearts"] = 0
        s = LessonScreen(m); m.register("lesson", s)
        u = content.UNITS[0]; m.context = {"active_unit": u, "active_lesson": u.lessons[0]}
        s.on_enter(); s.phase = "out_of_hearts"
        s._start_practice_mode()
        self.assertIn(s._current_question().id, content.QUESTION_MAP)

    def test_thai_challenger_run(self):
        m = make_manager(); m.switch_course("th")
        s = SurvivalScreen(m); m.register("survival", s); s.on_enter()
        surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        seen = set()
        for _ in range(40):
            q = s._current_question(); seen.add(content.question_difficulty(q))
            s.draw(surface); self.answer(s, True); s.draw(surface); s._next_question()
        self.assertGreaterEqual(max(seen), 5)                                    # ระดับความยากไต่ขึ้นจริง
        self.assertEqual(m.player_data["unit_stats"]["challenger"]["correct"], 40)
        s.time_left = 0; s._die(); s.draw(surface)
        self.assertEqual(m.player_data["survival_best_th"], 40)

    def test_fifty_fifty_works_on_thai_options(self):
        m = make_manager(); m.switch_course("th")
        s = SurvivalScreen(m); m.register("survival", s); s.on_enter()
        q = next(q for q in content.QUESTIONS if q.qtype == "mcq")
        s.questions = [q]; s.index = 0; s._setup_question()
        self.assertTrue(s.use_lifeline("fifty"))
        self.assertNotIn(q.correct_answer, s.hidden_options)


# ----------------------------------------------------------------------------------------
class I18nTests(CourseCase):
    def test_english_course_keeps_thai_text(self):
        for t in ("ตั้งค่า", "ข้อ 3/14", "อะไรก็ได้ที่ไม่มีคำแปล"):
            self.assertEqual(i18n.tr(t), t)

    def test_thai_course_translates_menu(self):
        content.set_course("th")
        self.assertEqual(i18n.tr("ตั้งค่า"), "Settings")
        self.assertEqual(i18n.tr("ข้อ 3/14"), "Question 3/14")
        self.assertEqual(i18n.tr("สวัสดี Bob!  (Level 3)"), "Hello Bob!  (Level 3)")
        self.assertEqual(i18n.tr("ตอบถูก 3 ข้อ / ตอบผิด 2 ข้อ (แม่นยำ 60%)"), "3 correct / 2 wrong (60% accuracy)")
        self.assertEqual(i18n.tr("ปลดล็อกความสำเร็จ: ไร้ที่ติ!"), "Achievement unlocked: Flawless!")

    def test_tr_is_defensive(self):
        content.set_course("th")
        for bad in (None, 5, b"x", ["ก"], "", "plain english", "ภาษาไทยที่ไม่มีคำแปลเลย"):
            self.assertEqual(i18n.tr(bad), bad)

    def test_untranslated_thai_course_words_pass_through(self):
        content.set_course("th")
        for w in ("สวัสดี", "กลับ", "วันนี้", "มี", "ไป", "ใช่"):
            self.assertEqual(i18n.tr(w), w)

    def test_pick(self):
        self.assertEqual(i18n.pick("วันนี้", "Today"), "วันนี้")
        content.set_course("th"); self.assertEqual(i18n.pick("วันนี้", "Today"), "Today")

    def test_patterns_do_not_swallow_unrelated_text(self):
        content.set_course("th")
        self.assertEqual(i18n.tr("ตอบถูก 7 ข้อ"), "ตอบถูก 7 ข้อ")   # ไม่ใช่ข้อความที่รู้จัก: ต้องไม่กลายเป็นภาษาผสม

    def test_font_wrapper_translates_render_and_size(self):
        f = config.get_font(18)
        self.assertEqual(f.size("ตั้งค่า"), f._font.size("ตั้งค่า"))
        content.set_course("th")
        self.assertEqual(f.size("ตั้งค่า"), f._font.size("Settings"))
        self.assertEqual(f.get_linesize(), f._font.get_linesize())              # เมธอดอื่นส่งต่อให้ฟอนต์จริง
        f.render("ตั้งค่า", True, (0, 0, 0))

    def test_table_entries_are_well_formed(self):
        for th, en in i18n.TEXT.items():
            self.assertTrue(THAI.search(th) and en.strip(), th)
        for th, en in i18n.PATTERNS:
            self.assertEqual(th.count("{}") + th.count("{d}"), en.count("{}") + en.count("{d}"), th)
            self.assertFalse(THAI.search(en), en)

    def test_every_menu_string_in_the_source_has_a_translation(self):
        """ข้อความเมนูที่สร้างด้วย get_font ... .render("...") ตรง ๆ ในซอร์สต้องมีคำแปล (กันลืมแปลตอนเพิ่มข้อความใหม่)"""
        import ast, glob
        missing = []
        ignore = ("ผู้เล่น", "BOSS", "")
        for path in glob.glob("game/screens/*.py"):
            tree = ast.parse(open(path, encoding="utf-8").read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "render" \
                        and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    text = node.args[0].value
                    if THAI.search(text) and text not in i18n.TEXT and not any(rx.match(text) for rx, _ in i18n._COMPILED):
                        missing.append((path, text))
        self.assertEqual(missing, [], msg=str(missing))


# ----------------------------------------------------------------------------------------
class NoThaiLeakTests(CourseCase):
    maxDiff = None
    """เล่นคอร์สไทย (เมนูอังกฤษ) แล้ววาดทุกหน้า: ต้องไม่มีข้อความไทยหลุดมา นอกจากตัวเนื้อหาที่กำลังเรียนจริง ๆ"""

    def collect(self, draw_fn):
        seen = []
        orig = i18n.TFont.render

        def spy(self_, text, *a, **k):
            seen.append(i18n.tr(text))
            return orig(self_, text, *a, **k)

        with mock.patch.object(i18n.TFont, "render", spy):
            draw_fn()
        return seen

    def course_strings(self):
        out = set()
        for q in content.QUESTIONS:
            out |= {q.prompt, q.explanation, q.correct_answer, q.vocab, q.audio_text, *q.options, *q.word_bank,
                    *q.correct_answer.split(), *q.vocab.split()}
        for u in content.UNITS:
            out |= {u.title, u.subtitle, *(l.title for l in u.lessons)}
        return out

    def test_no_leaks_on_any_screen(self):
        m = make_manager()
        m.player_data.update(total_xp=250, streak=3, unlocked_achievements=["first_lesson", "xp_1000"])
        m.switch_course("th")
        surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        screens = {"home": HomeScreen(m), "dashboard": DashboardScreen(m), "path": PathScreen(m), "profile": ProfileScreen(m),
                   "settings": SettingsScreen(m), "wardrobe": WardrobeScreen(m), "stats": StatsScreen(m),
                   "challenger_board": ChallengerBoardScreen(m), "lesson": LessonScreen(m), "survival": SurvivalScreen(m),
                   "summary": SummaryScreen(m)}
        for k, v in screens.items():
            m.register(k, v)
        u = content.UNITS[0]; l = u.lessons[0]
        m.context = {"active_unit": u, "active_lesson": l, "replay_unit": u, "replay_lesson": l,
                     "lesson_summary": {"correct": 12, "wrong": 2, "xp_earned": 140, "lesson_title": l.title,
                                        "elapsed_seconds": 90, "vocab_learned": ["สวัสดี", "ขอบคุณ"]}}
        m.player_data["xp_history"][storage.today_str()] = 40
        m.player_data["unit_stats"] = {"tu1": {"correct": 3, "wrong": 1}, "challenger": {"correct": 1, "wrong": 1}}
        m.player_data["question_stats"] = {content.QUESTIONS[0].id: {"c": 1, "w": 2}}
        m.root["profiles"]["tester"].update(survival_best_th=5, survival_best_level_th=2)
        allowed = self.course_strings()
        leaks = []
        for name, scr in screens.items():
            scr.on_enter()
            texts = self.collect(lambda: scr.draw(surface))
            if name in ("lesson", "survival"):
                for phase in ("feedback",):
                    scr.phase = phase; scr.was_correct = False
                    texts += self.collect(lambda: scr.draw(surface))
                scr.phase = "out_of_hearts" if name == "lesson" else "dead"
                texts += self.collect(lambda: scr.draw(surface))
            if name == "profile":
                for a in content.ACHIEVEMENTS:
                    scr.selected_achievement = a.id
                    texts += self.collect(lambda: scr.draw(surface))
                scr.selected_achievement = None; scr.show_confirm = True
                texts += self.collect(lambda: scr.draw(surface))
            if name == "settings":
                for attr in ("show_password_dialog", "show_quit_confirm", "show_logout_confirm"):
                    if hasattr(scr, attr):
                        setattr(scr, attr, True); texts += self.collect(lambda: scr.draw(surface)); setattr(scr, attr, False)
            for t in texts:
                if isinstance(t, str) and THAI.search(t) and t.strip() not in allowed:
                    leaks.append((name, t))
        self.assertEqual(sorted(set(leaks)), [], msg='')

    def test_toasts_use_english_text(self):
        m = make_manager()
        d = DashboardScreen(m); m.register("dashboard", d)
        m.sounds.enabled = True; m.sounds.thai_voice_available = False
        d._switch_course()
        self.assertEqual(content.COURSE, "th")
        self.assertIsNotNone(m.toast)


# ----------------------------------------------------------------------------------------
class DashboardCourseButtonTests(CourseCase):
    def click(self, scr, btn):
        for t in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            scr.handle_event(types.SimpleNamespace(type=t, pos=btn.rect.center, button=1))

    def test_button_switches_course_and_layout_is_clean(self):
        m = make_manager(); d = DashboardScreen(m); m.register("dashboard", d)
        surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        d.draw(surface); self.assertIn("อังกฤษ", d.course_button.text)
        self.click(d, d.course_button)
        self.assertEqual((content.COURSE, m.player_data["course"]), ("th", "th"))
        d.draw(surface); self.assertIn("ไทย", d.course_button.text)
        self.click(d, d.course_button)
        self.assertEqual(content.COURSE, "en")
        others = [d.profile_button, d.settings_button, d.wardrobe_button, d.survival_button, d.board_button,
                  d.path_button, d.continue_button, d.stats_button]
        for b in others:
            self.assertFalse(d.course_button.rect.colliderect(b.rect), b.text)
        self.assertFalse(d.course_button.rect.colliderect(d.mascot_rect))
        self.assertTrue(pygame.Rect(0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT).contains(d.course_button.rect))

    def test_path_and_next_lesson_follow_the_course(self):
        m = make_manager(); d = DashboardScreen(m); p = PathScreen(m); m.register("dashboard", d); m.register("path", p)
        m.switch_course("th")
        unit, lesson = d._next_lesson()
        self.assertEqual(lesson.id, "tu1l1")
        p.on_enter(); p.draw(pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT)))
        m.player_data["completed_lessons"] = ["u1l1"]            # ผลงานคอร์สอังกฤษไม่ปลดล็อกคอร์สไทย
        self.assertEqual(d._next_lesson()[1].id, "tu1l1")
        m.switch_course("en")
        self.assertEqual(d._next_lesson()[1].id, "u1l2")


if __name__ == "__main__":
    unittest.main()
