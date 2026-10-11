"""
screens/stats.py
----------------
หน้าสถิติการเรียน (วาดกราฟด้วย pygame ล้วน ๆ ไม่พึ่งไลบรารีกราฟ):
  1) กราฟแท่ง XP 7 วันล่าสุด
  2) ความแม่นยำแยกตาม Unit (แถบแนวนอน + สีตามระดับ)
  3) หัวข้อที่ตอบผิดบ่อย (Top 5)
"""

import pygame

from .base import Screen
from .. import config, fx, stats, i18n
from ..widgets import Button

XP_CARD = pygame.Rect(30, 96, 424, 262)
ACC_CARD = pygame.Rect(466, 96, 404, 262)
TOPIC_CARD = pygame.Rect(30, 370, 840, 250)
LEVEL_COLORS = {"good": config.COLOR_SUCCESS, "ok": config.COLOR_SECONDARY,
                "bad": config.COLOR_DANGER, "none": config.COLOR_LOCK}
ANIM_SECONDS = 0.7


def _fit(font, text: str, max_w: int) -> str:
    """ตัดข้อความให้พอดีความกว้าง (เติม …)"""
    if font.size(text)[0] <= max_w:
        return text
    while text and font.size(text + "…")[0] > max_w:
        text = text[:-1]
    return text + "…"


