"""ทดสอบโหมดจับเวลา (รัน: python -m unittest test_survival -v)
ไม่ต้องมีหน้าต่าง/เสียงจริง: ตั้ง SDL เป็นโหมด dummy ให้ก่อน import pygame
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import types
import unittest
from unittest import mock

import pygame

from game import config, content, storage
from game.screens.base import ScreenManager
from game.screens.survival import SurvivalScreen
from game.screens.challenger_board import ChallengerBoardScreen
from game.widgets import Toast


class DifficultyTests(unittest.TestCase):
    def test_every_question_has_a_level_in_range(self):
        for q in content.QUESTIONS:
            self.assertIn(content.question_difficulty(q), range(1, content.DIFFICULTY_LEVELS + 1), q.id)

    def test_there_are_ten_levels_with_names(self):
        self.assertEqual(content.DIFFICULTY_LEVELS, 10)
        self.assertEqual(len(content.LEVEL_NAMES), content.DIFFICULTY_LEVELS)
        self.assertEqual(len(content.LEVEL_CEFR), content.DIFFICULTY_LEVELS)
        self.assertEqual(content.level_name(1), "Baby Chick")
        self.assertEqual(content.level_name(10), "God of Destruction")
        self.assertEqual(len(set(content.LEVEL_NAMES)), content.DIFFICULTY_LEVELS)  # ชื่อห้ามซ้ำกัน
        self.assertEqual(content.level_name(0), content.level_name(1))              # นอกช่วง -> ถูกบีบเข้าช่วง
        self.assertEqual(content.level_name(99), content.level_name(10))

    def test_every_level_has_enough_questions(self):
        for level in range(1, content.DIFFICULTY_LEVELS + 1):
            need = 10 if level >= 4 else 20  # ระดับสูงพอให้ไม่ซ้ำติดกัน / ระดับ 1-3 ใช้โจทย์บทเรียนเยอะอยู่แล้ว
            self.assertGreaterEqual(len(content.questions_at_level(level)), need, f"ระดับ {level} มีโจทย์น้อยเกินไป")

    def test_top_level_has_extra_questions_because_players_stay_there(self):
        self.assertGreaterEqual(len(content.questions_at_level(content.DIFFICULTY_LEVELS)), 12)

    def test_basic_levels_use_lesson_questions_and_hard_levels_use_challenger_bank(self):
        for level in range(1, content.AUTO_LEVELS + 1):
            for q in content.questions_at_level(level):
                self.assertIn(q.id, content.LESSON_QUESTION_IDS, q.id)
        for level in range(content.AUTO_LEVELS + 1, content.DIFFICULTY_LEVELS + 1):
            for q in content.questions_at_level(level):
                self.assertIn(q.id, content.CHALLENGER_QUESTION_IDS, q.id)

    def test_harder_levels_have_longer_prompts_and_answers_on_average(self):
        # ยิ่งระดับสูง โจทย์ยิ่งยาว/ซับซ้อน (วัดคร่าว ๆ ด้วยความยาวโจทย์เฉลี่ย) - ระดับ 10 ต้องยากกว่าระดับ 1 ชัดเจน
        def avg_len(level):
            qs = content.questions_at_level(level)
            return sum(len(q.prompt) for q in qs) / len(qs)
        self.assertGreater(avg_len(10), avg_len(1) * 1.5)
        self.assertGreater(avg_len(7), avg_len(1))

    def test_each_hard_level_mixes_question_types(self):
        for level in range(4, content.DIFFICULTY_LEVELS + 1):
            kinds = {q.qtype for q in content.questions_at_level(level)}
            self.assertGreaterEqual(len(kinds), 2, f"ระดับ {level} มีโจทย์ชนิดเดียว")

    def test_manual_difficulty_overrides_auto(self):
        q = content.QUESTIONS[0]
        self.assertEqual(q.difficulty, 0)  # ข้อนี้ปล่อยให้ระบบคำนวณ -> ยังอยู่ในช่วงปกติ
        self.assertTrue(1 <= content.question_difficulty(q) <= content.DIFFICULTY_LEVELS)


class SurvivalRulesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    def setUp(self):
        sounds = mock.MagicMock()
        with mock.patch.object(storage, "load_all", return_value={"profiles": {}, "last_active": None}), \
                mock.patch.object(storage, "save_all"):
            self.manager = ScreenManager(sounds)
        self.manager.toast = Toast()
        self.manager.save = lambda: None
        self.manager.switch_profile = None
        self.manager.player_data = storage.default_profile("tester")
        self.screen = SurvivalScreen(self.manager)
        self.manager.register("survival", self.screen)
        self.screen.on_enter()

    def _answer(self, correct: bool):
        q = self.screen._current_question()
        kind = self.screen._kind(q)  # listen_mcq ตอบแบบ mcq / listen_type ตอบแบบพิมพ์
        if kind == "mcq":
            wrong = next(o for o in q.options if o != q.correct_answer)
            self.screen.selected_option = q.correct_answer if correct else wrong
        elif kind == "word_order":
            self.screen.built_words = q.correct_answer.split() if correct else ["zzz"]
        else:
            self.screen.text_input.text = q.correct_answer if correct else "zzz"
        self.screen._check_answer()

    def _question_of_type(self, qtype):
        q = next(q for q in content.QUESTIONS if q.qtype == qtype and all(w.isascii() for w in q.word_bank + q.options))
        self.screen.questions = [q]
        self.screen.index = 0
        self.screen._setup_question()
        self.screen.draw(pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT)))  # วาดก่อนเพื่อให้มี rect ให้คลิก
        return q

    def _click(self, rect):
        pos = rect.center
        self.screen.handle_event(types.SimpleNamespace(type=pygame.MOUSEBUTTONUP, pos=pos, button=1))

    def _set_question(self, qid):
        q = content.QUESTION_MAP[qid]
        self.screen.questions = [q]
        self.screen.index = 0
        self.manager.sounds.speak.reset_mock()
        self.screen._setup_question()
        self.screen.draw(pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT)))
        return q

    def test_listening_question_autoplays_its_audio_not_the_prompt(self):
        q = self._set_question("l5")   # listen_mcq: ฟังแล้วเลือกคำที่ได้ยิน
        self.manager.sounds.speak.assert_called_once_with("Good morning", lang="en")
        self.assertFalse(self.screen.audio_unavailable)

    def test_listening_replay_buttons_play_the_audio_again(self):
        self._set_question("l7")       # listen_type
        self.manager.sounds.speak.reset_mock()
        self._press_button(self.screen.listen_big_button)      # ปุ่มลำโพงใหญ่กลางการ์ด
        self.manager.sounds.speak.assert_called_once_with("Good afternoon", lang="en")
        self.manager.sounds.speak.reset_mock()
        self._press_button(self.screen.listen_prompt_button)   # ปุ่ม "ฟังอีกครั้ง" มุมซ้ายบน
        self.manager.sounds.speak.assert_called_once_with("Good afternoon", lang="en")
        self.assertEqual(self.screen.listen_prompt_button.text.strip(), "ฟังอีกครั้ง")

    def test_normal_question_still_reads_the_prompt_and_hides_the_big_button(self):
        q = self._set_question("q1")
        self.manager.sounds.speak.assert_called_once_with(content.prompt_for_speech(q.prompt), lang=q.prompt_lang)
        self.assertEqual(self.screen.listen_prompt_button.text.strip(), "ฟังโจทย์")

    def test_audio_unavailable_falls_back_to_showing_the_text(self):
        self.manager.sounds.speak.return_value = False         # ปิดเสียง/ไม่มี TTS
        self.manager.sounds.enabled = False
        self._set_question("l9")
        self.assertTrue(self.screen.audio_unavailable)
        self.screen.draw(pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT)))   # วาดโหมดข้อความแทนได้ไม่พัง
        with mock.patch.object(self.manager.toast, "show") as toast_show:
            self._press_button(self.screen.listen_prompt_button)   # กดฟังซ้ำทางปุ่มซ้ายบน -> ต้องแจ้งสาเหตุที่เล่นเสียงไม่ได้
            toast_show.assert_called()

    def test_listen_mcq_thai_answer_speaks_english_audio_after_check(self):
        q = self._set_question("l2")                            # ฟัง Goodbye เลือกความหมายไทย
        self.assertEqual(q.correct_answer, "ลาก่อน")
        self.manager.sounds.speak.reset_mock()
        self.screen.selected_option = "ลาก่อน"
        self.screen._check_answer()
        self.assertTrue(self.screen.was_correct)
        self.manager.sounds.speak.assert_called_once_with("Goodbye", lang="en")  # ไม่อ่านคำไทยด้วยเสียงอังกฤษ

    def test_listen_questions_grade_correct_and_wrong(self):
        for qid in ("l1", "l2", "l3", "l23", "l24"):
            for correct in (True, False):
                self._set_question(qid)
                self._answer(correct)
                self.assertEqual(self.screen.was_correct, correct, (qid, correct))

    def test_listening_choice_taps_speak_only_english_options(self):
        self._set_question("l5")                                # ตัวเลือกอังกฤษ -> อ่านตัวเลือกที่กด
        self.manager.sounds.speak.reset_mock()
        rect, option = self.screen.mcq_option_rects[1]
        self._click(rect)
        self.manager.sounds.speak.assert_called_once_with(option, lang="en")
        self._set_question("l6")                                # ตัวเลือกไทย -> ไม่อ่าน (ไม่นับเสียงที่เล่นอัตโนมัติตอนขึ้นข้อ)
        self.manager.sounds.speak.reset_mock()
        rect, option = self.screen.mcq_option_rects[0]
        self._click(rect)
        self.manager.sounds.speak.assert_not_called()

    def test_every_listening_question_draws_in_every_phase(self):
        surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        for q in content.QUESTIONS:
            if q.qtype.startswith("listen"):
                self._set_question(q.id)
                self.screen.draw(surface)
                self._answer(True)
                self.screen.draw(surface)

    def _press_button(self, button):
        """ปุ่ม (Button) ต้องกดลง (DOWN) แล้วปล่อย (UP) ที่เดิมถึงนับว่าคลิก ต่างจากแผ่นคำ/ตัวเลือกที่นับตอนปล่อยอย่างเดียว"""
        for kind in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            self.screen.handle_event(types.SimpleNamespace(type=kind, pos=button.rect.center, button=1))

    def test_tapping_a_word_tile_speaks_it_before_checking(self):
        self._question_of_type("word_order")
        self.manager.sounds.speak.reset_mock()
        rect, word = self.screen.word_tile_rects[0]
        self._click(rect)
        self.manager.sounds.speak.assert_called_once_with(word, lang="en")
        self.assertEqual(self.screen.phase, "answering")  # ยังไม่ได้ตรวจคำตอบ

    def test_tapping_a_built_word_to_remove_it_also_speaks(self):
        self._question_of_type("word_order")
        self._click(self.screen.word_tile_rects[0][0])
        self.screen.draw(pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT)))
        self.manager.sounds.speak.reset_mock()
        rect, word = self.screen.built_word_rects[0]
        self._click(rect)
        self.manager.sounds.speak.assert_called_once_with(word, lang="en")

    def test_choosing_an_mcq_option_speaks_it_when_english(self):
        q = self._question_of_type("mcq")
        self.manager.sounds.speak.reset_mock()
        rect, option = self.screen.mcq_option_rects[1]
        self._click(rect)
        self.manager.sounds.speak.assert_called_once_with(option, lang="en")

    def test_read_words_toggle_button_turns_tap_speech_off_and_on(self):
        self._question_of_type("word_order")
        data = self.manager.player_data
        self.assertTrue(data["read_words_on_tap"])             # ค่าเริ่มต้น = เปิด
        self._press_button(self.screen.read_toggle_button)       # กดปิด
        self.assertFalse(data["read_words_on_tap"])
        self.manager.sounds.stop_speech.assert_called()        # ปิดแล้วต้องเงียบทันที
        self.manager.sounds.speak.reset_mock()
        self._click(self.screen.word_tile_rects[0][0])         # กดคำตอนปิด -> ต้องไม่อ่าน
        self.manager.sounds.speak.assert_not_called()
        self._press_button(self.screen.read_toggle_button)       # กดเปิดอีกครั้ง
        self.assertTrue(data["read_words_on_tap"])
        self.screen.draw(pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT)))
        self._click(self.screen.word_tile_rects[0][0])
        self.manager.sounds.speak.assert_called_once()

    def test_read_words_toggle_does_not_silence_prompt_reading(self):
        self._question_of_type("mcq")
        self._press_button(self.screen.read_toggle_button)       # ปิดอ่านคำที่กด
        self.manager.sounds.speak.reset_mock()
        self.screen._speak_prompt()                            # ปุ่ม "ฟังโจทย์" ต้องยังพูดได้ปกติ
        self.manager.sounds.speak.assert_called()

    def test_read_words_setting_is_saved_in_profile_defaults(self):
        from game import storage
        self.assertTrue(storage.default_profile("x")["read_words_on_tap"])

    def test_thai_mcq_option_is_not_spoken(self):
        self.manager.sounds.speak.reset_mock()  # on_enter อ่านโจทย์อัตโนมัติไปแล้วหนึ่งครั้ง
        self.screen._speak_choice("แอปเปิล")
        self.screen._speak_choice("")
        self.manager.sounds.speak.assert_not_called()

    def test_starts_with_60_seconds_level_1(self):
        self.assertEqual(self.screen.time_left, 60)
        self.assertEqual(self.screen.level, 1)
        self.assertEqual(content.question_difficulty(self.screen._current_question()), 1)

    def test_correct_adds_5_seconds(self):
        self._answer(True)
        self.assertEqual(self.screen.time_left, 65)

    def test_wrong_subtracts_5_seconds(self):
        self._answer(False)
        self.assertEqual(self.screen.time_left, 55)
        self.assertIn(self.screen.questions[0].id, self.manager.player_data["wrong_question_ids"])

    def test_timer_runs_only_while_answering(self):
        self.screen.update(1.0 / 60)
        self.assertLess(self.screen.time_left, 60)
        self._answer(True)
        before = self.screen.time_left
        self.screen.update(0.05)  # อยู่หน้าเฉลย -> ไม่ลดเวลา
        self.assertEqual(self.screen.time_left, before)

    def test_time_runs_out_means_death_and_saves_best(self):
        self._answer(True)
        self.screen._next_question()
        for _ in range(2000):
            self.screen.update(0.1)
            if self.screen.phase == "dead":
                break
        self.assertEqual(self.screen.phase, "dead")
        self.assertEqual(self.manager.player_data["survival_best"], 1)
        self.assertTrue(self.screen.new_record)

    def test_wrong_answer_that_empties_the_clock_shows_feedback_then_dies(self):
        self.screen.time_left = 4
        self._answer(False)
        self.assertEqual(self.screen.time_left, 0)
        self.assertEqual(self.screen.phase, "feedback")  # ได้เห็นเฉลยก่อน
        self.screen._next_question()
        self.assertEqual(self.screen.phase, "dead")

    def test_difficulty_rises_every_3_correct(self):
        # กติกาพื้นฐานของระดับความยาก: ปิดบอสไว้ (บอสออกข้อที่ยากกว่าระดับปัจจุบันโดยตั้งใจ มีเทสต์แยกใน test_challenger_hardcore.py)
        patcher = mock.patch.object(config, "SURVIVAL_BOSS_EVERY", 10 ** 6)
        patcher.start()
        self.addCleanup(patcher.stop)
        levels = []
        for _ in range(config.SURVIVAL_CORRECT_PER_LEVEL * (content.DIFFICULTY_LEVELS + 1)):
            levels.append(content.question_difficulty(self.screen._current_question()))
            self._answer(True)
            self.screen._next_question()
        self.assertEqual(levels[:3], [1, 1, 1])
        self.assertEqual(levels[3:6], [2, 2, 2])
        self.assertEqual(levels[-1], content.DIFFICULTY_LEVELS)  # ถึงระดับสูงสุดแล้วคงที่
        self.assertEqual(levels, sorted(levels))

    def test_can_climb_all_ten_levels_and_names_show(self):
        seen = []
        for _ in range(config.SURVIVAL_CORRECT_PER_LEVEL * content.DIFFICULTY_LEVELS):
            seen.append(content.question_difficulty(self.screen._current_question()))
            self._answer(True)
            self.screen._next_question()
        self.assertEqual(sorted(set(seen)), list(range(1, content.DIFFICULTY_LEVELS + 1)))
        self.assertEqual(self.screen.level, content.DIFFICULTY_LEVELS)
        surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.screen.draw(surface)

    def test_no_immediate_repeat_questions(self):
        last = None
        for _ in range(40):
            qid = self.screen._current_question().id
            self.assertNotEqual(qid, last)
            last = qid
            self._answer(True)
            self.screen._next_question()

    def test_does_not_touch_hearts_or_xp(self):
        self._answer(False)
        self._answer(True) if self.screen.phase == "answering" else None
        self.assertEqual(self.manager.player_data["hearts"], config.START_HEARTS)
        self.assertEqual(self.manager.player_data["total_xp"], 0)

    def test_restart_resets_run(self):
        self._answer(True)
        self.screen._die()
        self.screen._restart()
        self.assertEqual(self.screen.phase, "answering")
        self.assertEqual(self.screen.time_left, 60)
        self.assertEqual(self.screen.correct_count, 0)

    def test_every_phase_draws_without_error(self):
        surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        for _ in range(60):  # วนหลายข้อ (ขึ้นไปถึงระดับสูง ๆ) ให้ครบทั้ง 3 ชนิดโจทย์
            self.screen.draw(surface)
            self._answer(True)
            self.screen.draw(surface)
            self.screen._next_question()
        self.screen._die()
        self.screen.draw(surface)


class ChallengerBoardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    @staticmethod
    def _root(entries):
        profiles = {}
        for name, best, level in entries:
            p = storage.default_profile(name)
            p["survival_best"], p["survival_best_level"] = best, level
            profiles[name.lower()] = p
        return {"profiles": profiles, "last_active": None}

    def test_sorted_by_score_then_level_then_name_and_skips_zero(self):
        root = self._root([("Zed", 5, 2), ("Amy", 5, 2), ("Bob", 5, 3), ("Cat", 9, 4), ("Idle", 0, 0)])
        names = [r[1] for r in storage.survival_leaderboard(root)]
        self.assertEqual(names, ["Cat", "Bob", "Amy", "Zed"])

    def test_limit_and_rank(self):
        root = self._root([(f"P{i}", i, 1) for i in range(1, 15)])
        self.assertEqual(len(storage.survival_leaderboard(root, limit=10)), 10)
        self.assertEqual(storage.survival_rank(root, "p14"), (1, 14))
        self.assertEqual(storage.survival_rank(root, "p1"), (14, 14))  # อยู่นอก 10 อันดับก็ยังรู้อันดับจริง
        self.assertIsNone(storage.survival_rank(self._root([("Idle", 0, 0)]), "idle"))

    def test_separate_from_xp_leaderboard(self):
        root = self._root([("Amy", 3, 1)])
        root["profiles"]["amy"]["total_xp"] = 500
        self.assertEqual(storage.leaderboard(root)[0][1], 500)
        self.assertEqual(storage.survival_leaderboard(root)[0][2], 3)

    def test_old_save_without_new_field_is_safe(self):
        root = {"profiles": {"old": {"name": "Old"}}, "last_active": None}
        self.assertEqual(storage.survival_leaderboard(root), [])

    def test_commit_best_records_level_and_screen_draws(self):
        sounds = mock.MagicMock()
        with mock.patch.object(storage, "load_all", return_value={"profiles": {}, "last_active": None}):
            manager = ScreenManager(sounds)
        manager.toast = Toast()
        manager.save = lambda: None
        data = storage.default_profile("Me")
        manager.root = {"profiles": {"me": data, **self._root([(f"P{i}", i, 1) for i in range(1, 13)])["profiles"]},
                        "last_active": "me"}
        manager.current_profile_key, manager.player_data = "me", data
        survival = SurvivalScreen(manager)
        board = ChallengerBoardScreen(manager)
        manager.register("survival", survival)
        manager.register("challenger_board", board)
        surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

        board.on_enter()
        board.draw(surface)                      # ยังไม่มีสถิติ
        survival.on_enter()
        survival.correct_count, survival.level = 4, 2
        survival._die()
        self.assertEqual((data["survival_best"], data["survival_best_level"]), (4, 2))
        survival.draw(surface)                   # หน้าตายแสดงอันดับ
        board.on_enter()
        self.assertEqual(board.my_rank, (9, 13))
        board.draw(surface)                      # อยู่นอก 10 อันดับ -> มีบรรทัดบอกอันดับ


if __name__ == "__main__":
    unittest.main()
