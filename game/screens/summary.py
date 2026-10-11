"""
screens/summary.py
---------------------
หน้าสรุปผลหลังเรียนจบบทเรียน: คะแนน, ความถูกต้อง, XP, เวลาที่ใช้,
คำศัพท์ที่ได้เรียน, และแจ้งเตือน Achievement ใหม่ (ถ้ามี)
"""

import pygame

from .. import config, content, mascot, fx
from .base import Screen
from ..widgets import Button


# ---------------------------------------------------------------------------
# เลย์เอาต์แนวตั้ง (จอ 640 px) เรียงบนลงล่างโดยไม่ซ้อนกัน:
#   มาสคอต -> ชื่อบท -> การ์ดสถิติ -> หัวข้อคำศัพท์ -> ปุ่มคำศัพท์ (กี่แถวก็ได้) -> ปุ่มเรียนซ้ำ/Dashboard
# มาสคอตสูงรวม ~2 เท่าของ size (หมวกอยู่เหนือหัว ตัว+หางอยู่ใต้ศูนย์กลาง) จึงใช้ size เล็กลง
# ส่วนปุ่มคำศัพท์จะจัดกึ่งกลางทีละแถว และถ้าคำเยอะจนแถวไม่พอ จะลดขนาดปุ่มก่อนเสมอ
# ---------------------------------------------------------------------------
MASCOT_SIZE = 72
MASCOT_CENTER_Y = 80          # ศูนย์กลางหัว: หมวกสูงสุดอยู่ ~ y=12 ตัว/หางต่ำสุด ~ y=157 (รวมแอนิเมชันลอยตัว)
TITLE_Y = 192
STAT_CARD = pygame.Rect(config.SCREEN_WIDTH // 2 - 320, 224, 640, 88)
HINT_Y = 336
VOCAB_TOP = 356               # แถวปุ่มคำศัพท์แถวแรกเริ่มที่นี่
BUTTON_Y = 562                # ปุ่มเรียนซ้ำ / กลับ Dashboard (สูง 54 -> ล่างสุด 616)
VOCAB_BOTTOM = BUTTON_Y - 12  # ปุ่มคำศัพท์ต้องไม่ล้ำเส้นนี้
VOCAB_MAX_WIDTH = 720
# (ขนาดฟอนต์, ความสูงปุ่ม, ช่องว่างระหว่างแถว) ลองจากใหญ่ไปเล็ก เลือกอันแรกที่ใส่พอดี
VOCAB_SIZES = [(16, 40, 8), (15, 36, 6), (14, 32, 6)]


class SummaryScreen(Screen):
    def __init__(self, manager):
        super().__init__(manager)
        self.time = 0.0
        self.summary = {}
        self.vocab_buttons = []
        self.vocab_hidden = 0

        self.retry_button = Button((config.SCREEN_WIDTH // 2 - 260, BUTTON_Y, 240, 54), "เรียนซ้ำ",
                                    sounds=manager.sounds, on_click=self._retry,
                                    base_color=config.COLOR_BG_LIGHT, hover_color=config.COLOR_ACCENT)
        self.dashboard_button = Button((config.SCREEN_WIDTH // 2 + 20, BUTTON_Y, 240, 54), "กลับ Dashboard",
                                        sounds=manager.sounds, on_click=lambda: manager.go_to("dashboard"))

    @staticmethod
    def _flow_rows(widths, max_width, gap_x):
        """แบ่งปุ่ม (ตามความกว้างที่ให้มา) เป็นแถว ๆ ไม่ให้แถวไหนกว้างเกิน max_width คืนลิสต์ของลิสต์ดัชนี"""
        rows, current, used = [], [], 0
        for i, w in enumerate(widths):
            need = w if not current else w + gap_x
            if current and used + need > max_width:
                rows.append(current)
                current, used = [], 0
                need = w
            current.append(i)
            used += need
        if current:
            rows.append(current)
        return rows

    def _build_vocab_buttons(self, words):
        """สร้างปุ่มคำศัพท์ให้พอดีพื้นที่ VOCAB_TOP..VOCAB_BOTTOM
        ลองขนาดใหญ่ -> เล็ก ถ้าเล็กสุดแล้วยังไม่พอ จะตัดคำท้าย ๆ ออก (self.vocab_hidden = จำนวนที่ซ่อน)"""
        self.vocab_buttons, self.vocab_hidden = [], 0
        if not words:
            return
        gap_x = 10
        area_h = VOCAB_BOTTOM - VOCAB_TOP
        shown = list(words)
        while shown:
            for font_size, btn_h, gap_y in VOCAB_SIZES:
                font = config.get_font(font_size, bold=True)
                # เว้นที่ด้านหน้าไว้สำหรับวาดไอคอนลำโพงทับ (แทน emoji ที่บางฟอนต์แสดงเป็นกล่องว่าง)
                labels = [f"   {w}" for w in shown]
                widths = [font.size(lb)[0] + 28 for lb in labels]
                rows = self._flow_rows(widths, VOCAB_MAX_WIDTH, gap_x)
                total_h = len(rows) * btn_h + (len(rows) - 1) * gap_y
                if total_h <= area_h:
                    y = VOCAB_TOP
                    for row in rows:
                        row_w = sum(widths[i] for i in row) + gap_x * (len(row) - 1)
                        x = config.SCREEN_WIDTH // 2 - row_w // 2   # จัดกึ่งกลางทีละแถว
                        for i in row:
                            word = shown[i]
                            self.vocab_buttons.append(Button(
                                (x, y, widths[i], btn_h), labels[i], font=font, sounds=self.manager.sounds,
                                on_click=lambda w=word: self.manager.sounds.speak(w, lang=content.LEARN_LANG),
                                base_color=config.COLOR_BG_LIGHT, hover_color=config.COLOR_ACCENT))
                            x += widths[i] + gap_x
                        y += btn_h + gap_y
                    self.vocab_hidden = len(words) - len(shown)
                    return
            shown.pop()   # เล็กสุดแล้วยังล้น (คำศัพท์เยอะผิดปกติ) -> ตัดคำสุดท้ายออกแล้วลองใหม่

    def on_enter(self):
        self.time = 0.0
        self.summary = self.manager.context.get("lesson_summary", {})
        self.replay_unit = self.manager.context.get("replay_unit")
        self.replay_lesson = self.manager.context.get("replay_lesson")

        # สร้างปุ่ม "คำศัพท์ + ลำโพง" ให้กดฟังเสียงแต่ละคำที่เพิ่งเรียนได้ทีละคำ
        self._build_vocab_buttons(sorted(set(self.summary.get("vocab_learned", []))))

        self.confetti = fx.ParticleSystem()
        newly = self.summary.get("newly_unlocked", [])
        if self.summary.get("correct", 0) > 0:
            self.confetti.spawn_confetti((config.SCREEN_WIDTH // 2, 150), count=40)
        if newly:
            first = content.ACHIEVEMENT_MAP.get(newly[0])
            if first:
                self.manager.toast.show(f"ปลดล็อกความสำเร็จ: {first.title}!", duration=3.0)
            self.manager.sounds.play_achievement()

    def _retry(self):
        self.manager.go_to("lesson", active_unit=self.replay_unit, active_lesson=self.replay_lesson)

    def update(self, dt):
        self.time += dt
        self.confetti.update(dt)

    def handle_event(self, event):
        self.retry_button.handle_event(event)
        self.dashboard_button.handle_event(event)
        for btn in self.vocab_buttons:
            btn.handle_event(event)

    def draw(self, surface):
        # ใช้สีพาสเทลของบทที่เพิ่งเรียนจบ (ตรงกับสีตอนทำข้อสอบ)
        if getattr(self, "replay_lesson", None) is not None:
            theme_top, theme_bottom = content.lesson_background(self.replay_lesson, 0)
        else:
            theme_top, theme_bottom = config.COLOR_BG_TOP, config.COLOR_BG_BOTTOM
        fx.draw_gradient_background(surface, theme_top, theme_bottom)
        fx.draw_ambient_blobs(surface, self.time, tint=theme_top)
        s = self.summary

        fx.draw_card(surface, STAT_CARD)
        correct = s.get("correct", 0)
        wrong = s.get("wrong", 0)
        total = max(1, correct + wrong)
        accuracy = int(correct / total * 100)

        mood = "excited" if accuracy >= 70 else "sad"
        mascot.draw_mascot(surface, (config.SCREEN_WIDTH // 2, MASCOT_CENTER_Y), size=MASCOT_SIZE,
                           mood=mood, t=self.time)

        title_font = config.get_font(30, bold=True)
        title = title_font.render(f'เรียนจบบท "{s.get("lesson_title", "")}"!', True, config.COLOR_TEXT_DARK)
        surface.blit(title, title.get_rect(center=(config.SCREEN_WIDTH // 2, TITLE_Y)))

        stat_font = config.get_font(20)
        # สถิติ 4 ค่าจัดเป็นตาราง 2 x 2 ในการ์ดเดียว (ประหยัดที่แนวตั้งให้ปุ่มคำศัพท์)
        lines = [
            f"ตอบถูก {correct} ข้อ / ตอบผิด {wrong} ข้อ",
            f"ความแม่นยำ: {accuracy}%",
            f"XP ที่ได้รับ: +{s.get('xp_earned', 0)} XP",
            f"เวลาที่ใช้: {s.get('elapsed_seconds', 0)} วินาที",
        ]
        col_x = (STAT_CARD.x + STAT_CARD.width // 4, STAT_CARD.x + STAT_CARD.width * 3 // 4)
        row_y = (STAT_CARD.y + 28, STAT_CARD.y + 62)
        for i, line in enumerate(lines):
            surf = stat_font.render(line, True, config.COLOR_TEXT_MUTED)
            surface.blit(surf, surf.get_rect(center=(col_x[i % 2], row_y[i // 2])))

        if self.vocab_buttons:
            hint_font = config.get_font(16, bold=True)
            text = "คำศัพท์ที่ได้เรียน (กดฟังเสียงได้เลย):"
            if self.vocab_hidden:
                text = f"คำศัพท์ที่ได้เรียน (แสดง {len(self.vocab_buttons)} จาก {len(self.vocab_buttons) + self.vocab_hidden} คำ):"
            hint = hint_font.render(text, True, config.COLOR_TEXT_DARK)
            surface.blit(hint, hint.get_rect(center=(config.SCREEN_WIDTH // 2, HINT_Y)))
            for btn in self.vocab_buttons:
                btn.draw(surface)
                mascot.draw_achievement_icon(surface, (btn.rect.x + 16, btn.rect.centery), 14, "speaker")

        self.retry_button.draw(surface)
        self.dashboard_button.draw(surface)

        self.confetti.draw(surface)  # วาดคอนเฟตตี้ทับบนสุด ให้เห็นชัดตอนฉลอง
