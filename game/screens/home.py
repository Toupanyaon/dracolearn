"""
screens/home.py
----------------
หน้าแรกของเกม: โลโก้แบรนด์ "DracoLearn", มาสคอตเบลซ, ช่องกรอกชื่อผู้เล่น และช่องกรอกรหัสผ่าน

กติกาการล็อกอิน/สมัคร (ระบบรหัสผ่าน):
    - พิมพ์ "ชื่อใหม่" (ไม่เคยมีใครใช้ชื่อนี้เล่นเกมนี้มาก่อน) + ตั้งรหัสผ่าน (อย่างน้อย
      config.MIN_PASSWORD_LENGTH ตัวอักษร) -> สร้างโปรไฟล์ใหม่ พร้อมบันทึกรหัสผ่านนี้ไว้ทันที
    - พิมพ์ "ชื่อเดิม" ที่เคยตั้งรหัสผ่านไว้แล้ว -> ต้องใส่รหัสผ่านให้ตรงกับที่ตั้งไว้ ถึงจะเข้าเล่นต่อได้
      ถ้ารหัสผ่านผิดจะขึ้นข้อความแจ้งเตือน และไม่ให้เข้าเกม (ไม่โหลด/ไม่สลับโปรไฟล์ให้)
    - พิมพ์ "ชื่อเดิม" ที่เป็นเซฟเก่าแบบยังไม่เคยมีระบบรหัสผ่าน (มาจากไฟล์เซฟรุ่นก่อน) ->
      เข้าเล่นต่อได้โดยไม่บังคับใส่รหัส แต่ถ้าใส่รหัสผ่านมาด้วยตอนนี้ จะถือเป็นการตั้งรหัสผ่าน
      ให้โปรไฟล์นั้นทันที (อัปเกรดให้มีรหัสผ่านจากนี้ไป)
"""

import pygame

from .base import Screen
from .. import config, mascot, fx, storage
from ..widgets import Button, TextInputBox


