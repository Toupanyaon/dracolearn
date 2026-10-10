"""ทดสอบเลย์เอาต์หน้าสรุปผล: ทุกส่วนต้องไม่ซ้อนกัน ไม่ว่าจะมีคำศัพท์กี่คำ/ใส่ชุดแต่งตัวอะไร
รัน: python -m unittest test_summary_layout -v  (ไม่ต้องมีหน้าต่าง/เสียงจริง)
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import unittest
from unittest import mock

import pygame

from game import config, content, mascot, storage
from game.screens import summary as summary_mod
from game.screens.base import ScreenManager
from game.screens.summary import SummaryScreen
from game.widgets import Toast


class SummaryLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    def setUp(self):
        with mock.patch.object(storage, "load_all", return_value={"profiles": {}, "last_active": None}):
            self.manager = ScreenManager(mock.MagicMock())
        self.manager.toast = Toast()
        self.screen = SummaryScreen(self.manager)
        self.lesson = content.UNITS[0].lessons[0]
        self.surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    def tearDown(self):
        mascot.set_outfit({})

    def _enter(self, words):
        self.manager.context = {"lesson_summary": {"correct": 14, "wrong": 0, "xp_earned": 160,
                                "elapsed_seconds": 90, "lesson_title": "ทดสอบ", "vocab_learned": words},
                                "replay_lesson": self.lesson}
        self.screen.on_enter()

    def _check_layout(self, words):
        self._enter(words)
        screen_rect = pygame.Rect(0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        buttons = [self.screen.retry_button.rect, self.screen.dashboard_button.rect]
        for btn in self.screen.vocab_buttons:
            r = btn.rect
            self.assertTrue(screen_rect.contains(r), f"ปุ่มคำศัพท์ล้นจอ {r}")
            self.assertGreaterEqual(r.top, summary_mod.VOCAB_TOP)
            self.assertLessEqual(r.bottom, summary_mod.VOCAB_BOTTOM)
            self.assertFalse(r.colliderect(summary_mod.STAT_CARD), "ปุ่มคำศัพท์ทับการ์ดสถิติ")
            for b in buttons:
                self.assertFalse(r.colliderect(b), "ปุ่มคำศัพท์ทับปุ่มด้านล่าง")
        rects = [b.rect for b in self.screen.vocab_buttons]
        for i, a in enumerate(rects):
            for b in rects[i + 1:]:
                self.assertFalse(a.colliderect(b), "ปุ่มคำศัพท์ซ้อนกันเอง")
        # หัวข้อคำศัพท์ต้องอยู่ใต้การ์ดสถิติและเหนือแถวปุ่มแรก
        if rects:
            self.assertGreater(summary_mod.HINT_Y - 10, summary_mod.STAT_CARD.bottom)
            self.assertLess(summary_mod.HINT_Y + 12, min(r.top for r in rects))
        self.screen.draw(self.surface)  # วาดจริงต้องไม่พัง

    def test_fixed_elements_do_not_overlap(self):
        size = summary_mod.MASCOT_SIZE
        cy = summary_mod.MASCOT_CENTER_Y
        mascot_bottom = cy + size * 1.06 + size * 0.04          # หาง + แอนิเมชันลอยตัว
        mascot_top = cy - size * 0.95 - size * 0.04             # หมวกสูงสุด
        self.assertGreaterEqual(mascot_top, 0)
        self.assertLess(mascot_bottom, summary_mod.TITLE_Y - 18)  # ชื่อบทสูง ~36 px
        self.assertLess(summary_mod.TITLE_Y + 22, summary_mod.STAT_CARD.top)
        self.assertLess(summary_mod.STAT_CARD.bottom, summary_mod.HINT_Y - 10)
        self.assertLess(summary_mod.VOCAB_BOTTOM, summary_mod.BUTTON_Y)
        self.assertLessEqual(summary_mod.BUTTON_Y + 54, config.SCREEN_HEIGHT)

    def test_every_lesson_fits(self):
        for unit in content.UNITS:
            for lesson in unit.lessons:
                self.lesson = lesson
                words = sorted({q.vocab for q in content.get_questions(lesson.question_ids) if q.vocab})
                self._check_layout(words)
                self.assertEqual(self.screen.vocab_hidden, 0, lesson.id)

    def test_no_vocab(self):
        self._check_layout([])

    def test_huge_vocab_list_is_trimmed_not_overflowing(self):
        words = [f"Long vocabulary word {i}" for i in range(60)]
        self._check_layout(words)
        self.assertGreater(self.screen.vocab_hidden, 0)
        self.assertEqual(len(self.screen.vocab_buttons) + self.screen.vocab_hidden, 60)

    def test_all_hats_and_outfits_draw(self):
        for hat in ("none", "party", "crown", "flame", "wizard", "horns"):
            mascot.set_outfit({"hat": hat, "glasses": "star", "neck": "cape", "color": "gold"})
            self._check_layout(["Hello", "Thank you"])


if __name__ == "__main__":
    unittest.main()
