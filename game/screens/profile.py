"""
screens/profile.py
---------------------
หน้าโปรไฟล์: Avatar ตัวอักษรแรกของชื่อ (สร้างด้วย CSS/pygame ไม่ใช้ภาพภายนอก),
สถิติสะสม, รายการ Achievement ทั้งหมด (ปลดล็อกแล้ว/ยังไม่ปลดล็อก) ที่กดดูรายละเอียด/เงื่อนไขได้,
และปุ่มรีเซ็ตความก้าวหน้าพร้อมกล่องยืนยัน
"""

import pygame

from .base import Screen
from .. import config, content, mascot, storage, fx
from ..widgets import Button


def wrap_to_width(font, text, max_w, max_lines):
    """ตัดข้อความให้อยู่ในความกว้าง max_w: ขึ้นบรรทัดใหม่ (ตามช่องว่างก่อน ถ้าไม่มีก็ตัดตามตัวอักษร - ภาษาไทยไม่มีช่องว่าง)
    ไม่เกิน max_lines บรรทัด ถ้ายังไม่พอจะลงท้ายด้วย … จึงไม่มีทางล้นกรอบ"""
    lines, cur = [], ""
    for ch in text:
        trial = cur + ch
        if font.size(trial)[0] <= max_w or not cur:
            cur = trial
            continue
        if ch == " ":                        # ตัดที่ช่องว่างพอดี
            lines.append(cur); cur = ""
        else:
            if " " in cur.strip():           # ถอยไปตัดที่ช่องว่างล่าสุด ไม่ผ่ากลางคำอังกฤษ
                head, _, tail = cur.rpartition(" ")
                lines.append(head); cur = tail + ch
            else:
                lines.append(cur); cur = ch
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and font.size(last + "…")[0] > max_w:
            last = last[:-1]
        lines[-1] = last + "…"
    return lines


