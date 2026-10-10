"""ทดสอบการสลับตำแหน่งตัวเลือก (mcq / listen_mcq) ทั้งโหมดปกติและโหมด Challenger
(รัน: python -m unittest test_option_shuffle -v)"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import random
import types
import unittest
from collections import Counter
from unittest import mock

import pygame

from game import config, content, storage
from game.screens.base import ScreenManager
from game.screens.lesson import LessonScreen
from game.screens.survival import SurvivalScreen
from game.widgets import Toast

CHOICE_TYPES = ("mcq", "listen_mcq")


def choice_questions():
    return [q for q in content.QUESTIONS if q.qtype in CHOICE_TYPES]


class ShuffleBase:
    screen_cls = None

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    def setUp(self):
        with mock.patch.object(storage, "load_all", return_value={"profiles": {}, "last_active": None}), \
                mock.patch.object(storage, "save_all"):
            self.manager = ScreenManager(mock.MagicMock())
        self.manager.toast = Toast()
        self.manager.save = lambda: None
        self.manager.player_data = storage.default_profile("tester")
        self.screen = self.screen_cls(self.manager)
        self.surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.setup_screen()

    def setup_screen(self):
        raise NotImplementedError

    def show(self, q):
        self.screen.questions = [q]
        self.screen.index = 0
        self.screen._setup_question()
        self.screen.draw(self.surface)

    def quick_shown(self, q):
        """ตั้งข้อใหม่แล้วคืนตัวเลือกที่สลับแล้วโดยไม่วาดจอ (ใช้กับเทสต์สถิติที่วนเยอะ ๆ ให้เร็ว)"""
        self.screen.questions = [q]
        self.screen.index = 0
        self.screen._setup_question()
        return list(self.screen.shown_options)

    def drawn_options(self):
        return [option for _, option in self.screen.mcq_option_rects]

    # ---------------- เทสต์ ----------------
    def test_shown_options_are_a_permutation_of_the_original(self):
        for q in choice_questions():
            original = list(q.options)
            self.show(q)
            self.assertEqual(Counter(self.drawn_options()), Counter(original), q.id)
            self.assertEqual(q.options, original, f"{q.id}: ห้ามแก้ลำดับ options ในคลังโจทย์")

    def test_correct_answer_appears_in_every_position(self):
        random.seed(2024)
        q = content.QUESTION_MAP["q1"]
        positions = Counter()
        for _ in range(240):
            positions[self.quick_shown(q).index(q.correct_answer)] += 1
        self.assertEqual(sorted(positions), [0, 1, 2, 3])
        for slot, n in positions.items():          # เฉลี่ย 60 ครั้งต่อช่อง ไม่ควรเอียงเกินไป
            self.assertGreater(n, 30, (slot, n))

    def test_correct_answer_is_no_longer_stuck_in_the_first_slot_across_the_bank(self):
        random.seed(7)
        first = total = 0
        for q in choice_questions():
            for _ in range(6):
                total += 1
                first += self.quick_shown(q)[0] == q.correct_answer
        self.assertLess(first / total, 0.35)       # สุ่มล้วนควรได้ ~25% (ก่อนแก้ ~99%)
        self.assertGreater(first / total, 0.15)

    def test_order_is_stable_across_redraws_and_feedback(self):
        q = content.QUESTION_MAP["q1"]
        self.show(q)
        first = self.drawn_options()
        for _ in range(5):
            self.screen.draw(self.surface)
            self.assertEqual(self.drawn_options(), first)
        self.screen.selected_option = q.correct_answer
        self.screen._check_answer()                # เข้าเฟสเฉลย ตัวเลือกต้องไม่ขยับ
        self.screen.draw(self.surface)
        self.assertEqual(self.drawn_options(), first)

    def test_new_question_gets_a_new_shuffle(self):
        random.seed(11)
        q = content.QUESTION_MAP["q1"]
        orders = set()
        for _ in range(30):
            orders.add(tuple(self.quick_shown(q)))
        self.assertGreater(len(orders), 5)

    def test_clicking_a_slot_selects_the_option_shown_there(self):
        random.seed(5)
        q = content.QUESTION_MAP["q1"]
        self.show(q)
        for slot in range(4):
            rect, shown = self.screen.mcq_option_rects[slot]
            self.screen.handle_event(types.SimpleNamespace(type=pygame.MOUSEBUTTONUP, pos=rect.center, button=1))
            self.assertEqual(self.screen.selected_option, shown)
            self.assertEqual(self.screen.selected_option, self.drawn_options()[slot])

    def test_grading_follows_the_text_not_the_position(self):
        random.seed(3)
        q = content.QUESTION_MAP["q1"]
        for _ in range(20):
            self.show(q)
            slot = self.drawn_options().index(q.correct_answer)
            rect, _ = self.screen.mcq_option_rects[slot]
            self.screen.handle_event(types.SimpleNamespace(type=pygame.MOUSEBUTTONUP, pos=rect.center, button=1))
            self.screen._check_answer()
            self.assertTrue(self.screen.was_correct)
            wrong_slot = (slot + 1) % 4
            self.show(q)
            wrong = next(o for o in self.drawn_options() if o != q.correct_answer)
            self.screen.selected_option = wrong
            self.screen._check_answer()
            self.assertFalse(self.screen.was_correct)

    def test_listening_choice_questions_are_shuffled_too(self):
        random.seed(9)
        q = content.QUESTION_MAP["l5"]             # listen_mcq
        seen = set()
        for _ in range(60):
            seen.add(self.quick_shown(q).index(q.correct_answer))
        self.assertEqual(seen, {0, 1, 2, 3})

    def test_stale_shuffle_from_previous_question_is_replaced(self):
        a, b = content.QUESTION_MAP["q1"], content.QUESTION_MAP["q2"]
        self.show(a)
        self.screen.questions = [b]                # เปลี่ยนข้อโดยไม่ผ่าน _setup_question ก็ต้องไม่โชว์ตัวเลือกของข้อเก่า
        self.screen.draw(self.surface)
        self.assertEqual(Counter(self.drawn_options()), Counter(b.options))

    def test_non_choice_questions_still_draw_and_grade(self):
        for q in content.QUESTIONS:
            if q.qtype in ("word_order", "translate_type", "listen_type"):
                self.show(q)
                kind = self.screen._kind(q)
                if kind == "word_order":
                    self.screen.built_words = q.correct_answer.split()
                    self.screen.word_tiles = []
                else:
                    self.screen.text_input.text = q.correct_answer
                self.screen._check_answer()
                self.assertTrue(self.screen.was_correct, q.id)


class NormalModeShuffleTests(ShuffleBase, unittest.TestCase):
    screen_cls = LessonScreen

    def setup_screen(self):
        unit, lesson = content.UNITS[0], content.UNITS[0].lessons[0]
        self.manager.context = {"active_unit": unit, "active_lesson": lesson}
        self.screen.on_enter()

    def test_lesson_flow_shuffles_each_question_it_enters(self):
        random.seed(21)
        self.screen.on_enter()
        first_slots = Counter()
        for i in range(len(self.screen.questions)):
            q = self.screen._current_question()
            self.screen.draw(self.surface)
            if q.qtype in CHOICE_TYPES:
                first_slots[self.drawn_options().index(q.correct_answer)] += 1
            if i < len(self.screen.questions) - 1:
                self.screen.index += 1
                self.screen._setup_question()
        self.assertGreater(len(first_slots), 1)    # ทั้งบทเฉลยต้องไม่อยู่ช่องเดียวตลอด


class ChallengerShuffleTests(ShuffleBase, unittest.TestCase):
    screen_cls = SurvivalScreen

    def setup_screen(self):
        self.manager.register("survival", self.screen)
        self.screen.on_enter()

    def test_challenger_hard_levels_are_shuffled(self):
        random.seed(33)
        hard = [q for q in choice_questions() if q.id in content.CHALLENGER_QUESTION_IDS]
        self.assertGreater(len(hard), 20)
        first = total = 0
        for q in hard:
            for _ in range(6):
                total += 1
                first += self.quick_shown(q)[0] == q.correct_answer
        self.assertLess(first / total, 0.35)


if __name__ == "__main__":
    unittest.main()
