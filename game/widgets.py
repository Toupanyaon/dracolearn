"""
widgets.py
----------
คอมโพเนนต์ UI ที่นำกลับมาใช้ซ้ำได้ทั่วทั้งเกม:
Button, ProgressBar, HeartMeter, TextInputBox, Toast, Slider
"""

import pygame

from . import config, fx


class Button:
    """ปุ่มสไตล์ทันสมัย: hover แล้ว "ขยายตัว" นุ่ม ๆ แบบสปริง (scale animation) พร้อมเงาลอยใต้ปุ่ม
    (อ้างอิงสไตล์ปุ่มจาก basic1.py) มี disabled state และเสียงประกอบผ่าน SoundManager"""

    def __init__(self, rect, text, font=None, sounds=None, on_click=None,
                 base_color=None, hover_color=None, text_color=None, disabled=False):
        self.rect = pygame.Rect(rect)  # ตำแหน่ง/ขนาดจริงที่ใช้เช็คการคลิก (ไม่ขยับตาม scale)
        self.text = text
        self.font = font or config.get_font(24, bold=True)
        self.sounds = sounds
        self.on_click = on_click
        self.base_color = base_color or config.COLOR_PRIMARY
        self.hover_color = hover_color or config.COLOR_PRIMARY_DARK
        self.text_color = text_color or config.COLOR_WHITE
        self.disabled = disabled

        self.hovering = False
        self._was_hovering = False
        self._pressed = False
        self.scale = 1.0  # 1.0 = ขนาดปกติ, ค่อย ๆ ไล่ไปทาง ~1.06 ตอน hover

    def set_disabled(self, value: bool):
        self.disabled = value

    def handle_event(self, event) -> bool:
        """คืนค่า True ถ้าปุ่มถูกคลิกสำเร็จในเฟรมนี้"""
        if self.disabled:
            self.hovering = False
            return False

        clicked = False
        if event.type == pygame.MOUSEMOTION:
            self.hovering = self.rect.collidepoint(event.pos)
            if self.hovering and not self._was_hovering and self.sounds:
                self.sounds.play_hover()
            self._was_hovering = self.hovering
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._pressed and self.rect.collidepoint(event.pos):
                clicked = True
                if self.sounds:
                    self.sounds.play_click()
                if self.on_click:
                    self.on_click()
            self._pressed = False
        return clicked

    def draw(self, surface):
        # แอนิเมชัน hover แบบขยายตัวนุ่ม ๆ (ease towards target ทุกเฟรมที่ draw ถูกเรียก)
        target_scale = 1.06 if (self.hovering and not self.disabled) else 1.0
        self.scale = config.lerp(self.scale, target_scale, 0.25)

        w = int(self.rect.width * self.scale)
        h = int(self.rect.height * self.scale)
        draw_rect = pygame.Rect(0, 0, w, h)
        draw_rect.center = self.rect.center

        if self.disabled:
            color = config.COLOR_LOCK
            text_color = config.COLOR_TEXT_MUTED
        else:
            fx.draw_soft_shadow(surface, draw_rect, radius=16, offset=6, alpha=90)
            hover_amt = min(1.0, max(0.0, (self.scale - 1.0) / 0.06))
            color = config.lerp_color(self.base_color, self.hover_color, hover_amt)
            if self._pressed and self.hovering:
                color = config.lerp_color(color, config.COLOR_BLACK, 0.18)
            text_color = self.text_color

        pygame.draw.rect(surface, color, draw_rect, border_radius=16)
        if not self.disabled:
            pygame.draw.rect(surface, config.COLOR_WHITE, draw_rect, width=2, border_radius=16)

        text_surf = self.font.render(self.text, True, text_color)
        max_w = max(1, draw_rect.width - 14)
        if text_surf.get_width() > max_w:     # ข้อความยาวกว่าปุ่ม (เช่น เมนูอังกฤษยาวกว่าไทย): ย่อให้พอดี ไม่ล้นกรอบ
            ratio = max_w / text_surf.get_width()
            new_size = (max_w, max(1, int(text_surf.get_height() * ratio)))
            try:
                text_surf = pygame.transform.smoothscale(text_surf, new_size)
            except (ValueError, pygame.error):
                text_surf = pygame.transform.scale(text_surf, new_size)
        surface.blit(text_surf, text_surf.get_rect(center=draw_rect.center))