class ProfileScreen(Screen):
    def __init__(self, manager):
        super().__init__(manager)
        self.back_button = Button((30, 20, 140, 44), "< กลับ", sounds=manager.sounds,
                                   on_click=lambda: manager.go_to("dashboard"),
                                   base_color=config.COLOR_BG_LIGHT, hover_color=config.COLOR_ACCENT)
        self.reset_button = Button((config.SCREEN_WIDTH - 250, 20, 220, 44), "รีเซ็ตความก้าวหน้า",
                                    font=config.get_font(18, bold=True), sounds=manager.sounds, on_click=self._ask_reset,
                                    base_color=config.COLOR_DANGER, hover_color=(200, 60, 60))

        self.confirm_yes = Button((config.SCREEN_WIDTH // 2 - 210, 360, 180, 54), "ยืนยัน รีเซ็ต",
                                   sounds=manager.sounds, on_click=self._do_reset,
                                   base_color=config.COLOR_DANGER, hover_color=(200, 60, 60))
        self.confirm_no = Button((config.SCREEN_WIDTH // 2 + 30, 360, 180, 54), "ยกเลิก",
                                  sounds=manager.sounds, on_click=self._cancel_reset)

        self.show_confirm = False

        # --- ป็อปอัปรายละเอียด Achievement (กดที่การ์ดความสำเร็จเพื่อดูเงื่อนไข/วิธีปลดล็อก) ---
        self.selected_achievement = None  # id ของ achievement ที่กำลังเปิดดูอยู่ (None = ปิดอยู่)
        self.ach_popup_rect = pygame.Rect(config.SCREEN_WIDTH // 2 - 230, 170, 460, 280)
        self.ach_close_button = Button(
            (self.ach_popup_rect.centerx - 70, self.ach_popup_rect.bottom - 56, 140, 40),
            "ปิด", sounds=manager.sounds, on_click=self._close_achievement_popup,
            base_color=config.COLOR_BG_LIGHT, hover_color=config.COLOR_ACCENT)

        self.achievement_rects = []  # [(rect, Achievement)] คำนวณใหม่ทุกเฟรมตอน draw() ใช้เช็คคลิก

        self.time = 0.0

    def on_enter(self):
        self.show_confirm = False
        self.selected_achievement = None

    def update(self, dt):
        self.time += dt

    def _ask_reset(self):
        self.show_confirm = True

    def _cancel_reset(self):
        self.show_confirm = False

    def _do_reset(self):
        # รีเซ็ตเฉพาะโปรไฟล์ของผู้เล่นคนนี้ - ไม่กระทบผู้เล่นคนอื่นที่แชร์เครื่องเดียวกัน
        storage.reset_profile(self.manager.root, self.manager.current_profile_key)
        self.manager.apply_outfit()  # รีเซ็ตแล้วชุดมาสคอตกลับเป็นค่าเริ่มต้นด้วย
        self.manager.save()
        self.show_confirm = False
        self.manager.toast.show("รีเซ็ตความก้าวหน้าเรียบร้อยแล้ว")

    def _close_achievement_popup(self):
        self.selected_achievement = None

    def handle_event(self, event):
        # ป็อปอัปรายละเอียด Achievement กันคลิกทะลุไปโดนอย่างอื่นด้านหลังเสมอ (เหมือนกล่องยืนยันรีเซ็ต)
        if self.selected_achievement:
            self.ach_close_button.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not self.ach_popup_rect.collidepoint(event.pos):
                    self._close_achievement_popup()
            return

        self.back_button.handle_event(event)
        self.reset_button.handle_event(event)

        if self.show_confirm:
            self.confirm_yes.handle_event(event)
            self.confirm_no.handle_event(event)
            return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for rect, ach in self.achievement_rects:
                if rect.collidepoint(event.pos):
                    self.selected_achievement = ach.id
                    self.manager.sounds.play_click()
                    break

    def draw(self, surface):
        fx.draw_gradient_background(surface)
        fx.draw_ambient_blobs(surface, self.time)
        data = self.manager.player_data
        name = data.get("name", "ผู้เล่น")
        level = config.level_from_xp(data.get("total_xp", 0))

        # Avatar: วงกลมสีพร้อมตัวอักษรแรกของชื่อ
        avatar_center = (config.SCREEN_WIDTH // 2, 140)
        pygame.draw.circle(surface, config.COLOR_ACCENT, avatar_center, 60)
        pygame.draw.circle(surface, config.COLOR_WHITE, avatar_center, 60, width=3)
        initial_font = config.get_font(48, bold=True)
        initial = initial_font.render(name[0].upper() if name else "?", True, config.COLOR_WHITE)
        surface.blit(initial, initial.get_rect(center=avatar_center))

        name_font = config.get_font(26, bold=True)
        name_surf = name_font.render(name, True, config.COLOR_TEXT)
        surface.blit(name_surf, name_surf.get_rect(center=(config.SCREEN_WIDTH // 2, 220)))

        stat_font = config.get_font(18)
        stats = [
            f"Level {level}",
            f"XP สะสม: {data.get('total_xp', 0)}",
            f"Streak: {data.get('streak', 0)} วัน",
            f"บทเรียนที่เรียนจบ: {data.get('lessons_finished_count', 0)} บท",
        ]
        y = 255
        for line in stats:
            surf = stat_font.render(line, True, config.COLOR_WHITE)  # ขาวล้วน ไม่ตัวหนา ไม่มีเงา
            surface.blit(surf, surf.get_rect(center=(config.SCREEN_WIDTH // 2, y)))
            y += 26

        # --- Achievements grid ---
        # เลย์เอาต์คำนวณจำนวนคอลัมน์ตามพื้นที่จริงของการ์ด แล้วขึ้นบรรทัดใหม่เมื่อเต็มแถว
        # (แก้บั๊กเดิมที่วางครบทุกช่องในแถวเดียวแบบตายตัว ทำให้การ์ดใบสุดท้ายเลยขอบการ์ด/จอออกไป)
        #
        # เพิ่มการ์การันตีไม่ให้ "การ์ดทั้งใบ" ล้นขอบจอด้วย: คำนวณพื้นที่สูงสุดที่เหลือจริง
        # จากตำแหน่งการ์ดถึงขอบจอล่าง (available_h) ก่อน แล้วค่อยลดความสูงกล่อง (box_h) ลง
        # อัตโนมัติถ้าจำนวน Achievement เยอะจนแถวทั้งหมดจะสูงเกินพื้นที่ที่มี - รองรับการเพิ่ม
        # Achievement ในอนาคตได้เรื่อย ๆ โดยไม่ต้องกลับมาคำนวณเลย์เอาต์ใหม่ทุกครั้ง
        n = len(content.ACHIEVEMENTS)
        box_h = 84
        col_gap, row_gap = 12, 14
        margin = 20
        title_area_h = 42
        bottom_margin = 20  # เว้นระยะห่างจากขอบจอล่าง กันการ์ดชนขอบจอพอดี

        ach_card_x, ach_card_y = 40, 390
        ach_card_w = config.SCREEN_WIDTH - 80

        usable_w = ach_card_w - margin * 2
        available_h = config.SCREEN_HEIGHT - ach_card_y - bottom_margin

        # ช่องละไม่แคบกว่า 120px (อ่านชื่อได้) แต่ไม่เกิน 5 คอลัมน์ แล้วขยายความกว้างกล่องให้เต็มแถวพอดีกรอบ
        columns = max(1, min(n, 5, (usable_w + col_gap) // (120 + col_gap)))
        box_w = (usable_w - (columns - 1) * col_gap) // columns
        rows = -(-n // columns)  # ceil division ไม่ต้อง import math

        rows_h_budget = available_h - title_area_h - margin
        max_box_h_fit = (rows_h_budget - (rows - 1) * row_gap) / rows if rows > 0 else box_h
        if max_box_h_fit < box_h:
            box_h = max(38, max_box_h_fit)  # ลดขนาดกล่องลงให้พอดีพื้นที่ แต่ไม่ให้เล็กจนอ่านไม่ออก

        ach_card_h = min(available_h, title_area_h + rows * box_h + (rows - 1) * row_gap + margin)
        ach_card = pygame.Rect(ach_card_x, ach_card_y, ach_card_w, int(ach_card_h))
        fx.draw_card(surface, ach_card, color=(35, 27, 52))

        ach_title_font = config.get_font(20, bold=True)
        ach_title = ach_title_font.render("ความสำเร็จ", True, config.COLOR_TEXT)
        surface.blit(ach_title, (ach_card.x + 20, ach_card.y + 10))
        hint_font = config.get_font(13)
        hint_surf = hint_font.render("(กดที่การ์ดเพื่อดูวิธีปลดล็อก)", True, config.COLOR_TEXT_MUTED)
        surface.blit(hint_surf, (ach_card.x + 20 + ach_title.get_width() + 12, ach_card.y + 15))

        unlocked = set(data.get("unlocked_achievements", []))
        self.achievement_rects = []
        start_x = ach_card.x + margin
        ax, ay = start_x, ach_card.y + title_area_h
        box_w_i, box_h_i = int(box_w), int(box_h)
        icon_size = max(18, min(34, int(box_h * 0.40)))
        for i, ach in enumerate(content.ACHIEVEMENTS):
            is_unlocked = ach.id in unlocked
            box = pygame.Rect(int(ax), int(ay), box_w_i, box_h_i)
            pygame.draw.rect(surface, config.COLOR_BG_LIGHT if is_unlocked else (35, 30, 45), box, border_radius=12)
            border_color = config.COLOR_SECONDARY if is_unlocked else config.COLOR_LOCK
            if self.selected_achievement == ach.id:
                border_color = config.COLOR_ACCENT
            pygame.draw.rect(surface, border_color, box, width=2, border_radius=12)
            # ตำแหน่งไอคอน/ชื่อคิดเป็นสัดส่วนของความสูงกล่อง (ไม่ใช่พิกเซลตายตัว) เพื่อให้ยังดูดีแม้กล่องจะถูกย่อลง
            icon_center = (box.centerx, box.y + int(box_h * 0.33))
            if is_unlocked:
                mascot.draw_achievement_icon(surface, icon_center, icon_size, ach.icon)
            else:
                pygame.draw.circle(surface, config.COLOR_LOCK, icon_center, icon_size // 2)
            small_font = config.get_font(13, bold=True)
            title_color = config.COLOR_TEXT if is_unlocked else config.COLOR_TEXT_MUTED
            # ชื่อยาว: ขึ้น 2 บรรทัดในกล่อง (ไม่ล้นกรอบ) ชื่อสั้นอยู่กึ่งกลางบรรทัดเดียว
            title_lines = wrap_to_width(small_font, ach.title, box_w - 16, 2 if box_h >= 70 else 1)
            line_h = 16
            if len(title_lines) == 1:
                ys = [box.y + int(box_h * 0.74)]
            else:
                top = box.y + int(box_h * 0.55)
                ys = [top + k * line_h + line_h // 2 for k in range(len(title_lines))]
            for line, cy in zip(title_lines, ys):
                title_surf = small_font.render(line, True, title_color)
                surface.blit(title_surf, title_surf.get_rect(center=(box.centerx, cy)))

            self.achievement_rects.append((box, ach))

            if (i + 1) % columns == 0:
                ax = start_x
                ay += box_h + row_gap
            else:
                ax += box_w + col_gap  # (ax คิดจาก box_w ที่ปรับให้พอดีแถวแล้ว)

        self.back_button.draw(surface)
        self.reset_button.draw(surface)

        if self.show_confirm:
            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            surface.blit(overlay, (0, 0))

            box = pygame.Rect(config.SCREEN_WIDTH // 2 - 260, 260, 520, 220)
            pygame.draw.rect(surface, config.COLOR_BG_LIGHT, box, border_radius=16)
            pygame.draw.rect(surface, config.COLOR_DANGER, box, width=2, border_radius=16)

            warn_font = config.get_font(22, bold=True)
            warn = warn_font.render("ยืนยันการรีเซ็ตความก้าวหน้า?", True, config.COLOR_TEXT)
            surface.blit(warn, warn.get_rect(center=(config.SCREEN_WIDTH // 2, 300)))
            sub_font = config.get_font(16)
            sub = sub_font.render("การกระทำนี้จะลบ XP, Streak, บทเรียนที่เรียนจบ และรหัสผ่านทั้งหมด",
                                   True, config.COLOR_TEXT_MUTED)
            surface.blit(sub, sub.get_rect(center=(config.SCREEN_WIDTH // 2, 330)))

            self.confirm_yes.draw(surface)
            self.confirm_no.draw(surface)

        # --- ป็อปอัปรายละเอียด Achievement: แสดงชื่อ/สถานะ/เงื่อนไขการปลดล็อก ---
        if self.selected_achievement:
            ach = content.ACHIEVEMENT_MAP.get(self.selected_achievement)
            if ach:
                overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 150))
                surface.blit(overlay, (0, 0))

                box = self.ach_popup_rect
                is_unlocked = ach.id in unlocked
                fx.draw_card(surface, box, radius=18, color=config.COLOR_BG_LIGHT)
                border_color = config.COLOR_SECONDARY if is_unlocked else config.COLOR_LOCK
                pygame.draw.rect(surface, border_color, box, width=2, border_radius=18)

                icon_center = (box.centerx, box.y + 58)
                if is_unlocked:
                    mascot.draw_achievement_icon(surface, icon_center, 44, ach.icon)
                else:
                    pygame.draw.circle(surface, config.COLOR_LOCK, icon_center, 23)

                title_font = config.get_font(22, bold=True)
                title_line = wrap_to_width(title_font, ach.title, box.width - 40, 1)[0]
                title_surf = title_font.render(title_line, True, config.COLOR_TEXT)
                surface.blit(title_surf, title_surf.get_rect(center=(box.centerx, box.y + 108)))

                status_font = config.get_font(15, bold=True)
                status_text = "ปลดล็อกแล้ว!" if is_unlocked else "ยังไม่ปลดล็อก"
                status_color = config.COLOR_SUCCESS if is_unlocked else config.COLOR_TEXT_MUTED
                status_surf = status_font.render(status_text, True, status_color)
                surface.blit(status_surf, status_surf.get_rect(center=(box.centerx, box.y + 136)))

                cond_label_font = config.get_font(14, bold=True)
                cond_label_text = "เงื่อนไขที่ทำสำเร็จแล้ว:" if is_unlocked else "วิธีปลดล็อก:"
                cond_label_surf = cond_label_font.render(cond_label_text, True, config.COLOR_TEXT_MUTED)
                surface.blit(cond_label_surf, cond_label_surf.get_rect(center=(box.centerx, box.y + 168)))

                desc_font = config.get_font(17)
                desc_lines = wrap_to_width(desc_font, ach.description, box.width - 48, 2)
                first_y = box.y + 196 - (len(desc_lines) - 1) * 12
                for k, line in enumerate(desc_lines):
                    desc_surf = desc_font.render(line, True, config.COLOR_TEXT)
                    surface.blit(desc_surf, desc_surf.get_rect(center=(box.centerx, first_y + k * 24)))

                self.ach_close_button.draw(surface)
