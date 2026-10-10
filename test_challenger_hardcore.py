"""ทดสอบ Challenger แบบโหด: คอมโบ, ไอเท็มช่วยชีวิต (50:50 / แช่แข็ง / ข้าม), บอส, สถิติสะสม"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import types
import unittest
from unittest import mock

import pygame

from game import config, content, storage
from game.screens.base import ScreenManager
from game.screens.survival import SurvivalScreen, LIFELINES
from game.widgets import Toast


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init(); pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    def setUp(self):
        sounds = mock.MagicMock()
        with mock.patch.object(storage, "load_all", return_value={"profiles": {}, "last_active": None}), \
                mock.patch.object(storage, "save_all"):
            self.manager = ScreenManager(sounds)
        self.manager.toast = Toast(); self.manager.save = lambda: None
        self.manager.player_data = storage.default_profile("tester")
        self.screen = SurvivalScreen(self.manager)
        self.manager.register("survival", self.screen)
        self.screen.on_enter()
        self.surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    def answer(self, correct=True):
        s = self.screen; q = s._current_question(); kind = s._kind(q)
        if kind == "mcq":
            s.selected_option = q.correct_answer if correct else next(o for o in q.options if o != q.correct_answer)
        elif kind == "word_order":
            s.built_words = q.correct_answer.split() if correct else ["zzz"]
        else:
            s.text_input.text = q.correct_answer if correct else "zzz"
        s._check_answer()

    def mcq(self):
        """บังคับให้ข้อปัจจุบันเป็นข้อเลือกตอบ 4 ตัวเลือก"""
        q = next(q for q in content.QUESTIONS if q.qtype == "mcq" and len(q.options) >= 4)
        self.screen.questions = [q]; self.screen.index = 0; self.screen._setup_question()
        self.screen.draw(self.surface)
        return q

    def click(self, rect):
        for t in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            self.screen.handle_event(types.SimpleNamespace(type=t, pos=rect.center, button=1))


class ComboTests(Base):
    def test_bonus_formula(self):
        f = SurvivalScreen.combo_bonus
        self.assertEqual([f(n) for n in (0, 1, 2, 3, 5, 6, 9, 15, 30, 99)], [0, 0, 0, 1, 1, 2, 3, 5, 5, 5])

    def test_combo_grows_and_adds_time(self):
        t0 = self.screen.time_left
        gained = []
        for _ in range(3):
            before = self.screen.time_left
            self.answer(True); gained.append(self.screen.time_left - before)
            self.screen._next_question()
        self.assertEqual(gained, [5, 5, 6])   # คอมโบ 3 ได้ +1
        self.assertEqual(self.screen.combo, 3)
        self.assertEqual(self.screen.time_left, t0 + 16)

    def test_wrong_resets_combo_but_keeps_best(self):
        for _ in range(4):
            self.answer(True); self.screen._next_question()
        self.answer(False)
        self.assertEqual(self.screen.combo, 0)
        self.assertEqual(self.screen.best_combo, 4)

    def test_feedback_text_mentions_combo(self):
        for _ in range(2):
            self.answer(True); self.screen._next_question()
        self.answer(True)
        self.assertIn("คอมโบ x3", self.screen._feedback_text())
        self.assertIn("+6", self.screen._feedback_text())

    def test_bonus_is_capped(self):
        self.screen.combo = 200
        before = self.screen.time_left
        self.answer(True)
        self.assertEqual(self.screen.time_left - before, config.SURVIVAL_CORRECT_BONUS + config.SURVIVAL_COMBO_BONUS_MAX)


class LifelineTests(Base):
    def test_start_with_one_of_each(self):
        self.assertEqual(self.screen.lifelines, {"fifty": 1, "freeze": 1, "skip": 1})

    def test_fifty_fifty_hides_two_wrong_options_and_keeps_correct(self):
        q = self.mcq()
        self.assertTrue(self.screen.use_lifeline("fifty"))
        hidden = self.screen.hidden_options
        self.assertEqual(len(hidden), 2)
        self.assertNotIn(q.correct_answer, hidden)
        self.assertTrue(hidden <= set(q.options))
        self.screen.draw(self.surface)
        shown = [o for _, o in self.screen.mcq_option_rects]
        self.assertEqual(len(shown), len(q.options) - 2)
        self.assertIn(q.correct_answer, shown)
        self.assertEqual(self.screen.lifelines["fifty"], 0)
        self.assertFalse(self.screen.use_lifeline("fifty"))   # หมดแล้ว

    def test_fifty_fifty_clears_a_hidden_selected_option(self):
        q = self.mcq()
        wrong = next(o for o in q.options if o != q.correct_answer)
        self.screen.selected_option = wrong
        with mock.patch("game.screens.survival.random.sample", return_value=[wrong, [o for o in q.options if o not in (wrong, q.correct_answer)][0]]):
            self.screen.use_lifeline("fifty")
        self.assertIsNone(self.screen.selected_option)

    def test_fifty_fifty_unavailable_for_typing_questions_and_costs_nothing(self):
        q = next(q for q in content.QUESTIONS if q.qtype == "translate_type")
        self.screen.questions = [q]; self.screen.index = 0; self.screen._setup_question()
        self.assertFalse(self.screen.can_use_lifeline("fifty"))
        self.assertFalse(self.screen.use_lifeline("fifty"))
        self.assertEqual(self.screen.lifelines["fifty"], 1)

    def test_hidden_options_reset_on_next_question(self):
        self.mcq(); self.screen.use_lifeline("fifty")
        self.screen._ask_next_question()
        self.assertEqual(self.screen.hidden_options, set())

    def test_clicking_a_hidden_option_position_is_not_possible(self):
        self.mcq(); self.screen.use_lifeline("fifty"); self.screen.draw(self.surface)
        for rect, opt in self.screen.mcq_option_rects:
            self.assertNotIn(opt, self.screen.hidden_options)

    def test_freeze_stops_the_clock_then_resumes(self):
        self.assertTrue(self.screen.use_lifeline("freeze"))
        t = self.screen.time_left
        for _ in range(10):
            self.screen.update(0.1)       # 1.0 วินาที
        self.assertEqual(self.screen.time_left, t)
        self.assertAlmostEqual(self.screen.freeze_left, config.SURVIVAL_FREEZE_SECONDS - 1.0, places=5)
        for _ in range(100):
            self.screen.update(0.1)       # เกินเวลาแช่แข็ง
        self.assertEqual(self.screen.freeze_left, 0)
        self.assertLess(self.screen.time_left, t)

    def test_freeze_cannot_stack(self):
        self.screen.lifelines["freeze"] = 3
        self.assertTrue(self.screen.use_lifeline("freeze"))
        self.assertFalse(self.screen.use_lifeline("freeze"))
        self.assertEqual(self.screen.lifelines["freeze"], 2)

    def test_skip_gives_new_question_without_penalty_or_count(self):
        first = self.screen._current_question().id
        t = self.screen.time_left
        self.assertTrue(self.screen.use_lifeline("skip"))
        self.assertNotEqual(self.screen._current_question().id, first)
        self.assertEqual((self.screen.time_left, self.screen.correct_count, self.screen.wrong_count), (t, 0, 0))
        self.assertEqual(self.screen.since_boss, 0)
        self.assertEqual(self.screen.phase, "answering")

    def test_lifelines_unusable_outside_answering_phase(self):
        self.answer(True)    # ตอนนี้อยู่หน้าเฉลย
        for n in LIFELINES:
            self.assertFalse(self.screen.can_use_lifeline(n))

    def test_buttons_work_by_click_and_keyboard(self):
        self.screen.draw(self.surface)
        self.click(self.screen.lifeline_buttons["skip"].rect)
        self.assertEqual(self.screen.lifelines["skip"], 0)
        self.screen.handle_event(types.SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_F2, unicode=""))
        self.assertEqual(self.screen.lifelines["freeze"], 0)
        self.assertGreater(self.screen.freeze_left, 0)

    def test_lifeline_buttons_fit_screen_and_do_not_overlap_game_buttons(self):
        screen = pygame.Rect(0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        game_btns = [self.screen.check_button, self.screen.next_button, self.screen.speak_button]
        rects = [b.rect for b in self.screen.lifeline_buttons.values()]
        for r in rects:
            self.assertTrue(screen.contains(r))
            for g in game_btns:
                self.assertFalse(r.colliderect(g.rect))
        for i in range(3):
            for j in range(i + 1, 3):
                self.assertFalse(rects[i].colliderect(rects[j]))


class BossTests(Base):
    def normal(self, n, correct=True):
        for _ in range(n):
            self.answer(correct); self.screen._next_question()

    def test_boss_appears_after_n_normal_answers(self):
        self.normal(config.SURVIVAL_BOSS_EVERY - 1)
        self.assertIsNone(self.screen.boss)
        self.normal(1)
        self.assertEqual(self.screen.boss, {"done": 0, "total": config.SURVIVAL_BOSS_QUESTIONS})

    def test_boss_counts_wrong_answers_too(self):
        self.normal(config.SURVIVAL_BOSS_EVERY, correct=False) if False else None
        self.screen.time_left = 10_000
        for _ in range(config.SURVIVAL_BOSS_EVERY):
            self.answer(False); self.screen._next_question()
        self.assertIsNotNone(self.screen.boss)

    def test_boss_questions_are_harder(self):
        self.normal(config.SURVIVAL_BOSS_EVERY)
        lvl = self.screen.level
        want = min(content.DIFFICULTY_LEVELS, lvl + config.SURVIVAL_BOSS_LEVEL_BOOST)
        self.assertEqual(content.question_difficulty(self.screen._current_question()), want)

    def test_beating_boss_gives_time_item_and_resets(self):
        self.normal(config.SURVIVAL_BOSS_EVERY)
        items_before = sum(self.screen.lifelines.values())
        t = self.screen.time_left
        for i in range(config.SURVIVAL_BOSS_QUESTIONS):
            self.assertIsNotNone(self.screen.boss)
            self.answer(True)
            if i < config.SURVIVAL_BOSS_QUESTIONS - 1:
                self.assertEqual(self.screen.boss["done"], i + 1)
                self.screen._next_question()
        self.assertIsNone(self.screen.boss)
        self.assertEqual(self.screen.bosses_beaten, 1)
        self.assertEqual(sum(self.screen.lifelines.values()), items_before + 1)
        self.assertGreaterEqual(self.screen.time_left - t, config.SURVIVAL_BOSS_WIN_BONUS)
        self.screen._next_question()
        self.assertIsNone(self.screen.boss)          # ไม่โผล่ติดกัน
        self.assertEqual(self.screen.since_boss, 0)

    def test_losing_boss_costs_extra_time_and_ends_boss(self):
        self.normal(config.SURVIVAL_BOSS_EVERY)
        t = self.screen.time_left
        self.answer(False)
        self.assertIsNone(self.screen.boss)
        self.assertEqual(t - self.screen.time_left, config.SURVIVAL_WRONG_PENALTY + config.SURVIVAL_BOSS_FAIL_PENALTY)
        self.assertEqual(self.screen.bosses_beaten, 0)
        self.assertIn("แพ้บอส", self.screen._feedback_text())

    def test_losing_boss_can_kill(self):
        self.normal(config.SURVIVAL_BOSS_EVERY)
        self.screen.time_left = 12
        self.answer(False)
        self.assertEqual(self.screen.time_left, 0)
        self.screen._next_question()
        self.assertEqual(self.screen.phase, "dead")

    def test_no_lifelines_during_boss(self):
        self.normal(config.SURVIVAL_BOSS_EVERY)
        for n in LIFELINES:
            self.assertFalse(self.screen.use_lifeline(n))
        self.assertEqual(self.screen.lifelines, {"fifty": 1, "freeze": 1, "skip": 1})

    def test_next_boss_comes_again_later(self):
        self.normal(config.SURVIVAL_BOSS_EVERY)
        self.normal(config.SURVIVAL_BOSS_QUESTIONS)      # ชนะบอส
        self.assertIsNone(self.screen.boss)
        self.normal(config.SURVIVAL_BOSS_EVERY)
        self.assertIsNotNone(self.screen.boss)

    def test_restart_clears_everything(self):
        self.normal(config.SURVIVAL_BOSS_EVERY)
        self.screen.use_lifeline("skip") if False else None
        self.screen._restart()
        s = self.screen
        self.assertEqual((s.boss, s.combo, s.best_combo, s.since_boss, s.freeze_left), (None, 0, 0, 0, 0.0))
        self.assertEqual(s.lifelines, {"fifty": 1, "freeze": 1, "skip": 1})
        self.assertEqual(s.hidden_options, set())


class RunStatsTests(Base):
    def test_death_saves_run_stats_once(self):
        for _ in range(4):
            self.answer(True); self.screen._next_question()
        self.screen.time_left = 0.01
        self.screen.update(0.5)
        self.assertEqual(self.screen.phase, "dead")
        d = self.manager.player_data
        self.assertEqual((d["challenger_runs"], d["challenger_best_combo"], d["challenger_bosses_beaten"]), (1, 4, 0))
        self.screen._commit_run()
        self.assertEqual(d["challenger_runs"], 1)       # ไม่นับซ้ำ

    def test_quit_saves_but_empty_run_does_not_count(self):
        self.manager.go_to = lambda *a, **k: None
        self.screen._quit()
        self.assertEqual(self.manager.player_data["challenger_runs"], 0)
        self.screen._restart()
        self.answer(True); self.screen._quit()
        self.assertEqual(self.manager.player_data["challenger_runs"], 1)

    def test_best_combo_is_max_across_runs(self):
        self.manager.go_to = lambda *a, **k: None
        for n in (5, 2):
            self.screen._restart()
            for _ in range(n):
                self.answer(True); self.screen._next_question()
            self.screen._quit()
        d = self.manager.player_data
        self.assertEqual((d["challenger_runs"], d["challenger_best_combo"]), (2, 5))

    def test_challenger_answers_are_counted_under_challenger_unit(self):
        self.answer(True); self.screen._next_question(); self.answer(False)
        self.assertEqual(self.manager.player_data["unit_stats"]["challenger"], {"correct": 1, "wrong": 1})

    def test_challenger_does_not_give_xp(self):
        self.answer(True)
        self.assertEqual(self.manager.player_data["total_xp"], 0)
        self.assertEqual(self.manager.player_data["xp_history"], {})


class DrawTests(Base):
    def test_every_state_draws(self):
        s = self.screen
        s.draw(self.surface)
        s.combo = 7; s.draw(self.surface)
        s.use_lifeline("freeze"); s.draw(self.surface)
        s.boss = {"done": 1, "total": 3}; s.draw(self.surface)
        self.answer(True); s.draw(self.surface)
        s.time_left = 0.0; s._die(); s.draw(self.surface)

    def test_boss_pill_changes_pixels(self):
        self.screen.draw(self.surface); a = pygame.image.tostring(self.surface, "RGB")
        self.screen.boss = {"done": 0, "total": 3}; self.screen.draw(self.surface)
        self.assertNotEqual(a, pygame.image.tostring(self.surface, "RGB"))

    def test_freeze_changes_timer_bar_color(self):
        self.screen.draw(self.surface); a = pygame.image.tostring(self.surface, "RGB")
        self.screen.freeze_left = 5; self.screen.draw(self.surface)
        self.assertNotEqual(a, pygame.image.tostring(self.surface, "RGB"))


if __name__ == "__main__":
    unittest.main()