class HomeScreen(Screen):
    def __init__(self, manager):
        super().__init__(manager)
        self.time = 0.0
        self.error_message = ""

        center_x = config.SCREEN_WIDTH // 2

        self.name_input = TextInputBox(
            (center_x - 160, 304, 320, 44),
            placeholder="พิมพ์ชื่อของคุณที่นี่...",
        )
        self.password_input = TextInputBox(
            (center_x - 160, 376, 320, 44),
            placeholder="พิมพ์รหัสผ่านที่นี่...",
            is_password=True,
        )

        self.start_button = Button(
            (center_x - 110, 434, 220, 56),
            "เริ่มผจญภัย!",
            sounds=manager.sounds,
            on_click=self._start,
        )

    def on_enter(self):
        self.error_message = ""
        # ถ้ามีผู้เล่น active อยู่แล้ว (เคยกรอกชื่อไปก่อนหน้านี้) ให้เติมชื่อไว้ให้เลย
        existing_name = self.manager.player_data.get("name", "")
        self.name_input.text = existing_name
        self.password_input.clear()
        # โฟกัสเริ่มต้นที่ช่องชื่อเสมอ (ไม่โชว์รหัสผ่านเดิมค้างไว้เพื่อความปลอดภัย)
        self.name_input.active = True
        self.password_input.active = False

    def _start(self):
        name = self.name_input.text.strip()
        password = self.password_input.text

        if not name:
            self.error_message = "กรุณาพิมพ์ชื่อก่อนเริ่มเรียนนะ!"
            return

        existing_profile = storage.find_profile(self.manager.root, name)

        if existing_profile is not None:
            # ชื่อนี้เคยเล่นมาก่อน -> ถ้าเคยตั้งรหัสผ่านไว้ ต้องใส่ให้ตรงถึงจะเข้าได้
            if storage.has_password(existing_profile):
                if not password:
                    self.error_message = "ชื่อนี้มีรหัสผ่านแล้ว กรุณาใส่รหัสผ่านด้วย"
                    return
                if not storage.verify_password(existing_profile, password):
                    self.error_message = "รหัสผ่านไม่ถูกต้อง กรุณาลองใหม่"
                    return
            # ถ้ายังไม่เคยตั้งรหัสผ่าน (โปรไฟล์เก่า) จะปล่อยผ่านไปเลย ไม่บังคับรหัส
        else:
            # ชื่อใหม่ -> ต้องตั้งรหัสผ่านให้เรียบร้อยก่อนสร้างโปรไฟล์
            if len(password) < config.MIN_PASSWORD_LENGTH:
                self.error_message = (
                    f"ชื่อนี้ยังไม่เคยเล่น กรุณาตั้งรหัสผ่านอย่างน้อย "
                    f"{config.MIN_PASSWORD_LENGTH} ตัวอักษร"
                )
                return

        # ชื่อต่างกัน = คนละคน: switch_profile จะโหลดของเดิมถ้าเคยมี หรือสร้างใหม่ถ้ายังไม่เคย
        profile = self.manager.switch_profile(name)

        # ตั้ง/อัปเกรดรหัสผ่านให้โปรไฟล์ที่ยังไม่มีรหัสผ่าน ถ้าผู้เล่นใส่รหัสผ่านมาด้วย
        if not storage.has_password(profile) and password:
            storage.set_password(profile, password)

        streak_increased = storage.register_login_for_streak(profile)
        self.manager.save()

        if streak_increased and profile["streak"] > 1:
            self.manager.toast.show(f'ต่อเนื่อง {profile["streak"]} วันแล้ว! สู้ๆ')
        elif profile.get("total_xp", 0) > 0:
            self.manager.toast.show(f'ยินดีต้อนรับกลับมา {profile["name"]}!')

        self.manager.go_to("dashboard")

    def handle_event(self, event):
        self.name_input.handle_event(event)
        self.password_input.handle_event(event)
        self.start_button.handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._start()
            elif event.key == pygame.K_TAB:
                # สลับโฟกัสระหว่างช่องชื่อ <-> ช่องรหัสผ่านด้วยปุ่ม Tab
                self.name_input.active, self.password_input.active = (
                    self.password_input.active, self.name_input.active,
                )

    def update(self, dt):
        self.time += dt
        self.name_input.update(dt)
        self.password_input.update(dt)

    def draw(self, surface):
        fx.draw_gradient_background(surface)
        fx.draw_ambient_blobs(surface, self.time)

        center_x = config.SCREEN_WIDTH // 2

        title_font = config.get_font(40, bold=True)
        subtitle_font = config.get_font(18)
        hint_font = config.get_font(14)

        title = title_font.render("DracoLearn", True, config.COLOR_PRIMARY)
        surface.blit(title, title.get_rect(center=(center_x, 74)))

        subtitle = subtitle_font.render("เรียนภาษาอังกฤษไปกับเบลซ มังกรน้อยผู้ใจดี", True, (255, 255, 255))
        surface.blit(subtitle, subtitle.get_rect(center=(center_x, 110)))

        hint = hint_font.render(
            "ชื่อเดิม+รหัสเดิม = เล่นต่อ  /  ชื่อใหม่+ตั้งรหัสใหม่ = เริ่มโปรไฟล์ใหม่",
            True, (255, 255, 255),
        )
        surface.blit(hint, hint.get_rect(center=(center_x, 136)))

        mascot.draw_mascot(surface, (center_x, 205), size=110, mood="excited", t=self.time)

        label_font = config.get_font(16)
        name_label = label_font.render("ชื่อผู้เล่น", True, config.COLOR_TEXT)
        surface.blit(name_label, (self.name_input.rect.x, self.name_input.rect.y - 22))

        password_label = label_font.render("รหัสผ่าน", True, config.COLOR_TEXT)
        surface.blit(password_label, (self.password_input.rect.x, self.password_input.rect.y - 22))

        self.name_input.draw(surface)
        self.password_input.draw(surface)
        self.start_button.draw(surface)

        if self.error_message:
            err_font = config.get_font(15, bold=True)
            err_surf = err_font.render(self.error_message, True, config.COLOR_DANGER)
            surface.blit(err_surf, err_surf.get_rect(center=(center_x, 512)))
