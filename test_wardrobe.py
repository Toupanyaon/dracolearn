"""ทดสอบระบบแต่งตัวมาสคอต (รัน: python -m unittest test_wardrobe -v)
ไม่ต้องมีหน้าต่าง/เสียงจริง: ตั้ง SDL เป็นโหมด dummy ให้ก่อน import pygame
"""
import json
import os
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import types
import unittest
from unittest import mock

import pygame

from game import config, content, mascot, storage, wardrobe
from game.screens.base import ScreenManager
from game.screens.dashboard import DashboardScreen
from game.screens.wardrobe import WardrobeScreen
from game.widgets import Toast

MOODS = ["happy", "excited", "sad", "worried", "sleepy"]


def profile(**overrides):
    data = storage.default_profile("tester")
    data.update(overrides)
    return data


class CatalogTests(unittest.TestCase):
    def test_ids_and_names_are_unique(self):
        ids = [i.id for i in wardrobe.ITEMS]
        self.assertEqual(len(ids), len(set(ids)))
        names = [i.name for i in wardrobe.ITEMS]
        self.assertEqual(len(names), len(set(names)))
        self.assertNotIn(wardrobe.NONE_ID, ids)

    def test_every_item_is_in_a_valid_slot_and_every_slot_has_items(self):
        for item in wardrobe.ITEMS:
            self.assertIn(item.slot, wardrobe.SLOTS, item.id)
        for slot in wardrobe.SLOTS:
            self.assertGreaterEqual(len(wardrobe.items_in_slot(slot)), 4, slot)

    def test_every_item_has_a_drawing(self):
        drawers = {"hat": mascot.HAT_DRAWERS, "glasses": mascot.GLASSES_DRAWERS, "neck": mascot.NECK_DRAWERS,
                   "color": mascot.PALETTES}
        for item in wardrobe.ITEMS:
            self.assertIn(item.id, drawers[item.slot], f"{item.id} ไม่มีฟังก์ชันวาด/พาเลตสี")
        for slot, table in drawers.items():     # และไม่มีฟังก์ชันวาดที่ไม่มีของในแคตตาล็อก
            for ident in table:
                self.assertIn(ident, wardrobe.ITEM_MAP, ident)
                self.assertEqual(wardrobe.ITEM_MAP[ident].slot, slot, ident)

    def test_palettes_have_four_valid_colors(self):
        for name, palette in mascot.PALETTES.items():
            self.assertEqual(len(palette), 4, name)
            for rgb in palette:
                self.assertEqual(len(rgb), 3)
                self.assertTrue(all(0 <= c <= 255 for c in rgb), name)

    def test_default_outfit_is_valid_and_free(self):
        self.assertEqual(wardrobe.normalize_outfit(wardrobe.DEFAULT_OUTFIT), wardrobe.DEFAULT_OUTFIT)
        self.assertTrue(wardrobe.is_unlocked(wardrobe.ITEM_MAP[wardrobe.DEFAULT_OUTFIT["color"]], profile()))

    def test_conditions_are_valid(self):
        for item in wardrobe.ITEMS:
            kind = item.condition[0]
            self.assertIn(kind, ("free", "level", "lessons", "achievement", "survival_level"), item.id)
            if kind == "achievement":
                self.assertIn(item.condition[1], content.ACHIEVEMENT_MAP, item.id)
            if kind == "survival_level":
                self.assertIn(item.condition[1], range(1, content.DIFFICULTY_LEVELS + 1), item.id)
            if kind == "lessons":
                self.assertLessEqual(item.condition[1], len(content.all_lessons_flat()), item.id)
            self.assertTrue(wardrobe.requirement_text(item).strip(), item.id)

    def test_there_are_free_items_and_hard_rewards_for_the_top_challenger_level(self):
        free = [i.id for i in wardrobe.ITEMS if i.condition == ("free",)]
        self.assertEqual(sorted(free), ["bowtie", "orange", "party"])
        for ident in ("flame", "gold"):    # ของที่โหดที่สุด = ต้องถึงระดับสูงสุดของ Challenger
            self.assertEqual(wardrobe.ITEM_MAP[ident].condition, ("survival_level", content.DIFFICULTY_LEVELS))


