import unittest

import pygame

from game import config
from game.widgets import Toast


class ToastWrappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()
        cls.font = config.get_font(20, bold=True)

    def test_long_thai_message_wraps_within_screen_width(self):
        message = (
            "เครื่องนี้ไม่มีเสียงพูดภาษาไทยติดตั้งไว้ จึงอ่านโจทย์ภาษาไทยไม่ได้ "
            "(ลองเพิ่มที่ Windows Settings > Time & Language > Speech)"
        )
        max_width = config.SCREEN_WIDTH - 40 - 32

        lines = Toast._wrap_message(message, self.font, max_width)

        self.assertGreater(len(lines), 1)
        self.assertTrue(all(self.font.size(line)[0] <= max_width for line in lines))

    def test_long_unbroken_text_is_split_to_fit(self):
        max_width = 100
        lines = Toast._wrap_message("ภาษาไทย" * 30, self.font, max_width)

        self.assertGreater(len(lines), 1)
        self.assertTrue(all(self.font.size(line)[0] <= max_width for line in lines))


if __name__ == "__main__":
    unittest.main()
