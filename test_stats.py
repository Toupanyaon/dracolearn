"""ทดสอบหน้าสถิติ: เก็บสถิติ, ตรรกะคำนวณ (game/stats.py), เซฟเก่า, และการวาดหน้า (pygame ล้วน)"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import types
import unittest
from datetime import date, timedelta
from unittest import mock

import pygame

from game import config, content, storage, stats
from game.screens.base import ScreenManager
from game.screens.stats import StatsScreen
from game.screens.dashboard import DashboardScreen
from game.screens.lesson import LessonScreen
from game.widgets import Toast

TODAY = date(2026, 10, 10)


class StorageTests(unittest.TestCase):
    def test_defaults_have_stat_fields(self):
        p = storage.default_profile("a")
        self.assertEqual((p["xp_history"], p["unit_stats"], p["question_stats"]), ({}, {}, {}))

    def test_add_xp_accumulates_into_today_history(self):
        p = storage.default_profile("a")
        storage.add_xp(p, 10); storage.add_xp(p, 20)
        self.assertEqual(p["xp_history"][storage.today_str()], 30)
        self.assertEqual(p["total_xp"], 30)

    def test_add_xp_survives_corrupt_history(self):
        p = storage.default_profile("a"); p["xp_history"] = "oops"
        storage.add_xp(p, 5)
        self.assertEqual(p["xp_history"][storage.today_str()], 5)

    def test_history_is_pruned(self):
        p = storage.default_profile("a")
        old = (date.today() - timedelta(days=storage.XP_HISTORY_DAYS + 5)).isoformat()
        p["xp_history"][old] = 99
        storage.add_xp(p, 1)
        self.assertNotIn(old, p["xp_history"])

    def test_record_answer_counts_unit_and_question(self):
        p = storage.default_profile("a")
        storage.record_answer(p, "q1", True, "u1"); storage.record_answer(p, "q1", False, "u1")
        storage.record_answer(p, "q2", False, "u2")
        self.assertEqual(p["unit_stats"]["u1"], {"correct": 1, "wrong": 1})
        self.assertEqual(p["unit_stats"]["u2"], {"correct": 0, "wrong": 1})
        self.assertEqual(p["question_stats"]["q1"], {"c": 1, "w": 1})

    def test_record_answer_survives_corrupt_fields(self):
        p = storage.default_profile("a"); p["unit_stats"] = []; p["question_stats"] = None
        storage.record_answer(p, "q1", True, "u1")
        self.assertEqual(p["unit_stats"]["u1"]["correct"], 1)
        self.assertEqual(p["question_stats"]["q1"]["c"], 1)

    def test_old_save_is_migrated_and_today_xp_seeded(self):
        import json, tempfile
        today = storage.today_str()
        old = {"profiles": {"x": {"name": "x", "total_xp": 50, "daily_xp_today": 40, "daily_xp_date": today}},
               "last_active": "x"}
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "s.json")
            json.dump(old, open(path, "w"))
            with mock.patch.object(config, "SAVE_FILE", path):
                root = storage.load_all()
        prof = root["profiles"]["x"]
        self.assertEqual(prof["xp_history"], {today: 40})
        self.assertEqual(prof["unit_stats"], {})
        self.assertEqual(prof["challenger_runs"], 0)

    def test_corrupt_types_in_save_are_repaired(self):
        import json, tempfile
        bad = {"profiles": {"x": {"name": "x", "xp_history": [1], "unit_stats": 5, "question_stats": "s"}}}
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "s.json")
            json.dump(bad, open(path, "w"))
            with mock.patch.object(config, "SAVE_FILE", path):
                prof = storage.load_all()["profiles"]["x"]
        self.assertEqual((prof["xp_history"], prof["unit_stats"], prof["question_stats"]), ({}, {}, {}))


class ContentTests(unittest.TestCase):
    def test_every_lesson_question_has_a_home_unit(self):
        for qid in content.LESSON_QUESTION_IDS:
            self.assertIn(content.unit_id_of_question(qid), content.UNIT_MAP)

    def test_challenger_only_question_maps_to_challenger(self):
        qid = next(iter(content.CHALLENGER_QUESTION_IDS - content.LESSON_QUESTION_IDS))
        self.assertEqual(content.unit_id_of_question(qid), "challenger")
        self.assertEqual(content.unit_id_of_question("nope"), "challenger")


class XpSeriesTests(unittest.TestCase):
    def test_seven_days_oldest_first_today_last(self):
        s = stats.xp_last_days({}, 7, TODAY)
        self.assertEqual(len(s), 7)
        self.assertEqual(s[-1].day, TODAY); self.assertTrue(s[-1].is_today)
        self.assertEqual(s[0].day, TODAY - timedelta(days=6))
        self.assertEqual(sum(d.is_today for d in s), 1)
        self.assertTrue(all(d.xp == 0 for d in s))

    def test_values_come_from_history_and_missing_days_are_zero(self):
        h = {TODAY.isoformat(): 30, (TODAY - timedelta(days=2)).isoformat(): 70,
             (TODAY - timedelta(days=9)).isoformat(): 500}
        s = stats.xp_last_days({"xp_history": h}, 7, TODAY)
        self.assertEqual([d.xp for d in s], [0, 0, 0, 0, 70, 0, 30])

    def test_weekday_labels(self):
        s = stats.xp_last_days({}, 7, TODAY)  # 2026-10-10 เป็นวันเสาร์
        self.assertEqual(s[-1].label, "ส.")
        self.assertEqual(s[-2].label, "ศ.")

    def test_corrupt_values_are_treated_as_zero(self):
        h = {TODAY.isoformat(): "abc", (TODAY - timedelta(days=1)).isoformat(): -5,
             (TODAY - timedelta(days=2)).isoformat(): True}
        s = stats.xp_last_days({"xp_history": h}, 7, TODAY)
        self.assertTrue(all(d.xp == 0 for d in s))
        self.assertEqual(len(stats.xp_last_days({"xp_history": 7}, 7, TODAY)), 7)

    def test_nice_axis_max(self):
        for peak, want in [(0, 10), (10, 10), (11, 20), (45, 50), (100, 100), (101, 150), (1000, 1000), (1001, 1500)]:
            self.assertEqual(stats.nice_axis_max(peak), want, peak)
        for peak in range(0, 3000, 7):
            self.assertGreaterEqual(stats.nice_axis_max(peak), peak)

    def test_summary(self):
        h = {TODAY.isoformat(): 30, (TODAY - timedelta(days=2)).isoformat(): 70}
        s = stats.xp_summary({"xp_history": h}, 7, TODAY)
        self.assertEqual((s["total"], s["average"], s["active_days"], s["best_xp"]), (100, 14, 2, 70))
        self.assertEqual(s["best_day"], TODAY - timedelta(days=2))
        self.assertIsNone(stats.xp_summary({}, 7, TODAY)["best_day"])


class AccuracyTests(unittest.TestCase):
    def test_rows_are_units_then_challenger(self):
        rows = stats.unit_accuracy({})
        self.assertEqual([r.unit_id for r in rows], [u.id for u in content.UNITS] + ["challenger"])
        self.assertTrue(all(r.percent is None for r in rows))
        self.assertIsNone(stats.overall_accuracy({}))

    def test_percentages(self):
        d = {"unit_stats": {"u1": {"correct": 3, "wrong": 1}, "u2": {"correct": 0, "wrong": 2},
                            "challenger": {"correct": 1, "wrong": 0}}}
        rows = {r.unit_id: r for r in stats.unit_accuracy(d)}
        self.assertEqual(rows["u1"].percent, 75); self.assertEqual(rows["u2"].percent, 0)
        self.assertEqual(rows["challenger"].percent, 100); self.assertIsNone(rows["u3"].percent)
        self.assertEqual(stats.overall_accuracy(d), round(100 * 4 / 7))

    def test_levels(self):
        self.assertEqual([stats.accuracy_level(p) for p in (None, 100, 80, 79, 60, 59, 0)],
                         ["none", "good", "good", "ok", "ok", "bad", "bad"])

    def test_corrupt_unit_stats(self):
        d = {"unit_stats": {"u1": "x", "u2": {"correct": "a", "wrong": -3}, "u3": [1]}}
        self.assertEqual(len(stats.unit_accuracy(d)), 6)
        self.assertIsNone(stats.overall_accuracy(d))


class TopicTests(unittest.TestCase):
    def test_sorted_by_wrong_count_and_limited(self):
        qids = sorted(content.QUESTION_MAP)[:8]
        qs = {qid: {"c": 1, "w": i + 1} for i, qid in enumerate(qids)}
        t = stats.wrong_topics({"question_stats": qs}, 5)
        self.assertEqual(len(t), 5)
        self.assertEqual([x.wrong for x in t], [8, 7, 6, 5, 4])

    def test_ignores_never_wrong_unknown_and_corrupt(self):
        qid = sorted(content.QUESTION_MAP)[0]
        qs = {qid: {"c": 5, "w": 0}, "ghost": {"c": 0, "w": 9}, "bad": "x", "bad2": {"w": "z"}}
        self.assertEqual(stats.wrong_topics({"question_stats": qs}), [])
        self.assertEqual(stats.wrong_topics({}), [])

    def test_tie_break_by_percent_wrong_then_id(self):
        a, b = sorted(content.QUESTION_MAP)[:2]
        qs = {a: {"c": 5, "w": 2}, b: {"c": 0, "w": 2}}
        self.assertEqual([t.qid for t in stats.wrong_topics({"question_stats": qs})], [b, a])

    def test_topic_has_title_and_location(self):
        qid = "q1"
        t = stats.topic_of_question(qid)
        self.assertTrue(t.title); self.assertIn("Greetings", t.where)
        ch = next(iter(content.CHALLENGER_QUESTION_IDS - content.LESSON_QUESTION_IDS))
        self.assertEqual(stats.topic_of_question(ch).where, "Challenger")
        self.assertIsNone(stats.topic_of_question("ghost"))


def _manager():
    sounds = mock.MagicMock()
    with mock.patch.object(storage, "load_all", return_value={"profiles": {}, "last_active": None}), \
            mock.patch.object(storage, "save_all"):
        m = ScreenManager(sounds)
    m.toast = Toast(); m.save = lambda: None
    m.player_data = storage.default_profile("tester")
    return m


class ScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init(); pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    def setUp(self):
        self.m = _manager()
        self.screen = StatsScreen(self.m)
        self.m.register("stats", self.screen)
        self.surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    def _fill(self):
        d = self.m.player_data
        for i in range(7):
            d["xp_history"][(date.today() - timedelta(days=i)).isoformat()] = 30 * (i + 1)
        for u, c, w in (("u1", 9, 1), ("u2", 6, 4), ("u3", 1, 9), ("challenger", 4, 4)):
            d["unit_stats"][u] = {"correct": c, "wrong": w}
        for i, qid in enumerate(sorted(content.QUESTION_MAP)[:6]):
            d["question_stats"][qid] = {"c": 1, "w": i + 1}

    def test_draws_empty_without_error_and_shows_empty_messages(self):
        self.screen.on_enter()
        for _ in range(60):
            self.screen.update(0.02); self.screen.draw(self.surface)
        self.assertEqual(self.screen.topics, [])

    def test_draws_full_data_at_every_animation_step(self):
        self._fill(); self.screen.on_enter()
        for _ in range(60):
            self.screen.update(0.02); self.screen.draw(self.surface)
        self.assertEqual(len(self.screen.topics), 5)
        self.assertEqual(len(self.screen.series), 7)

    def test_chart_actually_draws_bars_pixels_change(self):
        self.screen.on_enter(); self.screen.update(5); self.screen.draw(self.surface)
        empty = self.surface.copy()
        self._fill(); self.screen.on_enter(); self.screen.update(5); self.screen.draw(self.surface)
        region = pygame.Rect(30, 96, 424, 262)
        a = pygame.image.tostring(empty.subsurface(region), "RGB")
        b = pygame.image.tostring(self.surface.subsurface(region), "RGB")
        self.assertNotEqual(a, b)

    def test_cards_do_not_overlap_and_fit_screen(self):
        from game.screens import stats as sc
        cards = [sc.XP_CARD, sc.ACC_CARD, sc.TOPIC_CARD]
        screen = pygame.Rect(0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        for c in cards:
            self.assertTrue(screen.contains(c))
        for i in range(3):
            for j in range(i + 1, 3):
                self.assertFalse(cards[i].colliderect(cards[j]))

    def test_back_button_returns_to_dashboard(self):
        went = []
        self.m.go_to = lambda key, **k: went.append(key)
        self.screen.on_enter()
        pos = self.screen.back_button.rect.center
        for t in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            self.screen.handle_event(types.SimpleNamespace(type=t, pos=pos, button=1))
        self.assertEqual(went, ["dashboard"])

    def test_fit_truncates_long_text(self):
        from game.screens.stats import _fit
        f = config.get_font(17)
        out = _fit(f, "x" * 200, 100)
        self.assertTrue(out.endswith("…")); self.assertLessEqual(f.size(out)[0], 100)
        self.assertEqual(_fit(f, "ok", 100), "ok")

    def test_corrupt_profile_does_not_crash_screen(self):
        self.m.player_data.update(xp_history=None, unit_stats="x", question_stats=[1])
        self.screen.on_enter(); self.screen.draw(self.surface)


class HookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init(); pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    def test_lesson_answers_are_recorded_per_unit(self):
        m = _manager(); s = LessonScreen(m); m.register("lesson", s)
        unit = content.UNITS[0]; lesson = unit.lessons[0]
        m.context = {"active_unit": unit, "active_lesson": lesson}
        s.on_enter()
        q = s._current_question()
        kind = s._kind(q)
        if kind == "mcq": s.selected_option = q.correct_answer
        elif kind == "word_order": s.built_words = q.correct_answer.split()
        else: s.text_input.text = q.correct_answer
        s._check_answer()
        self.assertEqual(m.player_data["unit_stats"][unit.id]["correct"], 1)
        self.assertEqual(m.player_data["question_stats"][q.id]["c"], 1)
        self.assertEqual(m.player_data["xp_history"][storage.today_str()], config.XP_PER_CORRECT)

    def test_dashboard_has_working_stats_button(self):
        m = _manager(); d = DashboardScreen(m)
        went = []
        m.go_to = lambda key, **k: went.append(key)
        pos = d.stats_button.rect.center
        for t in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            d.handle_event(types.SimpleNamespace(type=t, pos=pos, button=1))
        self.assertEqual(went, ["stats"])
        # ปุ่มไม่ชนปุ่มอื่นบนแดชบอร์ด
        others = [d.profile_button, d.settings_button, d.wardrobe_button, d.survival_button,
                  d.board_button, d.path_button, d.continue_button]
        for b in others:
            self.assertFalse(d.stats_button.rect.colliderect(b.rect), b.text)
        self.assertFalse(d.stats_button.rect.colliderect(d.mascot_rect))
        d.draw(pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT)))


if __name__ == "__main__":
    unittest.main()