class UnlockTests(unittest.TestCase):
    def test_new_player_only_has_free_items(self):
        self.assertEqual(sorted(wardrobe.unlocked_ids(profile())), ["bowtie", "orange", "party"])
        self.assertEqual(wardrobe.unlocked_count(profile()), (3, len(wardrobe.ITEMS)))

    def test_level_condition_boundary(self):
        chef = wardrobe.ITEM_MAP["chef"]          # เลเวล 3 = 200 XP
        self.assertFalse(wardrobe.is_unlocked(chef, profile(total_xp=199)))
        self.assertTrue(wardrobe.is_unlocked(chef, profile(total_xp=200)))

    def test_lessons_condition_counts_unique_completed_lessons(self):
        scarf = wardrobe.ITEM_MAP["scarf"]        # เรียนจบ 3 บท
        self.assertFalse(wardrobe.is_unlocked(scarf, profile(completed_lessons=["u1l1", "u1l1", "u1l2"])))
        self.assertTrue(wardrobe.is_unlocked(scarf, profile(completed_lessons=["u1l1", "u1l2", "u1l3"])))

    def test_achievement_condition(self):
        sun = wardrobe.ITEM_MAP["sunglasses"]
        self.assertFalse(wardrobe.is_unlocked(sun, profile()))
        self.assertTrue(wardrobe.is_unlocked(sun, profile(unlocked_achievements=["streak_3"])))

    def test_survival_level_condition_uses_best_level_ever_reached(self):
        horns = wardrobe.ITEM_MAP["horns"]        # Challenger ระดับ 7
        self.assertFalse(wardrobe.is_unlocked(horns, profile(survival_best_level=6)))
        self.assertTrue(wardrobe.is_unlocked(horns, profile(survival_best_level=7)))
        self.assertTrue(wardrobe.is_unlocked(horns, profile(survival_best_level=10)))

    def test_requirement_text_mentions_level_names(self):
        self.assertIn("Wicked Demon", wardrobe.requirement_text(wardrobe.ITEM_MAP["horns"]))
        self.assertIn("เลเวล 8", wardrobe.requirement_text(wardrobe.ITEM_MAP["crown"]))
        self.assertIn(content.ACHIEVEMENT_MAP["perfect_lesson"].title, wardrobe.requirement_text(wardrobe.ITEM_MAP["medal"]))

    def test_max_player_unlocks_everything(self):
        everything = profile(total_xp=5000, completed_lessons=[l.id for _, l in content.all_lessons_flat()],
                             unlocked_achievements=list(content.ACHIEVEMENT_MAP), survival_best_level=10)
        self.assertEqual(len(wardrobe.unlocked_ids(everything)), len(wardrobe.ITEMS))


