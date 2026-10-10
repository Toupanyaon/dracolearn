"""ทดสอบสีหน้า/อารมณ์ของมาสคอต (รัน: python -m unittest test_mascot_moods -v)
ไม่ต้องมีหน้าต่าง/เสียงจริง: ตั้ง SDL เป็นโหมด dummy ให้ก่อน import pygame
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import itertools
import unittest
from unittest import mock

import pygame

from game import config, content, mascot, storage
from game.screens.base import Screen, ScreenManager
from game.screens.lesson import LessonScreen
from game.screens.survival import LOW_TIME_SECONDS, SurvivalScreen
from game.widgets import Toast

NO_OUTFIT = {"hat": "none", "glasses": "none", "neck": "none", "color": "orange"}


def render(mood, size=120, t=1.0, outfit=NO_OUTFIT, bg=(0, 0, 0, 0)):
    surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
    surf.fill(bg)
    mascot.draw_mascot(surf, (size * 2, size * 1.6), size=size, mood=mood, t=t, outfit=outfit)
    return surf


def diff_pixels(a, b):
    ba, bb = pygame.image.tostring(a, "RGBA"), pygame.image.tostring(b, "RGBA")
    return sum(1 for i in range(0, len(ba), 4) if ba[i:i + 4] != bb[i:i + 4])


class MoodDrawingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    def test_mood_list_matches_what_the_app_uses(self):
        self.assertEqual(set(mascot.MOODS), {"happy", "excited", "sad", "worried", "sleepy"})

    def test_every_pair_of_moods_looks_clearly_different(self):
        # t คงที่เพื่อเทียบหน้าตาล้วน ๆ - ต้องต่างกันเยอะพอจะเห็นชัด ไม่ใช่แค่ปากเปลี่ยนนิดเดียว
        for size, need in ((120, 400), (70, 120)):
            shots = {m: render(m, size) for m in mascot.MOODS}
            for a, b in itertools.combinations(mascot.MOODS, 2):
                self.assertGreater(diff_pixels(shots[a], shots[b]), need, f"{a} vs {b} @ {size}px คล้ายกันเกินไป")

    def test_brows_eyes_and_mouth_all_change_between_happy_and_sad(self):
        # แยกดูทีละส่วนของใบหน้า: ตา (แถบกลางหน้า), คิ้ว (แถบบน), ปาก (แถบล่าง) ต้องต่างกันทั้งสามส่วน
        size = 120
        a, b = render("happy", size), render("sad", size)
        cx, cy, hr = size * 2, size * 1.6, size * 0.5
        bands = {"brows": (-0.62, -0.28), "eyes": (-0.28, 0.15), "mouth": (0.3, 0.75)}
        for name, (y0, y1) in bands.items():
            rect = pygame.Rect(int(cx - hr * 0.8), int(cy + hr * y0), int(hr * 1.6), int(hr * (y1 - y0)))
            self.assertGreater(diff_pixels(a.subsurface(rect), b.subsurface(rect)), 40, f"ส่วน {name} ไม่ต่างกัน")

    def test_unknown_mood_falls_back_to_happy(self):
        self.assertEqual(diff_pixels(render("grumpy"), render("happy")), 0)

    def test_every_mood_draws_at_every_size_without_error_and_on_screen_parts(self):
        for mood in mascot.MOODS:
            for size in (24, 40, 70, 110, 140, 220):
                for t in (0.0, 0.7, 3.3, 12.9):
                    surf = render(mood, size, t)
                    self.assertGreater(surf.get_bounding_rect().width, size * 0.5)

    def test_extras_stay_close_to_the_head(self):
        # ประกายดาว/Z/เหงื่อ ต้องไม่ลอยสูงเหนือหัวไกล (กันไปทับข้อความที่วางเหนือมาสคอต)
        size = 110
        hr = size * 0.5
        for mood in mascot.MOODS:
            for t in (0.0, 0.5, 1.0, 1.7, 2.9, 5.1):
                bound = render(mood, size, t).get_bounding_rect()
                self.assertGreaterEqual(bound.top, size * 1.6 - hr * 1.35, f"{mood} t={t}: ลอยสูงเกิน")

    def test_all_outfits_in_all_moods_still_draw(self):
        from game import wardrobe
        for item in wardrobe.ITEMS:
            outfit = dict(NO_OUTFIT)
            outfit[item.slot] = item.id
            for mood in mascot.MOODS:
                render(mood, 60, 2.0, outfit)

    def test_brows_are_drawn_over_glasses(self):
        # คนใส่แว่นดำก็ต้องเห็นคิ้ว: เทียบแว่นดำ+worried กับ แว่นดำ+happy แล้วแถบคิ้วต้องต่างกัน
        outfit = dict(NO_OUTFIT, glasses="sunglasses")
        size = 120
        a, b = render("worried", size, outfit=outfit), render("happy", size, outfit=outfit)
        cx, cy, hr = size * 2, size * 1.6, size * 0.5
        rect = pygame.Rect(int(cx - hr * 0.8), int(cy - hr * 0.62), int(hr * 1.6), int(hr * 0.3))
        self.assertGreater(diff_pixels(a.subsurface(rect), b.subsurface(rect)), 30)

    def test_does_not_mutate_global_outfit(self):
        before = mascot.get_outfit()
        render("excited", 80, outfit={"hat": "crown", "glasses": "star", "neck": "cape", "color": "gold"})
        self.assertEqual(mascot.get_outfit(), before)


class _Stub(Screen):
    def draw(self, surface):
        pass


class ScreenMoodTests(unittest.TestCase):
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
        self.data = storage.default_profile("t")
        self.manager.player_data = self.data
        self.manager.root = {"profiles": {"t": self.data}, "last_active": "t"}
        self.manager.current_profile_key = "t"
        for key, cls in (("lesson", LessonScreen), ("survival", SurvivalScreen), ("dashboard", _Stub),
                         ("summary", _Stub)):
            self.manager.register(key, cls(self.manager))
        self.surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    def _lesson(self):
        unit = content.UNITS[0]
        self.manager.go_to("lesson", active_unit=unit, active_lesson=unit.lessons[0])
        return self.manager.current

    def _answer(self, ls, correct):
        with mock.patch.object(content, "is_correct_answer", return_value=correct), \
                mock.patch.object(ls, "_has_answer", return_value=True), \
                mock.patch.object(ls, "_submitted_answer_text", return_value="x"):
            ls._check_answer()

    def test_reaction_mood_stays_for_the_whole_feedback_phase(self):
        ls = self._lesson()
        self._answer(ls, True)
        self.assertEqual(ls.mascot_mood, "excited")
        for _ in range(300):          # 5 วินาทีที่ยังดูเฉลยอยู่ (เดิมกลับเป็น happy หลัง 1.2 วิ)
            ls.update(1 / 60)
        self.assertEqual(ls.phase, "feedback")
        self.assertEqual(ls._display_mood(), "excited")

    def test_wrong_answer_stays_sad_in_feedback_then_resets_on_next_question(self):
        ls = self._lesson()
        self._answer(ls, False)
        for _ in range(240):
            ls.update(1 / 60)
        self.assertEqual(ls._display_mood(), "sad")
        ls._next_question()
        self.assertEqual(ls.phase, "answering")
        self.assertEqual(ls.mascot_mood, "happy")

    def test_last_heart_makes_idle_mascot_worried(self):
        ls = self._lesson()
        self.data["hearts"] = 1
        self.assertEqual(ls._display_mood(), "worried")
        self.data["hearts"] = 3
        self.assertEqual(ls._display_mood(), "happy")

    def test_survival_low_time_makes_mascot_worried(self):
        self.manager.go_to("survival")
        sv = self.manager.current
        self.assertEqual(sv._display_mood(), "happy")
        sv.time_left = LOW_TIME_SECONDS - 0.1
        self.assertEqual(sv._display_mood(), "worried")
        sv.mascot_mood = "excited"        # ปฏิกิริยาตอบถูกมาก่อนความกังวล
        self.assertEqual(sv._display_mood(), "excited")

    def test_out_of_hearts_screen_draws_with_sad_mascot(self):
        ls = self._lesson()
        ls.phase = "out_of_hearts"
        ls.draw(self.surface)

    def test_lesson_and_survival_draw_in_every_phase(self):
        ls = self._lesson()
        ls.draw(self.surface)
        self._answer(ls, False)
        ls.draw(self.surface)
        self.manager.go_to("survival")
        sv = self.manager.current
        sv.time_left = 5
        sv.draw(self.surface)


if __name__ == "__main__":
    unittest.main()
