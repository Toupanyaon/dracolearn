"""
screens/dashboard.py
----------------------
หน้าหลักหลังล็อกอิน: สรุปสถานะผู้เล่น, ภารกิจประจำวัน, ปุ่มไปต่อบทเรียน,
และ "ตารางคะแนนของจริง" ที่ดึงมาจากผู้เล่นทุกคนที่เคยเล่นเกมนี้บนเครื่องเดียวกัน
(คนละชื่อ = คนละคน คนละคะแนน ไม่ใช่ข้อมูลจำลองอีกต่อไป)
"""

import pygame

from .base import Screen
from .. import config, mascot, content, storage, fx, wardrobe
from ..widgets import Button, ProgressBar, HeartMeter


class DashboardScreen(Screen):
    def __init__(self, manager):
        super().__init__(manager)
        self.time = 0.0

        # ปุ่มล่างซ้าย: จัดให้ขอบซ้าย-ขวาตรงกับการ์ดฝั่งซ้าย (x 24 -> 404) และเว้นระยะห่างจากบอร์ดคะแนน (เริ่มที่ x=470)
        # เหลือช่องว่าง 66px ไม่ติดกัน ปุ่มสองปุ่มห่างกัน 16px
        action_font = config.get_font(22, bold=True)
        self.path_button = Button((24, 500, 170, 52), "ไปเส้นทางเรียน", font=action_font, sounds=manager.sounds,
                                   on_click=lambda: manager.go_to("path"))
        self.continue_button = Button((210, 500, 194, 52), "เรียนต่อบทถัดไป", font=action_font, sounds=manager.sounds,
                                       on_click=self._continue_lesson)
        # ปุ่มโหมด Challenger + ปุ่มตารางคะแนนของโหมดนี้: อยู่ใต้การ์ดภารกิจ เหนือแถวปุ่มเรียน
        # (ข้อความบนปุ่มอัปเดตสถิติสูงสุดตอนวาด) รวมกว้าง 24 -> 404 ตรงกับการ์ดฝั่งซ้าย
        self.survival_button = Button((24, 436, 262, 52), "โหมด Challenger", font=config.get_font(19, bold=True),
                                       sounds=manager.sounds, on_click=lambda: manager.go_to("survival"),
                                       base_color=config.COLOR_ACCENT, hover_color=(150, 120, 255))
        self.board_button = Button((296, 436, 108, 52), "อันดับ", font=config.get_font(19, bold=True),
                                    sounds=manager.sounds, on_click=lambda: manager.go_to("challenger_board"),
                                    base_color=config.COLOR_BG_LIGHT, hover_color=config.COLOR_ACCENT)
        # แถวปุ่มมุมขวาบน: จัดเป็นแนวนอนแถบเดียวเหนือบอร์ดคะแนน (บอร์ดคะแนนเริ่มที่ y=230)
        # (เอาปุ่ม "เปลี่ยนผู้เล่น" ออกแล้ว เพราะทำงานซ้ำกับ "ออกจากระบบ" ในหน้าตั้งค่า)
        header_btn_font = config.get_font(18, bold=True)
        header_btn_w, header_btn_h, header_btn_gap = 160, 44, 12
        header_btn_y = 18
        header_btn_x = (config.SCREEN_WIDTH - 20) - 2 * header_btn_w - header_btn_gap
        self.profile_button = Button((header_btn_x, header_btn_y, header_btn_w, header_btn_h), "โปรไฟล์",
                                      font=header_btn_font,
                                      sounds=manager.sounds, on_click=lambda: manager.go_to("profile"),
                                      base_color=config.COLOR_BG_LIGHT, hover_color=config.COLOR_ACCENT)
        self.settings_button = Button((header_btn_x + (header_btn_w + header_btn_gap), header_btn_y,
                                        header_btn_w, header_btn_h), "ตั้งค่า",
                                       font=header_btn_font,
                                       sounds=manager.sounds, on_click=lambda: manager.go_to("settings"),
                                       base_color=config.COLOR_BG_LIGHT, hover_color=config.COLOR_ACCENT)

        # ปุ่มแต่งตัวมาสคอต: อยู่ซ้ายมาสคอต (ช่องว่างระหว่างการ์ดสถานะกับมาสคอต) กดตัวมาสคอตเองก็เข้าตู้เสื้อผ้าได้
        self.wardrobe_button = Button((470, 150, 220, 52), "แต่งตัวมาสคอต", font=config.get_font(20, bold=True),
                                       sounds=manager.sounds, on_click=lambda: manager.go_to("wardrobe"),
                                       base_color=config.COLOR_ACCENT, hover_color=(150, 120, 255))
        self.stats_button = Button((470, 88, 220, 48), "สถิติการเรียน", font=config.get_font(20, bold=True),
                                    sounds=manager.sounds, on_click=lambda: manager.go_to("stats"),
                                    base_color=config.COLOR_BG_LIGHT, hover_color=config.COLOR_ACCENT)
        self.mascot_rect = pygame.Rect(config.SCREEN_WIDTH - 175, 66, 110, 160)

        self.xp_bar = ProgressBar((40, 175, 340, 22))
        self.hearts = HeartMeter((40, 130))

    def on_enter(self):
        # แจ้งของแต่งตัวที่เพิ่งปลดล็อก (แจ้งครั้งเดียวต่อชิ้น - ดู wardrobe.newly_unlocked)
        fresh = wardrobe.newly_unlocked(self.manager.player_data)
        if fresh:
            self.manager.save()
            if self.manager.toast is not None:
                extra = f" เช่น \"{fresh[0].name}\"" if len(fresh) > 1 else f" \"{fresh[0].name}\""
                self.manager.toast.show(f"ปลดล็อกของแต่งตัวใหม่ {len(fresh)} ชิ้น!{extra} กด \"แต่งตัวมาสคอต\" เพื่อสวม",
                                        duration=4.0)
            self.manager.sounds.play_achievement()

    def _next_lesson(self):
        data = self.manager.player_data
        completed = set(data.get("completed_lessons", []))
        for unit, lesson in content.all_lessons_flat():
            if lesson.id not in completed:
                return unit, lesson
        return None, None

    def _continue_lesson(self):
        unit, lesson = self._next_lesson()
        if lesson is None:
            self.manager.toast.show("คุณเรียนจบทุกบทแล้ว เก่งมาก!")
            return
        self.manager.go_to("lesson", active_unit=unit, active_lesson=lesson)

    def update(self, dt):
        self.time += dt

    def handle_event(self, event):
        for btn in (self.path_button, self.continue_button, self.survival_button, self.board_button,
                    self.profile_button, self.settings_button, self.wardrobe_button, self.stats_button):
            btn.handle_event(event)
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.mascot_rect.collidepoint(event.pos):
            self.manager.sounds.play_click()
            self.manager.go_to("wardrobe")

    def draw(self, surface):
        fx.draw_gradient_background(surface)
        fx.draw_ambient_blobs(surface, self.time)
        data = self.manager.player_data

        header_font = config.get_font(30, bold=True)
        sub_font = config.get_font(18)

        name = data.get("name", "ผู้เล่น")
        level = config.level_from_xp(data.get("total_xp", 0))
        header = header_font.render(f"สวัสดี {name}!  (Level {level})", True, config.COLOR_TEXT)
        surface.blit(header, (40, 30))

        # การ์ดสรุปสถานะ (หัวใจ / XP)
        stat_card = pygame.Rect(24, 112, 380, 110)
        fx.draw_card(surface, stat_card)

        self.hearts.draw(surface, data.get("hearts", config.START_HEARTS))

        xp_in_level = config.xp_into_current_level(data.get("total_xp", 0))
        self.xp_bar.draw(surface, xp_in_level / 100, label=f"XP: {xp_in_level}/100")

        # มาสคอต
        mood = "excited" if data.get("hearts", 0) >= 2 else "worried"
        # ขนาด/ตำแหน่งเลือกให้หมวกที่สูงที่สุดไม่ชนปุ่มมุมขวาบน (ล่างสุด y=62) และตัว/หางไม่ล้ำการ์ดตารางคะแนน (เริ่ม y=230)
        mascot.draw_mascot(surface, (config.SCREEN_WIDTH - 120, 146), size=80, mood=mood, t=self.time)

        # ภารกิจประจำวัน (การ์ด)
        quest_card = pygame.Rect(24, 300, 380, 120)
        fx.draw_card(surface, quest_card)
        quest_title = sub_font.render("ภารกิจวันนี้", True, config.COLOR_TEXT)
        surface.blit(quest_title, (40, 312))
        quests = [
            ("ตอบถูก 5 ข้อ", data.get("correct_today", 0) >= 5),
            ("เรียนจบ 1 บท", data.get("lessons_today", 0) >= 1),
        ]
        qy = 348
        for text, done in quests:
            box_color = config.COLOR_SUCCESS if done else config.COLOR_BG
            pygame.draw.rect(surface, box_color, (40, qy, 22, 22), border_radius=5)
            if done:
                pygame.draw.line(surface, config.COLOR_WHITE, (44, qy + 11), (49, qy + 17), 3)
                pygame.draw.line(surface, config.COLOR_WHITE, (49, qy + 17), (58, qy + 5), 3)
            label = sub_font.render(text, True, config.COLOR_TEXT_MUTED if done else config.COLOR_TEXT)
            surface.blit(label, (72, qy - 2))
            qy += 34

        best = data.get("survival_best", 0)
        self.survival_button.text = f"โหมด Challenger ({best} ข้อ)" if best else "โหมด Challenger"
        self.survival_button.draw(surface)
        self.board_button.draw(surface)
        self.path_button.draw(surface)
        self.continue_button.draw(surface)
        self.profile_button.draw(surface)
        self.settings_button.draw(surface)
        self.wardrobe_button.draw(surface)
        self.stats_button.draw(surface)

        # --- ตารางคะแนนของจริง: ดึงจากผู้เล่นทุกคนที่เคยเล่นเกมนี้บนเครื่องนี้ ---
        board_rect = pygame.Rect(470, 230, 400, 380)
        fx.draw_card(surface, board_rect)

        mascot.draw_achievement_icon(surface, (board_rect.x + 30, board_rect.y + 24), 22, "trophy")
        board_title = sub_font.render("ตารางคะแนน", True, config.COLOR_TEXT)
        surface.blit(board_title, (board_rect.x + 48, board_rect.y + 14))

        rows = storage.leaderboard(self.manager.root, limit=8)
        row_font = config.get_font(17)
        ry = board_rect.y + 56
        my_key = self.manager.current_profile_key
        for rank, (pname, pxp, pstreak) in enumerate(rows, start=1):
            is_me = (self.manager.root["profiles"].get(my_key, {}).get("name") == pname
                     and self.manager.root["profiles"].get(my_key, {}).get("total_xp") == pxp)
            row_bg = config.COLOR_ACCENT if is_me else None
            if row_bg:
                pygame.draw.rect(surface, row_bg, (board_rect.x + 12, ry - 4, board_rect.width - 24, 30),
                                  border_radius=8)
            # อันดับ 1-3 ใช้สีเหรียญทอง/เงิน/ทองแดงแทนอีโมจิเหรียญ (ฟอนต์ระบบบางเครื่องแสดงอีโมจิเป็นกล่องว่าง)
            medal_colors = {1: (255, 215, 0), 2: (200, 200, 210), 3: (205, 140, 90)}
            rank_color = medal_colors.get(rank, config.COLOR_TEXT_MUTED)
            rank_font = config.get_font(17, bold=(rank <= 3))
            rank_surf = rank_font.render(f"#{rank}", True, rank_color)
            surface.blit(rank_surf, (board_rect.x + 20, ry))

            color = config.COLOR_WHITE if is_me else config.COLOR_TEXT_MUTED
            # ชื่อผู้เล่น -> ไฟ streak + จำนวนวัน (หลังชื่อ) -> XP
            name_surf = row_font.render(pname, True, color)
            surface.blit(name_surf, (board_rect.x + 60, ry))
            fx_x = board_rect.x + 60 + name_surf.get_width() + 16
            mascot.draw_achievement_icon(surface, (fx_x, ry + 11), 16, "flame")
            streak_surf = row_font.render(str(pstreak), True, config.COLOR_SECONDARY)
            surface.blit(streak_surf, (fx_x + 12, ry))
            xp_surf = row_font.render(f"- {pxp} XP", True, color)
            surface.blit(xp_surf, (fx_x + 12 + streak_surf.get_width() + 12, ry))
            ry += 34

        if not rows:
            empty_font = config.get_font(16)
            empty = empty_font.render("ยังไม่มีผู้เล่นในตาราง", True, config.COLOR_TEXT_MUTED)
            surface.blit(empty, (board_rect.x + 20, ry))
