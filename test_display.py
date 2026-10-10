"""ทดสอบการคำนวณการปรับขนาดหน้าต่าง (รัน: python -m unittest test_display -v) ไม่ต้องใช้ pygame"""
import unittest

from game.display import compute_viewport, window_to_logical, initial_window_size


class ViewportTests(unittest.TestCase):
    def test_same_size_no_offset(self):
        self.assertEqual(compute_viewport(900, 640, 900, 640), (1.0, 0, 0, 900, 640))

    def test_wide_window_letterboxes_sides(self):
        scale, ox, oy, w, h = compute_viewport(1800, 640, 900, 640)
        self.assertEqual((scale, h, oy), (1.0, 640, 0))
        self.assertEqual((w, ox), (900, 450))

    def test_tall_window_letterboxes_top_bottom(self):
        scale, ox, oy, w, h = compute_viewport(900, 1280, 900, 640)
        self.assertEqual((scale, ox, w, h), (1.0, 0, 900, 640))
        self.assertEqual(oy, 320)

    def test_scale_up_keeps_aspect_ratio(self):
        scale, ox, oy, w, h = compute_viewport(1800, 1280, 900, 640)
        self.assertEqual((scale, w, h, ox, oy), (2.0, 1800, 1280, 0, 0))

    def test_mouse_mapping_roundtrip(self):
        vp = compute_viewport(1800, 1000, 900, 640)
        scale, ox, oy, _w, _h = vp
        for logical in [(0, 0), (450, 320), (899, 639)]:
            win = (ox + logical[0] * scale, oy + logical[1] * scale)
            x, y = window_to_logical(win, vp)
            self.assertAlmostEqual(x, logical[0], places=6)
            self.assertAlmostEqual(y, logical[1], places=6)

    def test_click_in_letterbox_is_outside_canvas(self):
        vp = compute_viewport(1800, 640, 900, 640)
        x, _ = window_to_logical((10, 100), vp)
        self.assertLess(x, 0)

    def test_initial_size_fits_desktop_and_keeps_ratio(self):
        for dw, dh in [(1920, 1080), (1366, 768), (2560, 1440), (1280, 720)]:
            w, h = initial_window_size(dw, dh, 900, 640)
            self.assertLessEqual(w, dw)
            self.assertLessEqual(h, dh)
            self.assertAlmostEqual(w / h, 900 / 640, delta=0.02)

    def test_initial_size_1080p(self):
        self.assertEqual(initial_window_size(1920, 1080, 900, 640), (1366, 972))


if __name__ == "__main__":
    unittest.main()