class OutfitTests(unittest.TestCase):
    def test_normalize_handles_garbage(self):
        for bad in (None, "x", 5, [], {"hat": 3}, {"hat": "unknown", "color": "nope"}):
            self.assertEqual(wardrobe.normalize_outfit(bad), wardrobe.DEFAULT_OUTFIT, bad)

    def test_normalize_rejects_item_in_wrong_slot(self):
        out = wardrobe.normalize_outfit({"hat": "round", "glasses": "crown"})
        self.assertEqual(out["hat"], "none")
        self.assertEqual(out["glasses"], "none")

    def test_normalize_color_can_never_be_none(self):
        self.assertEqual(wardrobe.normalize_outfit({"color": "none"})["color"], "orange")

    def test_normalize_with_data_drops_locked_items(self):
        out = wardrobe.normalize_outfit({"hat": "crown", "color": "gold", "neck": "bowtie"}, profile())
        self.assertEqual(out, {"hat": "none", "glasses": "none", "neck": "bowtie", "color": "orange"})

    def test_normalize_keeps_unlocked_items(self):
        data = profile(total_xp=800)
        out = wardrobe.normalize_outfit({"hat": "crown", "color": "blue"}, data)
        self.assertEqual((out["hat"], out["color"]), ("crown", "blue"))

    def test_equip_unlocked_item(self):
        data = profile()
        self.assertTrue(wardrobe.equip(data, "party"))
        self.assertEqual(data["outfit"]["hat"], "party")

    def test_equip_locked_or_unknown_item_fails_and_changes_nothing(self):
        data = profile()
        before = dict(wardrobe.normalize_outfit(data["outfit"]))
        for ident in ("crown", "gold", "nope", "hat:wizard", "color:none", "bogus:none"):
            self.assertFalse(wardrobe.equip(data, ident), ident)
        self.assertEqual(wardrobe.normalize_outfit(data["outfit"]), before)

    def test_equip_replaces_item_in_same_slot_only(self):
        data = profile(total_xp=300)
        wardrobe.equip(data, "party")
        wardrobe.equip(data, "bowtie")
        wardrobe.equip(data, "chef")
        self.assertEqual((data["outfit"]["hat"], data["outfit"]["neck"]), ("chef", "bowtie"))

    def test_take_off_one_slot(self):
        data = profile()
        wardrobe.equip(data, "party")
        self.assertTrue(wardrobe.equip(data, "hat:none"))
        self.assertEqual(data["outfit"]["hat"], "none")

    def test_undress_keeps_color(self):
        data = profile(total_xp=300)
        for ident in ("party", "bowtie", "blue"):
            wardrobe.equip(data, ident)
        wardrobe.undress(data)
        self.assertEqual(data["outfit"], {"hat": "none", "glasses": "none", "neck": "none", "color": "blue"})

    def test_newly_unlocked_announces_once_and_skips_free_items(self):
        data = profile()
        self.assertEqual(wardrobe.newly_unlocked(data), [])
        data["total_xp"] = 400                      # เลเวล 5 -> หมวกเชฟ(3) แว่นกลม(2) สีฟ้า(4)
        fresh = {i.id for i in wardrobe.newly_unlocked(data)}
        self.assertEqual(fresh, {"chef", "round", "blue"})
        self.assertEqual(wardrobe.newly_unlocked(data), [])      # แจ้งแล้วไม่แจ้งซ้ำ
        data["total_xp"] = 600                      # เลเวล 7 -> แว่นดาว(6) สีมิ้นต์(6)
        self.assertEqual({i.id for i in wardrobe.newly_unlocked(data)}, {"star", "mint"})


class StorageTests(unittest.TestCase):
    def test_default_profile_has_outfit_fields(self):
        data = storage.default_profile("x")
        self.assertEqual(data["outfit"], wardrobe.DEFAULT_OUTFIT)
        self.assertEqual(data["outfit_seen"], [])

    def test_old_save_without_outfit_loads_with_defaults(self):
        old = {"profiles": {"kim": {"name": "Kim", "total_xp": 123, "completed_lessons": ["u1l1"]}}, "last_active": "kim"}
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "save.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(old, f)
            with mock.patch.object(config, "SAVE_FILE", path):
                root = storage.load_all()
        kim = root["profiles"]["kim"]
        self.assertEqual(kim["total_xp"], 123)                    # ข้อมูลเดิมไม่หาย
        self.assertEqual(kim["outfit"], wardrobe.DEFAULT_OUTFIT)
        self.assertEqual(kim["outfit_seen"], [])

    def test_outfit_round_trips_through_save_file(self):
        data = profile(total_xp=300)
        wardrobe.equip(data, "chef")
        wardrobe.equip(data, "blue")
        root = {"profiles": {"tester": data}, "last_active": "tester"}
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "save.json")
            with mock.patch.object(config, "SAVE_FILE", path):
                storage.save_all(root)
                loaded = storage.load_all()
        self.assertEqual(loaded["profiles"]["tester"]["outfit"]["hat"], "chef")
        self.assertEqual(loaded["profiles"]["tester"]["outfit"]["color"], "blue")

    def test_reset_profile_resets_outfit(self):
        data = profile(total_xp=300)
        wardrobe.equip(data, "chef")
        root = {"profiles": {"tester": data}, "last_active": "tester"}
        storage.reset_profile(root, "tester")
        self.assertEqual(root["profiles"]["tester"]["outfit"], wardrobe.DEFAULT_OUTFIT)
        self.assertEqual(root["profiles"]["tester"]["outfit_seen"], [])


