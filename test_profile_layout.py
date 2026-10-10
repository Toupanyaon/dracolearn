"""ทดสอบเลย์เอาต์หน้าโปรไฟล์/ความสำเร็จ: การ์ดและข้อความต้องไม่ล้นกรอบ แม้ชื่อยากหรือจำนวนความสำเร็จเยอะ"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import unittest
from unittest import mock

import pygame

from game import config, content, storage
from game.models import Achievement
from game.screens.base import ScreenManager
from game.screens.profile import ProfileScreen, wrap_to_width
from game.widgets import Toast


class WrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init(); pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    def test_lines_never_exceed_width_or_line_count(self):
        font = config.get_font(13, bold=True)
        texts = [a.title for a in content.ACHIEVEMENTS] + [a.description for a in content.ACHIEVEMENTS] + \
                ["x" * 80, "ก" * 90, "word " * 30, ""]
        for text in texts:
            for width in (60, 100, 124, 300):
                for n in (1, 2, 3):
                    lines = wrap_to_width(font, text, width, n)
                    self.assertLessEqual(len(lines), max(1, n))
                    for ln in lines:
                        self.assertLessEqual(font.size(ln)[0], width, (text, width, ln))

    def test_short_text_is_untouched(self):
        font = config.get_font(13, bold=True)
        self.assertEqual(wrap_to_width(font, "ไร้ที่ติ", 200, 2), ["ไร้ที่ติ"])

    def test_too_long_gets_ellipsis(self):
        font = config.get_font(13, bold=True)
        lines = wrap_to_width(font, "x" * 200, 80, 2)
        self.assertEqual(len(lines), 2); self.assertTrue(lines[-1].endswith("…"))


class ProfileLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init(); pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    def setUp(self):
        with mock.patch.object(storage, "load_all", return_value={"profiles": {}, "last_active": None}):
            self.m = ScreenManager(mock.MagicMock())
        self.m.toast = Toast(); self.m.save = lambda: None
        self.m.player_data = storage.default_profile("tester")
        self.m.player_data["unlocked_achievements"] = [a.id for a in content.ACHIEVEMENTS]
        self.screen = ProfileScreen(self.m)
        self.surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.scr = pygame.Rect(0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT)

    def _check_boxes_inside_screen(self):
        self.screen.draw(self.surface)
        rects = [r for r, _ in self.screen.achievement_rects]
        self.assertEqual(len(rects), len(content.ACHIEVEMENTS))
        for r in rects:
            self.assertTrue(self.scr.contains(r), r)
        for i in range(len(rects)):
            for j in range(i + 1, len(rects)):
                self.assertFalse(rects[i].colliderect(rects[j]))
        return rects

    def test_all_boxes_inside_screen_and_not_overlapping(self):
        self._check_boxes_inside_screen()

    def test_boxes_stay_inside_the_achievement_card(self):
        rects = self._check_boxes_inside_screen()
        left, right = min(r.left for r in rects), max(r.right for r in rects)
        top, bottom = min(r.top for r in rects), max(r.bottom for r in rects)
        # การ์ดความสำเร็จเริ่มที่ x=40 กว้าง SCREEN_WIDTH-80, y=390 ลงไปถึงขอบจอ-20
        self.assertGreaterEqual(left, 40); self.assertLessEqual(right, config.SCREEN_WIDTH - 40)
        self.assertGreaterEqual(top, 390); self.assertLessEqual(bottom, config.SCREEN_HEIGHT - 20)

    def test_many_more_achievements_still_fit(self):
        extra = [Achievement(f"x{i}", f"ความสำเร็จทดสอบที่ยาวมากเป็นพิเศษหมายเลข {i}", "ทดสอบ", "star") for i in range(10)]
        with mock.patch.object(content, "ACHIEVEMENTS", content.ACHIEVEMENTS + extra):
            self._check_boxes_inside_screen()

    def test_popup_for_every_achievement_draws_inside_popup(self):
        popup = self.screen.ach_popup_rect
        self.assertTrue(self.scr.contains(popup))
        for a in content.ACHIEVEMENTS:
            self.screen.selected_achievement = a.id
            self.screen.draw(self.surface)
        self.assertTrue(popup.contains(self.screen.ach_close_button.rect))

    def test_locked_achievements_also_draw(self):
        self.m.player_data["unlocked_achievements"] = []
        self._check_boxes_inside_screen()


if __name__ == "__main__":
    unittest.main()