class ProgressBar:
    """แถบความคืบหน้าแนวนอน ใช้ได้ทั้ง XP, ความคืบหน้าข้อสอบ, % ของ Unit"""

    def __init__(self, rect, fg_color=None, bg_color=None, border_radius=10):
        self.rect = pygame.Rect(rect)
        self.fg_color = fg_color or config.COLOR_PRIMARY
        self.bg_color = bg_color or config.COLOR_BG_LIGHT
        self.border_radius = border_radius
        self._animated_ratio = 0.0  # ไล่ค่าเข้าหาเป้าหมายทีละนิดทุกเฟรม ให้แถบวิ่งลื่น ๆ แทนกระตุก

    def draw(self, surface, ratio: float, label: str = ""):
        target = max(0.0, min(1.0, ratio))
        self._animated_ratio += (target - self._animated_ratio) * 0.15
        display_ratio = self._animated_ratio

        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=self.border_radius)
        fill_w = int(self.rect.width * display_ratio)
        if fill_w > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.height)
            pygame.draw.rect(surface, self.fg_color, fill_rect, border_radius=self.border_radius)
            # ไฮไลต์มันวาวบาง ๆ ด้านบนของแถบ ให้ดูมีมิติแบบ UI สมัยใหม่
            sheen_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, max(2, self.rect.height // 3))
            sheen = pygame.Surface((sheen_rect.width, sheen_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(sheen, (255, 255, 255, 45), (0, 0, sheen_rect.width, sheen_rect.height),
                              border_radius=self.border_radius)
            surface.blit(sheen, (sheen_rect.x, sheen_rect.y))
        pygame.draw.rect(surface, config.COLOR_WHITE, self.rect, width=1, border_radius=self.border_radius)
        if label:
            font = config.get_font(16, bold=True)
            text_surf = font.render(label, True, config.COLOR_TEXT)
            surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))


class HeartMeter:
    """แสดงจำนวนหัวใจที่เหลือ เป็นรูปหัวใจวาดด้วยเวกเตอร์ (ไม่ใช้ภาพภายนอก)"""

    def __init__(self, pos, max_hearts=config.MAX_HEARTS, size=22, gap=6):
        self.pos = pos
        self.max_hearts = max_hearts
        self.size = size
        self.gap = gap

    def draw(self, surface, current_hearts: int):
        x, y = self.pos
        for i in range(self.max_hearts):
            hx = x + i * (self.size + self.gap)
            filled = i < current_hearts
            color = config.COLOR_DANGER if filled else config.COLOR_LOCK
            r = self.size * 0.28
            pygame.draw.circle(surface, color, (int(hx + r), int(y + r)), int(r))
            pygame.draw.circle(surface, color, (int(hx + self.size - r), int(y + r)), int(r))
            pygame.draw.polygon(surface, color, [
                (hx, y + r * 0.9),
                (hx + self.size / 2, y + self.size),
                (hx + self.size, y + r * 0.9),
            ])


class TextInputBox:
    """กล่องพิมพ์ข้อความ ใช้ได้ทั้งโจทย์ประเภท translate_type และช่องกรอกทั่วไป (ชื่อ/รหัสผ่าน)
    is_password=True จะแสดงตัวอักษรที่พิมพ์เป็น • แทนของจริง (แต่ self.text ยังเก็บค่าจริงไว้ใช้งาน)
    รองรับหลายกล่องในหน้าเดียวกัน: คลิกกล่องไหนกล่องนั้น active (รับคีย์บอร์ด) กล่องอื่นจะ inactive"""

    def __init__(self, rect, font=None, placeholder="", is_password=False):
        self.rect = pygame.Rect(rect)
        self.font = font or config.get_font(22)
        self.text = ""
        self.placeholder = placeholder
        self.is_password = is_password
        self.active = True
        self._cursor_timer = 0.0
        self._cursor_visible = True

    def clear(self):
        self.text = ""

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # คลิกโดนกล่องนี้ -> active, คลิกที่อื่น -> inactive (ให้กล่องที่ถูกคลิกจริงรับคีย์บอร์ดแทน)
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_TAB):
                pass  # Enter ใช้ submit ที่ปุ่มของแต่ละหน้า, Tab ใช้สลับโฟกัสที่ระดับหน้าจอ
            elif event.unicode and event.unicode.isprintable() and len(self.text) < 60:
                self.text += event.unicode

    def update(self, dt):
        self._cursor_timer += dt
        if self._cursor_timer >= 0.5:
            self._cursor_timer = 0.0
            self._cursor_visible = not self._cursor_visible

    def _display_text(self) -> str:
        return "•" * len(self.text) if self.is_password else self.text

    def draw(self, surface):
        pygame.draw.rect(surface, config.COLOR_BG_LIGHT, self.rect, border_radius=10)
        border_color = config.COLOR_PRIMARY if self.active else config.COLOR_TEXT_MUTED
        pygame.draw.rect(surface, border_color, self.rect, width=2, border_radius=10)

        shown = self._display_text()
        if self.text:
            text_surf = self.font.render(shown, True, config.COLOR_TEXT)
        else:
            text_surf = self.font.render(self.placeholder, True, config.COLOR_TEXT_MUTED)
        surface.blit(text_surf, (self.rect.x + 12, self.rect.centery - text_surf.get_height() // 2))

        if self.active and self._cursor_visible:
            cursor_x = self.rect.x + 12 + self.font.size(shown)[0] + 2
            pygame.draw.line(surface, config.COLOR_TEXT, (cursor_x, self.rect.y + 8),
                              (cursor_x, self.rect.bottom - 8), 2)


class Toast:
    """ข้อความแจ้งเตือนลอยชั่วคราว (เช่น ปลดล็อก Achievement, Streak เพิ่ม)"""

    def __init__(self):
        self.message = ""
        self.timer = 0.0
        self.duration = 2.5

    def show(self, message: str, duration: float = 2.5):
        self.message = message
        self.timer = duration
        self.duration = duration

    @staticmethod
    def _wrap_message(message: str, font: pygame.font.Font, max_width: int) -> list:
        from .i18n import tr
        message = tr(message)
        lines = []
        for paragraph in message.splitlines() or [""]:
            line = ""
            for word in paragraph.split():
                candidate = f"{line} {word}".strip()
                if font.size(candidate)[0] <= max_width:
                    line = candidate
                    continue
                if line:
                    lines.append(line)
                    line = ""
                for character in word:
                    candidate = line + character
                    if line and font.size(candidate)[0] > max_width:
                        lines.append(line)
                        line = character
                    else:
                        line = candidate
            lines.append(line)
        return lines

    def update(self, dt):
        if self.timer > 0:
            self.timer -= dt

    @property
    def visible(self):
        return self.timer > 0

    def draw(self, surface):
        if not self.visible:
            return
        alpha_ratio = min(1.0, self.timer / 0.4) if self.timer < 0.4 else 1.0
        font = config.get_font(20, bold=True)
        padding = 16
        max_text_width = config.SCREEN_WIDTH - 40 - padding * 2
        lines = self._wrap_message(self.message, font, max_text_width)
        line_height = font.get_linesize()
        box_w = max(font.size(line)[0] for line in lines) + padding * 2
        box_h = len(lines) * line_height + padding
        box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(box, (*config.COLOR_ACCENT, int(230 * alpha_ratio)), (0, 0, box_w, box_h), border_radius=14)
        for index, line in enumerate(lines):
            text_surf = font.render(line, True, config.COLOR_WHITE)
            box.blit(text_surf, (padding, padding // 2 + index * line_height))
        rect = box.get_rect(midtop=(config.SCREEN_WIDTH // 2, 20))
        surface.blit(box, rect)


class Slider:
    """สไลเดอร์แนวนอน (ลากด้วยเมาส์หรือคลิกบนแถบได้) ค่า 0.0 - 1.0
    on_change(value) ถูกเรียกทุกครั้งที่ค่าเปลี่ยนระหว่างลาก, on_release(value) เรียกตอนปล่อยเมาส์"""

    def __init__(self, rect, value=1.0, on_change=None, on_release=None,
                 fill_color=None, sounds=None):
        self.rect = pygame.Rect(rect)          # พื้นที่แถบ (ความสูงน้อย ๆ) - พื้นที่คลิกจริงจะสูงกว่านี้เล็กน้อย
        self.value = max(0.0, min(1.0, value))
        self.on_change = on_change
        self.on_release = on_release
        self.fill_color = fill_color or config.COLOR_SECONDARY
        self.dragging = False
        self.hovering = False

    def _hit_rect(self):
        return self.rect.inflate(24, 26)

    def _value_from_x(self, x):
        return max(0.0, min(1.0, (x - self.rect.x) / max(1, self.rect.width)))

    def _set_from_x(self, x):
        new_value = round(self._value_from_x(x), 2)
        if new_value != self.value:
            self.value = new_value
            if self.on_change:
                self.on_change(self.value)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovering = self._hit_rect().collidepoint(event.pos)
            if self.dragging:
                self._set_from_x(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._hit_rect().collidepoint(event.pos):
                self.dragging = True
                self._set_from_x(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                if self.on_release:
                    self.on_release(self.value)

    def draw(self, surface):
        r = self.rect
        pygame.draw.rect(surface, config.COLOR_BG_LIGHT, r, border_radius=r.height // 2)
        fill_w = int(r.width * self.value)
        if fill_w > 0:
            pygame.draw.rect(surface, self.fill_color, (r.x, r.y, fill_w, r.height), border_radius=r.height // 2)
        pygame.draw.rect(surface, config.COLOR_WHITE, r, width=1, border_radius=r.height // 2)
        knob_r = 12 if (self.hovering or self.dragging) else 10
        pygame.draw.circle(surface, config.COLOR_WHITE, (r.x + fill_w, r.centery), knob_r)
        pygame.draw.circle(surface, self.fill_color, (r.x + fill_w, r.centery), knob_r - 4)