def make_manager(data=None):
    sounds = mock.MagicMock()
    with mock.patch.object(storage, "load_all", return_value={"profiles": {}, "last_active": None}), \
            mock.patch.object(storage, "save_all"):
        manager = ScreenManager(sounds)
    manager.toast = Toast()
    manager.save = mock.MagicMock()
    if data is not None:
        manager.player_data = data
        manager.root = {"profiles": {"tester": data}, "last_active": "tester"}
        manager.current_profile_key = "tester"
    return manager


class ManagerSyncTests(unittest.TestCase):
    def tearDown(self):
        mascot.set_outfit(None)

    def test_apply_outfit_sets_the_mascot_outfit(self):
        data = profile(total_xp=300, outfit={"hat": "chef", "glasses": "none", "neck": "none", "color": "blue"})
        manager = make_manager(data)
        manager.apply_outfit()
        self.assertEqual(mascot.get_outfit()["hat"], "chef")
        self.assertEqual(mascot.get_outfit()["color"], "blue")

    def test_tampered_save_with_locked_items_is_sanitized(self):
        data = profile(outfit={"hat": "flame", "glasses": "none", "neck": "cape", "color": "gold"})
        manager = make_manager(data)
        manager.apply_outfit()
        self.assertEqual(data["outfit"], wardrobe.DEFAULT_OUTFIT)
        self.assertEqual(mascot.get_outfit(), wardrobe.DEFAULT_OUTFIT)

    def test_switch_profile_loads_that_players_outfit_and_logout_resets(self):
        manager = make_manager()
        other = profile(total_xp=300, outfit={"hat": "chef", "glasses": "none", "neck": "none", "color": "blue"})
        manager.root = {"profiles": {"mali": other}, "last_active": None}
        manager.screens["home"] = mock.MagicMock()
        with mock.patch.object(storage, "save_all"):
            manager.switch_profile("Mali")
        self.assertEqual(mascot.get_outfit()["hat"], "chef")
        manager.logout()
        self.assertEqual(mascot.get_outfit(), wardrobe.DEFAULT_OUTFIT)

    def test_set_outfit_with_garbage_never_breaks_drawing(self):
        mascot.set_outfit({"hat": "???", "color": 12})
        self.assertEqual(mascot.get_outfit(), wardrobe.DEFAULT_OUTFIT)


class MascotDrawingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    def test_every_item_draws_in_every_mood_and_size(self):
        surface = pygame.Surface((400, 400))
        for item in wardrobe.ITEMS:
            outfit = dict(wardrobe.DEFAULT_OUTFIT)
            outfit[item.slot] = item.id
            for mood in MOODS:
                for size in (40, 70, 110, 140):
                    mascot.draw_mascot(surface, (200, 200), size=size, mood=mood, t=1.3, outfit=outfit)

    def test_full_outfit_and_unknown_outfit_entries_draw(self):
        surface = pygame.Surface((400, 400))
        mascot.draw_mascot(surface, (200, 200), outfit={"hat": "wizard", "glasses": "star", "neck": "cape", "color": "gold"})
        mascot.draw_mascot(surface, (200, 200), outfit={})        # ช่องหาย -> ใช้ค่าเริ่มต้นของช่องนั้น (ไม่พัง)

    def test_default_call_signature_still_works(self):
        mascot.draw_mascot(pygame.Surface((300, 300)), (150, 150), 120, "happy", 0.0)


class WardrobeScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    def setUp(self):
        self.data = profile(total_xp=300, completed_lessons=["u1l1"], survival_best_level=0)
        self.manager = make_manager(self.data)
        self.screen = WardrobeScreen(self.manager)
        self.manager.register("wardrobe", self.screen)
        self.manager.register("dashboard", mock.MagicMock())
        self.surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.screen.on_enter()
        self.screen.draw(self.surface)

    def tearDown(self):
        mascot.set_outfit(None)

    def _press(self, button):
        for kind in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            self.screen.handle_event(types.SimpleNamespace(type=kind, pos=button.rect.center, button=1))

    def _click_card(self, item_id):
        rect = dict((i, r) for r, i in self.screen.card_rects)[item_id]
        self.screen.handle_event(types.SimpleNamespace(type=pygame.MOUSEBUTTONUP, pos=rect.center, button=1))
        self.screen.draw(self.surface)

    def test_card_grid_matches_the_slot_items(self):
        ids = [i for _, i in self.screen.card_rects]
        self.assertEqual(ids[0], "hat:none")
        self.assertEqual(ids[1:], [i.id for i in wardrobe.items_in_slot("hat")])
        self.screen.tab = "color"
        self.screen.draw(self.surface)
        self.assertEqual([i for _, i in self.screen.card_rects], [i.id for i in wardrobe.items_in_slot("color")])

    def test_cards_fit_inside_the_grid_area_in_every_tab(self):
        area = pygame.Rect(*__import__("game.screens.wardrobe", fromlist=["GRID_AREA"]).GRID_AREA)
        for slot in wardrobe.SLOTS:
            self.screen.tab = slot
            self.screen.draw(self.surface)
            for rect, _ in self.screen.card_rects:
                self.assertTrue(area.contains(rect), (slot, rect))

    def test_clicking_unlocked_card_equips_saves_and_updates_mascot(self):
        self._click_card("chef")                       # เลเวล 4 (300 XP) ปลดล็อกแล้ว
        self.assertEqual(self.data["outfit"]["hat"], "chef")
        self.assertEqual(mascot.get_outfit()["hat"], "chef")
        self.manager.save.assert_called()

    def test_clicking_locked_card_shows_requirement_and_does_not_equip(self):
        with mock.patch.object(self.manager.toast, "show") as toast_show:
            self._click_card("crown")
        self.assertEqual(self.data["outfit"]["hat"], "none")
        toast_show.assert_called_once()
        self.assertIn("เลเวล 8", toast_show.call_args[0][0])

    def test_none_card_takes_item_off(self):
        self._click_card("chef")
        self._click_card("hat:none")
        self.assertEqual(self.data["outfit"]["hat"], "none")

    def test_tab_buttons_switch_tabs(self):
        for slot in wardrobe.SLOTS:
            self._press(self.screen.tab_buttons[slot])
            self.assertEqual(self.screen.tab, slot)
            self.screen.draw(self.surface)

    def test_equipping_in_different_tabs_combines(self):
        self._click_card("chef")
        self._press(self.screen.tab_buttons["color"]); self.screen.draw(self.surface)
        self._click_card("blue")
        self._press(self.screen.tab_buttons["neck"]); self.screen.draw(self.surface)
        self._click_card("bowtie")
        self.assertEqual((self.data["outfit"]["hat"], self.data["outfit"]["color"], self.data["outfit"]["neck"]),
                         ("chef", "blue", "bowtie"))

    def test_undress_button_keeps_color(self):
        self._click_card("chef")
        self._press(self.screen.tab_buttons["color"]); self.screen.draw(self.surface)
        self._click_card("blue")
        self._press(self.screen.undress_button)
        self.assertEqual(self.data["outfit"], {"hat": "none", "glasses": "none", "neck": "none", "color": "blue"})

    def test_random_button_only_uses_unlocked_items(self):
        unlocked = set(wardrobe.unlocked_ids(self.data))
        for _ in range(60):
            self._press(self.screen.random_button)
            for slot in wardrobe.SLOTS:
                value = self.data["outfit"][slot]
                self.assertTrue(value in unlocked or value == wardrobe.NONE_ID, (slot, value))
            self.assertNotEqual(self.data["outfit"]["color"], wardrobe.NONE_ID)

    def test_back_button_goes_to_dashboard(self):
        with mock.patch.object(self.manager, "go_to") as go_to:
            self._press(self.screen.back_button)
        go_to.assert_called_once_with("dashboard")

    def test_entering_sanitizes_and_marks_new_items_as_seen(self):
        self.data["outfit"] = {"hat": "flame", "glasses": "none", "neck": "none", "color": "orange"}
        self.screen.on_enter()
        self.assertEqual(self.data["outfit"]["hat"], "none")
        self.assertEqual(wardrobe.newly_unlocked(self.data), [])    # เข้าตู้แล้ว = เห็นของใหม่แล้ว

    def test_draws_in_every_state(self):
        for slot in wardrobe.SLOTS:
            self.screen.tab = slot
            for _ in range(2):
                self.screen.update(0.05)
                self.screen.draw(self.surface)
        maxed = profile(total_xp=5000, unlocked_achievements=list(content.ACHIEVEMENT_MAP), survival_best_level=10,
                        completed_lessons=[l.id for _, l in content.all_lessons_flat()])
        self.manager.player_data = maxed
        for slot in wardrobe.SLOTS:
            self.screen.tab = slot
            self.screen.draw(self.surface)


class DashboardIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    def setUp(self):
        self.data = profile(total_xp=400)
        self.manager = make_manager(self.data)
        self.screen = DashboardScreen(self.manager)
        self.manager.register("dashboard", self.screen)

    def _click(self, pos):
        self.screen.handle_event(types.SimpleNamespace(type=pygame.MOUSEBUTTONUP, pos=pos, button=1))

    def test_unlock_toast_is_shown_once(self):
        with mock.patch.object(self.manager.toast, "show") as toast_show:
            self.screen.on_enter()
            self.screen.on_enter()
        toast_show.assert_called_once()
        self.assertIn("3 ชิ้น", toast_show.call_args[0][0])         # หมวกเชฟ แว่นกลม สีฟ้า
        self.manager.save.assert_called()

    def test_no_toast_for_player_without_new_items(self):
        self.manager.player_data = profile()
        with mock.patch.object(self.manager.toast, "show") as toast_show:
            self.screen.on_enter()
        toast_show.assert_not_called()

    def test_wardrobe_button_and_mascot_click_open_the_wardrobe(self):
        self.manager.register("wardrobe", mock.MagicMock())
        with mock.patch.object(self.manager, "go_to") as go_to:
            for btn_pos in (self.screen.wardrobe_button.rect.center, self.screen.mascot_rect.center):
                self.screen.handle_event(types.SimpleNamespace(type=pygame.MOUSEBUTTONDOWN, pos=btn_pos, button=1))
                self._click(btn_pos)
        self.assertEqual([c.args for c in go_to.call_args_list], [("wardrobe",), ("wardrobe",)])

    def test_wardrobe_controls_do_not_overlap_other_dashboard_controls(self):
        others = [self.screen.profile_button, self.screen.settings_button, self.screen.board_button,
                  self.screen.survival_button, self.screen.path_button, self.screen.continue_button]
        for rect in (self.screen.wardrobe_button.rect, self.screen.mascot_rect):
            for other in others:
                self.assertFalse(rect.colliderect(other.rect), (rect, other.text))
        self.assertFalse(self.screen.wardrobe_button.rect.colliderect(self.screen.mascot_rect))

    def test_dashboard_draws_with_a_full_outfit(self):
        for ident in ("chef", "round", "bowtie", "blue"):
            wardrobe.equip(self.data, ident)
        self.manager.apply_outfit()
        self.screen.draw(pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT)))
        mascot.set_outfit(None)


if __name__ == "__main__":
    unittest.main()