class StatsScreen(Screen):
    def __init__(self, manager):
        super().__init__(manager)
        self.time = 0.0
        self.anim = 0.0
        self.series = []
        self.summary = {}
        self.accuracy = []
        self.overall = None
        self.topics = []
        self.back_button = Button((30, 20, 140, 44), "< กลับ", sounds=manager.sounds,
                                   on_click=lambda: manager.go_to("dashboard"),
                                   base_color=config.COLOR_BG_LIGHT, hover_color=config.COLOR_ACCENT)

    def on_enter(self):
        self.time = 0.0
        self.anim = 0.0
        self.refresh()

    def refresh(self):
        data = self.manager.player_data
        self.series = stats.xp_last_days(data, 7)
        self.summary = stats.xp_summary(data, 7)
        self.accuracy = stats.unit_accuracy(data)
        self.overall = stats.overall_accuracy(data)
        self.topics = stats.wrong_topics(data, 5)

    def handle_event(self, event):
        self.back_button.handle_event(event)

    def update(self, dt):
        self.time += dt
        self.anim = min(1.0, self.anim + dt / ANIM_SECONDS)

    @property
    def _ease(self) -> float:
        t = self.anim
        return 1 - (1 - t) ** 3

    # ------------------------------------------------------------------
    def draw(self, surface):
        fx.draw_gradient_background(surface)
        fx.draw_ambient_blobs(surface, self.time)
        title = config.get_font(28, bold=True).render("สถิติการเรียน", True, config.COLOR_TEXT)
        surface.blit(title, title.get_rect(center=(config.SCREEN_WIDTH // 2, 42)))
        for card in (XP_CARD, ACC_CARD, TOPIC_CARD):
            fx.draw_card(surface, card)
        self._draw_xp_chart(surface)
        self._draw_accuracy(surface)
        self._draw_topics(surface)
        self.back_button.draw(surface)

    def _draw_xp_chart(self, surface):
        c = XP_CARD
        head = config.get_font(18, bold=True)
        small = config.get_font(14)
        surface.blit(head.render("XP 7 วันล่าสุด", True, config.COLOR_TEXT), (c.x + 18, c.y + 12))
        s = self.summary
        info = f"รวม {s.get('total', 0)} · เฉลี่ย {s.get('average', 0)}/วัน"
        surface.blit(small.render(info, True, config.COLOR_TEXT_MUTED), (c.x + 18, c.y + 40))

        plot = pygame.Rect(c.x + 52, c.y + 74, c.width - 76, c.height - 74 - 40)
        peak = max([d.xp for d in self.series] + [0])
        top = stats.nice_axis_max(peak)
        # เส้นกริด + ตัวเลขแกน Y (0, ครึ่ง, สูงสุด)
        for frac in (0.0, 0.5, 1.0):
            y = plot.bottom - int(plot.height * frac)
            pygame.draw.line(surface, config.COLOR_BG_LIGHT, (plot.x, y), (plot.right, y), 1)
            lab = small.render(str(int(top * frac)), True, config.COLOR_TEXT_MUTED)
            surface.blit(lab, lab.get_rect(midright=(plot.x - 8, y)))
        n = len(self.series)
        slot = plot.width / max(1, n)
        bar_w = int(slot * 0.56)
        for i, d in enumerate(self.series):
            cx = plot.x + int(slot * (i + 0.5))
            full = plot.height * d.xp / top if top else 0
            h = int(full * self._ease)
            color = config.COLOR_PRIMARY if d.is_today else config.COLOR_ACCENT
            if d.xp == 0:
                pygame.draw.rect(surface, config.COLOR_LOCK, (cx - bar_w // 2, plot.bottom - 3, bar_w, 3),
                                 border_radius=2)
            elif h > 0:
                pygame.draw.rect(surface, color, (cx - bar_w // 2, plot.bottom - h, bar_w, h),
                                 border_top_left_radius=6, border_top_right_radius=6)
                if self.anim >= 1.0:
                    v = small.render(str(d.xp), True, config.COLOR_TEXT)
                    surface.blit(v, v.get_rect(midbottom=(cx, plot.bottom - h - 2)))
            lab = small.render(i18n.pick("วันนี้", "Today") if d.is_today else (d.label if i18n.ui_lang() == "th" else stats.WEEKDAYS_EN[d.day.weekday()]), True,
                               config.COLOR_SECONDARY if d.is_today else config.COLOR_TEXT_MUTED)
            surface.blit(lab, lab.get_rect(midtop=(cx, plot.bottom + 8)))
        if peak == 0:
            msg = small.render("ยังไม่มี XP ใน 7 วันนี้ ไปเรียนกันเถอะ!", True, config.COLOR_TEXT_MUTED)
            surface.blit(msg, msg.get_rect(center=plot.center))

    def _draw_accuracy(self, surface):
        c = ACC_CARD
        head = config.get_font(18, bold=True)
        small = config.get_font(14)
        row_font = config.get_font(16)
        surface.blit(head.render("ความแม่นยำแต่ละ Unit", True, config.COLOR_TEXT), (c.x + 18, c.y + 12))
        ov = "ยังไม่มีข้อมูล" if self.overall is None else f"รวมทุกโหมด {self.overall}%"
        surface.blit(small.render(ov, True, config.COLOR_TEXT_MUTED), (c.x + 18, c.y + 40))
        y = c.y + 70
        label_w, bar_x = 134, c.x + 160
        bar_w = c.width - 160 - 66
        for r in self.accuracy:
            name = _fit(row_font, r.title, label_w)
            surface.blit(row_font.render(name, True, config.COLOR_TEXT), (c.x + 18, y))
            track = pygame.Rect(bar_x, y + 3, bar_w, 16)
            pygame.draw.rect(surface, config.COLOR_BG_LIGHT, track, border_radius=8)
            pct = r.percent
            if pct is not None and pct > 0:
                w = max(8, int(bar_w * pct / 100 * self._ease))
                pygame.draw.rect(surface, LEVEL_COLORS[stats.accuracy_level(pct)],
                                 (track.x, track.y, w, track.height), border_radius=8)
            txt = "—" if pct is None else f"{pct}%"
            t = row_font.render(txt, True, config.COLOR_TEXT_MUTED if pct is None else config.COLOR_TEXT)
            surface.blit(t, t.get_rect(midright=(c.right - 16, y + 11)))
            y += 30

    def _draw_topics(self, surface):
        c = TOPIC_CARD
        head = config.get_font(18, bold=True)
        small = config.get_font(14)
        row_font = config.get_font(17)
        surface.blit(head.render("หัวข้อที่ผิดบ่อย", True, config.COLOR_TEXT), (c.x + 18, c.y + 12))
        if not self.topics:
            msg = row_font.render("ยังไม่มีข้อที่ตอบผิด — เยี่ยมมาก! ทำต่อไปเลย", True, config.COLOR_TEXT_MUTED)
            surface.blit(msg, msg.get_rect(center=c.center))
            return
        top_wrong = max(t.wrong for t in self.topics)
        y = c.y + 50
        for rank, t in enumerate(self.topics, start=1):
            surface.blit(row_font.render(f"#{rank}", True, config.COLOR_SECONDARY), (c.x + 18, y))
            surface.blit(row_font.render(_fit(row_font, t.title, 250), True, config.COLOR_TEXT), (c.x + 58, y))
            surface.blit(small.render(_fit(small, t.where, 210), True, config.COLOR_TEXT_MUTED), (c.x + 320, y + 3))
            track = pygame.Rect(c.x + 545, y + 4, 170, 14)
            pygame.draw.rect(surface, config.COLOR_BG_LIGHT, track, border_radius=7)
            w = max(8, int(track.width * t.wrong / top_wrong * self._ease))
            pygame.draw.rect(surface, config.COLOR_DANGER, (track.x, track.y, w, track.height), border_radius=7)
            cnt = small.render(f"ผิด {t.wrong}/{t.total}", True, config.COLOR_TEXT)
            surface.blit(cnt, cnt.get_rect(midright=(c.right - 16, y + 11)))
            y += 38
