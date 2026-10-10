"""
display.py
----------
ทำให้หน้าต่างเกมปรับขนาดตามหน้าจอ/ผู้เล่น โดยไม่ต้องแก้โค้ดแต่ละหน้าจอ:
  - เกมยังวาดลงผืนผ้าใบ "ขนาดตรรกะ" คงที่ (config.SCREEN_WIDTH x SCREEN_HEIGHT = 900x640)
  - ตอนแสดงผล ขยาย/ย่อผืนผ้าใบให้พอดีหน้าต่าง รักษาอัตราส่วนเดิม (เว้นขอบดำ/ม่วงเข้มด้านข้างถ้าสัดส่วนไม่ตรง)
  - แปลงตำแหน่งเมาส์จากพิกัดหน้าต่างกลับเป็นพิกัดตรรกะ ปุ่ม/การ์ดจึงคลิกตรงตำแหน่งเสมอ
  - เปิดเกมครั้งแรกจะปรับขนาดหน้าต่างเป็น ~90% ของหน้าจอเครื่อง (ไม่ล้นจอ ไม่เล็กเกินไป)
  - ลากขอบเพื่อย่อ/ขยายได้ และกด F11 เพื่อสลับเต็มจอ

ฟังก์ชันคำนวณ (compute_viewport ฯลฯ) ไม่พึ่ง pygame เพื่อให้ทดสอบได้ใน test_display.py
"""

import sys

MIN_WINDOW_W = 450
MIN_WINDOW_H = 320
WINDOW_FRACTION = 0.9  # ขนาดหน้าต่างเริ่มต้นเทียบกับหน้าจอเครื่อง


# ---------------------------------------------------------------------------
# ฟังก์ชันคำนวณล้วน ๆ (ไม่ใช้ pygame)
# ---------------------------------------------------------------------------
def compute_viewport(win_w, win_h, log_w, log_h):
    """คืน (scale, offset_x, offset_y, width, height) ของผืนผ้าใบที่ขยายแล้วให้อยู่กึ่งกลางหน้าต่าง"""
    win_w, win_h = max(1, win_w), max(1, win_h)
    scale = min(win_w / log_w, win_h / log_h)
    w = max(1, int(log_w * scale))
    h = max(1, int(log_h * scale))
    return scale, (win_w - w) // 2, (win_h - h) // 2, w, h


def window_to_logical(pos, viewport):
    """แปลงพิกัดในหน้าต่าง -> พิกัดตรรกะของเกม (viewport ได้จาก compute_viewport)"""
    scale, ox, oy, _w, _h = viewport
    return ((pos[0] - ox) / scale, (pos[1] - oy) / scale)


def initial_window_size(desktop_w, desktop_h, log_w, log_h, fraction=WINDOW_FRACTION):
    """ขนาดหน้าต่างเริ่มต้น: ใหญ่สุดที่พอดี fraction ของหน้าจอ โดยคงอัตราส่วนของเกม"""
    scale = min(desktop_w * fraction / log_w, desktop_h * fraction / log_h)
    scale = max(scale, 0.5)
    return max(MIN_WINDOW_W, int(log_w * scale)), max(MIN_WINDOW_H, int(log_h * scale))


def _enable_windows_dpi_awareness():
    """บน Windows ที่ตั้ง Display scaling (125%/150%) ถ้าไม่ประกาศ DPI-aware หน้าต่างจะเบลอและ
    ขนาดหน้าจอที่อ่านได้จะคลาดเคลื่อน"""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# ตัวจัดการหน้าต่าง
# ---------------------------------------------------------------------------
class ScaledDisplay:
    def __init__(self, log_w, log_h, title="", letterbox_color=(20, 14, 32)):
        import pygame
        self.pygame = pygame
        self.log_w, self.log_h = log_w, log_h
        self.letterbox_color = letterbox_color
        self.fullscreen = False

        _enable_windows_dpi_awareness()

        try:
            info = pygame.display.Info()
            desktop_w, desktop_h = info.current_w, info.current_h
            if desktop_w <= 0 or desktop_h <= 0:
                raise ValueError
        except Exception:
            desktop_w, desktop_h = log_w, log_h  # อ่านขนาดจอไม่ได้ -> ใช้ขนาดเดิม
        self.desktop_size = (desktop_w, desktop_h)
        self.windowed_size = initial_window_size(desktop_w, desktop_h, log_w, log_h)

        self.window = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        if title:
            pygame.display.set_caption(title)

        # ผืนผ้าใบขนาดตรรกะ: ทุกหน้าจอวาดลงที่นี่ (พิกัดเดิม 900x640 ไม่ต้องแก้)
        self.canvas = pygame.Surface((log_w, log_h)).convert()
        self._viewport = compute_viewport(*self.window.get_size(), log_w, log_h)

    # ----------------------------------------------------------------
    def _refresh_window(self):
        self.window = self.pygame.display.get_surface()
        self._viewport = compute_viewport(*self.window.get_size(), self.log_w, self.log_h)

    def toggle_fullscreen(self):
        pygame = self.pygame
        if not self.fullscreen:
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.fullscreen = True
        else:
            self.window = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
            self.fullscreen = False
        self._refresh_window()

    def handle_system_event(self, event):
        """จัดการอีเวนต์ของหน้าต่าง (ย่อ/ขยาย, F11) คืน True ถ้าอีเวนต์นี้ถูกใช้ไปแล้ว ไม่ต้องส่งต่อให้หน้าจอเกม"""
        pygame = self.pygame
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self.toggle_fullscreen()
            return True
        if event.type == pygame.VIDEORESIZE:
            if not self.fullscreen:
                w, h = event.w, event.h
                if w < MIN_WINDOW_W or h < MIN_WINDOW_H:  # กันไม่ให้หน้าต่างเล็กจนใช้งานไม่ได้
                    w, h = max(w, MIN_WINDOW_W), max(h, MIN_WINDOW_H)
                    pygame.display.set_mode((w, h), pygame.RESIZABLE)
                self.windowed_size = (w, h)
            self._refresh_window()
            return True
        return False

    def translate_event(self, event):
        """แปลงพิกัดเมาส์ในอีเวนต์จากพิกัดหน้าต่างเป็นพิกัดตรรกะ (อีเวนต์อื่นส่งคืนตามเดิม)"""
        pygame = self.pygame
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            data = dict(event.dict)
            x, y = window_to_logical(event.pos, self._viewport)
            data["pos"] = (int(x), int(y))
            if "rel" in data:
                scale = self._viewport[0]
                data["rel"] = (int(data["rel"][0] / scale), int(data["rel"][1] / scale))
            return pygame.event.Event(event.type, data)
        return event

    def present(self):
        """ขยายผืนผ้าใบลงหน้าต่างจริงแล้ว flip"""
        pygame = self.pygame
        self._viewport = compute_viewport(*self.window.get_size(), self.log_w, self.log_h)
        _scale, ox, oy, w, h = self._viewport
        self.window.fill(self.letterbox_color)
        if (w, h) == (self.log_w, self.log_h):
            self.window.blit(self.canvas, (ox, oy))
        else:
            self.window.blit(pygame.transform.smoothscale(self.canvas, (w, h)), (ox, oy))
        pygame.display.flip()
