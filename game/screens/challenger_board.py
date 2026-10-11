"""
screens/challenger_board.py
----------------------------
ตารางคะแนนเฉพาะโหมด Challenger (แยกจากตาราง XP ที่หน้า Dashboard)

จัดอันดับผู้เล่นทุกคนบนเครื่องนี้ด้วย "จำนวนข้อที่ตอบถูกมากที่สุดในหนึ่งรอบ" (survival_best)
ถ้าเท่ากันดูระดับความยากที่ไปถึง (survival_best_level) แล้วค่อยเรียงตามชื่อ
คนที่ยังไม่เคยเล่นโหมดนี้จะไม่อยู่ในตาราง
"""

import pygame

from .base import Screen
from .. import config, content, mascot, fx, storage
from ..widgets import Button

TOP_N = 10
MEDAL_COLORS = {1: (255, 215, 0), 2: (200, 200, 210), 3: (205, 140, 90)}


class ChallengerBoardScreen(Screen):
    def __init__(self, manager):
        super().__init__(manager)
        self.time = 0.0
        self.rows = []
        self.my_rank = None
        self.back_button = Button((30, 20, 140, 44), "< กลับ", sounds=manager.sounds,
                                   on_click=lambda: manager.go_to("dashboard"),
                                   base_color=config.COLOR_BG_LIGHT, hover_color=config.COLOR_ACCENT)
        self.play_button = Button((config.SCREEN_WIDTH // 2 - 130, 566, 260, 54), "เล่น Challenger",
                                   sounds=manager.sounds, on_click=lambda: manager.go_to("survival"),
                                   base_color=config.COLOR_ACCENT, hover_color=(150, 120, 255))

    def on_enter(self):
        self.time = 0.0
        self.rows = storage.survival_leaderboard(self.manager.root, limit=TOP_N, course=content.COURSE)
        self.my_rank = storage.survival_rank(self.manager.root, self.manager.current_profile_key, course=content.COURSE)

    def handle_event(self, event):
        self.back_button.handle_event(event)
        self.play_button.handle_event(event)

    def update(self, dt):
        self.time += dt

    def draw(self, surface):
        fx.draw_gradient_background(surface)
        fx.draw_ambient_blobs(surface, self.time)
        center_x = config.SCREEN_WIDTH // 2

        title_font = config.get_font(28, bold=True)
        title = title_font.render("ตารางคะแนน Challenger", True, config.COLOR_TEXT)
        surface.blit(title, title.get_rect(center=(center_x, 40)))

        board = pygame.Rect(center_x - 330, 84, 660, 468)
        fx.draw_card(surface, board)
        mascot.draw_achievement_icon(surface, (board.x + 36, board.y + 30), 26, "trophy")

        head_font = config.get_font(16, bold=True)
        sub = head_font.render("เรียงตามจำนวนข้อที่ตอบถูกมากที่สุดในหนึ่งรอบ", True, config.COLOR_TEXT_MUTED)
        surface.blit(sub, (board.x + 62, board.y + 20))

        row_font = config.get_font(19)
        row_bold = config.get_font(19, bold=True)
        my_key = self.manager.current_profile_key
        y = board.y + 64
        row_h = 38
        for rank, (key, name, best, level) in enumerate(self.rows, start=1):
            is_me = key == my_key
            if is_me:
                pygame.draw.rect(surface, config.COLOR_ACCENT, (board.x + 14, y - 5, board.width - 28, row_h - 2),
                                  border_radius=9)
            color = config.COLOR_WHITE if is_me else config.COLOR_TEXT
            rank_surf = (row_bold if rank <= 3 else row_font).render(
                f"#{rank}", True, MEDAL_COLORS.get(rank, config.COLOR_TEXT_MUTED))
            surface.blit(rank_surf, (board.x + 26, y))

            name_text = name if len(name) <= 18 else name[:17] + "…"
            surface.blit(row_font.render(name_text, True, color), (board.x + 84, y))

            lvl = row_font.render(f"ระดับ {level}/{content.DIFFICULTY_LEVELS}", True, config.COLOR_TEXT_MUTED
                                  if not is_me else config.COLOR_WHITE)
            surface.blit(lvl, lvl.get_rect(topright=(board.right - 170, y)))
            score = row_bold.render(f"{best} ข้อ", True, config.COLOR_SECONDARY)
            surface.blit(score, score.get_rect(topright=(board.right - 28, y)))
            y += row_h

        if not self.rows:
            empty_font = config.get_font(18)
            empty = empty_font.render("ยังไม่มีใครทำสถิติ มาเป็นคนแรกกันเลย!", True, config.COLOR_TEXT_MUTED)
            surface.blit(empty, empty.get_rect(center=(center_x, board.centery)))
        elif self.my_rank is None:
            note_font = config.get_font(16)
            note = note_font.render("คุณยังไม่มีสถิติในโหมดนี้ ลองเล่นดูสิ!", True, config.COLOR_TEXT_MUTED)
            surface.blit(note, note.get_rect(center=(center_x, board.bottom - 22)))
        elif self.my_rank[0] > TOP_N:
            note_font = config.get_font(16, bold=True)
            best = storage.survival_stat(self.manager.player_data)[0]
            note = note_font.render(f"คุณอยู่อันดับที่ {self.my_rank[0]} จาก {self.my_rank[1]} คน ({best} ข้อ)",
                                     True, config.COLOR_SECONDARY)
            surface.blit(note, note.get_rect(center=(center_x, board.bottom - 22)))

        self.back_button.draw(surface)
        self.play_button.draw(surface)
