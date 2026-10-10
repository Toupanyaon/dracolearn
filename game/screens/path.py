"""
screens/path.py
-----------------
หน้าเส้นทางการเรียน: แสดง Unit ต่าง ๆ พร้อมโหนดบทเรียนที่มีสถานะ
Locked (ล็อก) / Available (เรียนได้) / Completed (เรียนจบแล้ว)
เรียนจบบทก่อนหน้า -> ปลดล็อกบทถัดไปโดยอัตโนมัติ
"""

import pygame

from .base import Screen
from .. import config, content, fx
from ..widgets import Button

NODE_RADIUS = 34


class PathScreen(Screen):
    def __init__(self, manager):
        super().__init__(manager)
        self.back_button = Button((30, 20, 140, 44), "< กลับ", sounds=manager.sounds,
                                   on_click=lambda: manager.go_to("dashboard"),
                                   base_color=config.COLOR_BG_LIGHT, hover_color=config.COLOR_ACCENT)
        self.scroll_y = 0
        self.time = 0.0
        self._node_rects = []  # [(rect, unit, lesson, status)]

    def on_enter(self):
        self.scroll_y = 0

    def _compute_layout(self):
        """คำนวณตำแหน่งโหนดทั้งหมด และสถานะ locked/available/completed"""
        self._node_rects = []
        completed = set(self.manager.player_data.get("completed_lessons", []))
        unlocked_next = True  # บทแรกสุดของเกมปลดล็อกเสมอ

        y = 100 - self.scroll_y
        for unit in content.UNITS:
            unit_done = sum(1 for l in unit.lessons if l.id in completed)
            unit_pct = int(unit_done / len(unit.lessons) * 100)

            self._node_rects.append(("unit_header", None, unit, unit_pct, (config.SCREEN_WIDTH // 2, y)))
            y += 60

            for i, lesson in enumerate(unit.lessons):
                status = "completed" if lesson.id in completed else ("available" if unlocked_next else "locked")
                if status != "completed":
                    unlocked_next = False  # หลังเจอบทที่ยังไม่จบบทแรก บทถัด ๆ ไปต้องล็อกหมด

                x = config.SCREEN_WIDTH // 2 + (60 if i % 2 == 0 else -60)
                self._node_rects.append(("lesson", lesson, unit, status, (x, y)))
                y += 90

            y += 20

        self.content_height = y

    def handle_event(self, event):
        self.back_button.handle_event(event)

        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y = max(0, self.scroll_y - event.y * 40)
            self._compute_layout()

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for kind, lesson, unit, status, pos in self._node_rects:
                if kind != "lesson":
                    continue
                rect = pygame.Rect(0, 0, NODE_RADIUS * 2, NODE_RADIUS * 2)
                rect.center = pos
                if rect.collidepoint(event.pos) and status in ("available", "completed"):
                    self.manager.sounds.play_click()
                    self.manager.go_to("lesson", active_unit=unit, active_lesson=lesson)
                    return

    def update(self, dt):
        self.time += dt
        self._compute_layout()

    def draw(self, surface):
        fx.draw_gradient_background(surface)
        fx.draw_ambient_blobs(surface, self.time)
        title_font = config.get_font(28, bold=True)
        title = title_font.render("เส้นทางการเรียนรู้", True, config.COLOR_TEXT)
        surface.blit(title, title.get_rect(center=(config.SCREEN_WIDTH // 2, 30)))

        node_font = config.get_font(15, bold=True)
        header_font = config.get_font(20, bold=True)

        for kind, lesson, unit, status_or_pct, pos in self._node_rects:
            if pos[1] < -60 or pos[1] > config.SCREEN_HEIGHT + 60:
                continue

            if kind == "unit_header":
                text = header_font.render(f"{unit.title} - {unit.subtitle} ({status_or_pct}%)", True,
                                           config.COLOR_TEXT_DARK)
                badge_rect = pygame.Rect(0, 0, text.get_width() + 40, 40)
                badge_rect.center = pos
                # ป้ายสีธีมของแต่ละ Unit ให้เห็นความแตกต่างของแต่ละด่านตั้งแต่หน้าเส้นทางเรียน
                pygame.draw.rect(surface, unit.bg_top, badge_rect, border_radius=20)
                pygame.draw.rect(surface, config.COLOR_WHITE, badge_rect, width=1, border_radius=20)
                surface.blit(text, text.get_rect(center=pos))
                continue

            status = status_or_pct
            if status == "completed":
                color = config.COLOR_SUCCESS
            elif status == "available":
                color = config.COLOR_PRIMARY
            else:
                color = config.COLOR_LOCK

            # เงานุ่ม ๆ ใต้โหนดบทเรียน ให้ดูมีมิติแบบ UI สมัยใหม่
            shadow_surf = pygame.Surface((NODE_RADIUS * 2 + 12, NODE_RADIUS * 2 + 12), pygame.SRCALPHA)
            pygame.draw.circle(shadow_surf, (0, 0, 0, 70), (NODE_RADIUS + 6, NODE_RADIUS + 8), NODE_RADIUS)
            surface.blit(shadow_surf, (pos[0] - NODE_RADIUS - 6, pos[1] - NODE_RADIUS - 6))

            pygame.draw.circle(surface, color, pos, NODE_RADIUS)
            # วงแหวนรอบโหนดใช้สีพาสเทลประจำบทเรียนนั้น (ทุกบทสีไม่ซ้ำกัน) ส่วนบทที่ล็อกอยู่ใช้ขอบขาวเหมือนเดิม
            if status == "locked":
                pygame.draw.circle(surface, config.COLOR_WHITE, pos, NODE_RADIUS, width=2)
            else:
                pygame.draw.circle(surface, content.lesson_background(lesson, 0)[0], pos, NODE_RADIUS, width=5)

            if status == "locked":
                # ไอคอนแม่กุญแจอย่างง่าย
                lx, ly = pos
                pygame.draw.rect(surface, config.COLOR_TEXT_MUTED, (lx - 8, ly - 2, 16, 12), border_radius=2)
                pygame.draw.arc(surface, config.COLOR_TEXT_MUTED, (lx - 6, ly - 12, 12, 14), 3.14, 6.28, 2)
            elif status == "completed":
                pygame.draw.line(surface, config.COLOR_WHITE, (pos[0] - 10, pos[1]), (pos[0] - 2, pos[1] + 8), 3)
                pygame.draw.line(surface, config.COLOR_WHITE, (pos[0] - 2, pos[1] + 8), (pos[0] + 12, pos[1] - 8), 3)
            else:
                play = node_font.render("▶", True, config.COLOR_WHITE)
                surface.blit(play, play.get_rect(center=pos))

            label = node_font.render(lesson.title, True, config.COLOR_TEXT)
            surface.blit(label, label.get_rect(center=(pos[0], pos[1] + NODE_RADIUS + 16)))

        self.back_button.draw(surface)
