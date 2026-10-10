"""
screens/settings_screen.py
-----------------------------
หน้าตั้งค่า: เปิด/ปิดเสียง, สไลเดอร์เสียงพื้นหลัง + สไลเดอร์เสียงเอฟเฟกต์ (แยกกัน), ความเร็วเสียงพูด, เปลี่ยนรหัสผ่าน
บันทึกลง LocalStorage (ไฟล์ JSON) ทันทีที่มีการเปลี่ยนแปลง
"""

import pygame

from .base import Screen
from .. import config, fx, storage, mascot
from ..widgets import Button, TextInputBox, Slider


class SettingsScreen(Screen):
    # ตัวเลือกความเร็วเสียงพูดที่ปรับได้ (ตัวคูณ, ป้ายข้อความที่แสดงบนปุ่ม)
    SPEECH_RATE_OPTIONS = [(0.5, "x0.5"), (0.75, "x0.75"), (1.0, "x1"), (1.25, "x1.25"), (1.5, "x1.5")]

    def __init__(self, manager):
        super().__init__(manager)
        self.time = 0.0
        self.back_button = Button((30, 20, 140, 44), "< กลับ", sounds=manager.sounds,
                                   on_click=manager.close_settings,
                                   base_color=config.COLOR_BG_LIGHT, hover_color=config.COLOR_ACCENT)

        self.sound_toggle = Button((350, 145, 200, 50), "", sounds=manager.sounds, on_click=self._toggle_sound)

        # สไลเดอร์แยก 3 ตัว: เสียงพื้นหลัง / เสียงเอฟเฟกต์ / เสียงโจทย์ (พูด) - ลากได้อิสระต่อกัน
        data = manager.player_data
        self.music_slider = Slider((350, 240, 250, 10), value=data.get("music_volume", 0.4),
                                    on_change=self._set_music_volume, on_release=lambda v: manager.save(),
                                    fill_color=config.COLOR_ACCENT)
        self.effects_slider = Slider((350, 290, 250, 10), value=data.get("volume", 1.0),
                                      on_change=self._set_effects_volume,
                                      on_release=self._effects_slider_released,
                                      fill_color=config.COLOR_SECONDARY)
        self.speech_slider = Slider((350, 340, 250, 10), value=data.get("speech_volume", 1.0),
                                     on_change=self._set_speech_volume,
                                     on_release=self._speech_slider_released,
                                     fill_color=config.COLOR_SUCCESS)

        self.test_sound_button = Button((640, 142, 190, 44), "   ทดสอบเสียง", sounds=manager.sounds,
                                         on_click=self._test_sound,
                                         base_color=config.COLOR_ACCENT, hover_color=config.COLOR_PRIMARY)
        self._pending_test_check = 0.0
        self._pending_test_fail_count_before = 0

        # ความเร็วเสียงพูด: ปุ่มแบบ segmented control ให้เลือกได้ทีละอัน (กดปุ่มไหนอยู่ = ไฮไลต์ปุ่มนั้น)
        self.speed_buttons = []
        speed_x = 350
        for value, label in self.SPEECH_RATE_OPTIONS:
            btn = Button((speed_x, 380, 82, 44), label, sounds=manager.sounds,
                         on_click=lambda v=value: self._set_speech_rate(v))
            self.speed_buttons.append((value, btn))
            speed_x += 90

        self.change_password_button = Button((350, 440, 300, 50), "เปลี่ยนรหัสผ่าน", sounds=manager.sounds,
                                              on_click=self._open_password_form,
                                              base_color=config.COLOR_ACCENT, hover_color=config.COLOR_PRIMARY)

        self.exit_button = Button((60, 515, 340, 54), "ออกจากเกม", sounds=manager.sounds,
                                   on_click=self._ask_exit,
                                   base_color=config.COLOR_DANGER, hover_color=(200, 60, 60))
        self.logout_button = Button((420, 515, 340, 54), "ออกจากระบบ (Log out)", sounds=manager.sounds,
                                     on_click=self._ask_logout,
                                     base_color=config.COLOR_BG_LIGHT, hover_color=config.COLOR_ACCENT)

        self.confirm_yes = Button((config.SCREEN_WIDTH // 2 - 210, 280, 180, 54), "ยืนยัน",
                                   sounds=manager.sounds, on_click=self._do_confirm,
                                   base_color=config.COLOR_DANGER, hover_color=(200, 60, 60))
        self.confirm_no = Button((config.SCREEN_WIDTH // 2 + 30, 280, 180, 54), "ยกเลิก",
                                  sounds=manager.sounds, on_click=self._cancel_confirm)

        self.show_confirm = None  # None | "exit" | "logout"

        # --- ฟอร์มเปลี่ยนรหัสผ่าน (overlay แยกจาก show_confirm) ---
        center_x = config.SCREEN_WIDTH // 2
        field_w = 280
        self.old_password_input = TextInputBox((center_x - field_w // 2, 205, field_w, 42),
                                                 placeholder="รหัสผ่านเดิม (เว้นว่างได้ถ้ายังไม่เคยตั้ง)",
                                                 is_password=True)
        self.new_password_input = TextInputBox((center_x - field_w // 2, 270, field_w, 42),
                                                 placeholder="รหัสผ่านใหม่", is_password=True)
        self.confirm_password_input = TextInputBox((center_x - field_w // 2, 335, field_w, 42),
                                                     placeholder="ยืนยันรหัสผ่านใหม่อีกครั้ง", is_password=True)
        self.save_password_button = Button((center_x - 190, 420, 170, 50), "บันทึก", sounds=manager.sounds,
                                            on_click=self._save_password_form,
                                            base_color=config.COLOR_SUCCESS, hover_color=(60, 170, 110))
        self.cancel_password_button = Button((center_x + 20, 420, 170, 50), "ยกเลิก", sounds=manager.sounds,
                                              on_click=self._cancel_password_form)
        self.show_password_form = False
        self.password_form_error = ""

    def on_enter(self):
        data = self.manager.player_data
        self.music_slider.value = data.get("music_volume", 0.4)
        self.effects_slider.value = data.get("volume", 1.0)
        self.speech_slider.value = data.get("speech_volume", 1.0)
        self.music_slider.dragging = self.effects_slider.dragging = self.speech_slider.dragging = False
        self.show_confirm = None
        self.show_password_form = False
        self.password_form_error = ""

    def _toggle_sound(self):
        data = self.manager.player_data
        data["sound_on"] = not data.get("sound_on", True)
        self.manager.sounds.set_enabled(data["sound_on"])
        self.manager.save()

    def _set_music_volume(self, value):
        self.manager.player_data["music_volume"] = value
        self.manager.sounds.set_music_volume(value)

    def _set_effects_volume(self, value):
        self.manager.player_data["volume"] = value
        self.manager.sounds.set_volume(value)

    def _effects_slider_released(self, value):
        self.manager.save()
        self.manager.sounds.play_correct()  # เล่นเสียงตัวอย่างให้ได้ยินระดับเสียงเอฟเฟกต์ใหม่ทันทีที่ปล่อยสไลเดอร์

    def _set_speech_volume(self, value):
        self.manager.player_data["speech_volume"] = value
        self.manager.sounds.set_speech_volume(value)

    def _speech_slider_released(self, value):
        self.manager.save()
        self.manager.sounds.speak("This is the question voice volume.")  # พูดตัวอย่างให้ได้ยินระดับเสียงโจทย์ใหม่ทันที

    def _set_speech_rate(self, multiplier: float):
        data = self.manager.player_data
        data["speech_rate"] = multiplier
        self.manager.sounds.set_speech_rate(multiplier)
        self.manager.save()
        # พูดตัวอย่างสั้น ๆ ทันทีให้ได้ยินความเร็วใหม่เลย โดยไม่ต้องกดปุ่มทดสอบเสียงซ้ำ
        self.manager.sounds.speak("This is the new speech speed.")

    def _test_sound(self):
        """ทดสอบเสียงพูดจริง แล้วรายงานผลตามจริง (สำเร็จ/ล้มเหลว พร้อมเหตุผล) แทนการเดา"""
        sounds = self.manager.sounds
        if not sounds.enabled:
            self.manager.toast.show("เสียงถูกปิดอยู่ - เปิดเสียงเอฟเฟกต์ก่อนแล้วลองใหม่", duration=3.0)
            return

        if not sounds.tts_available:
            reason = sounds.last_error or "ไม่ทราบสาเหตุ"
            self.manager.toast.show(f"ไม่พบระบบเสียงพูดในเครื่องนี้: {reason}", duration=5.0)
            return

        # จำจำนวนครั้งที่ล้มเหลวไว้ก่อน แล้วค่อยเช็กอีกทีหลังหน่วงเวลา ให้ worker thread มีเวลาพูดจริงก่อน
        self._pending_test_fail_count_before = sounds.speak_stats["fail"]
        spoke = sounds.speak("Hello! This is a sound test. Can you hear me?")
        if not spoke:
            self.manager.toast.show("เรียก speak() ไม่สำเร็จ (พูดอยู่แล้ว หรือปิดเสียงอยู่)", duration=3.0)
            return

        engine_name = "SAPI5 (Windows)" if sounds.engine_type == "sapi" else "pyttsx3"
        self.manager.toast.show(f"กำลังพูดทดสอบผ่าน {engine_name}... ฟังออกไหม?", duration=2.5)
        self._pending_test_check = 2.5  # เช็กผลลัพธ์จริงอีกครั้งใน 2.5 วินาที

    def _ask_exit(self):
        self.show_confirm = "exit"

    def _ask_logout(self):
        self.show_confirm = "logout"

    def _cancel_confirm(self):
        self.show_confirm = None

    def _do_confirm(self):
        action = self.show_confirm
        self.show_confirm = None
        if action == "exit":
            self.manager.quit_game()
        elif action == "logout":
            self.manager.logout()

    # --- เปลี่ยนรหัสผ่าน ---
    def _open_password_form(self):
        self.old_password_input.clear()
        self.new_password_input.clear()
        self.confirm_password_input.clear()
        self.old_password_input.active = True
        self.new_password_input.active = False
        self.confirm_password_input.active = False
        self.password_form_error = ""
        self.show_password_form = True

    def _cancel_password_form(self):
        self.show_password_form = False

    def _save_password_form(self):
        data = self.manager.player_data
        old_pw = self.old_password_input.text
        new_pw = self.new_password_input.text
        confirm_pw = self.confirm_password_input.text

        # ถ้าโปรไฟล์นี้เคยตั้งรหัสผ่านไว้แล้ว ต้องยืนยันรหัสเดิมให้ถูกก่อน
        if storage.has_password(data) and not storage.verify_password(data, old_pw):
            self.password_form_error = "รหัสผ่านเดิมไม่ถูกต้อง"
            return
        if len(new_pw) < config.MIN_PASSWORD_LENGTH:
            self.password_form_error = f"รหัสผ่านใหม่ต้องมีอย่างน้อย {config.MIN_PASSWORD_LENGTH} ตัวอักษร"
            return
        if new_pw != confirm_pw:
            self.password_form_error = "รหัสผ่านใหม่ทั้งสองช่องไม่ตรงกัน"
            return

        storage.set_password(data, new_pw)
        self.manager.save()
        self.show_password_form = False
        self.manager.toast.show("เปลี่ยนรหัสผ่านเรียบร้อยแล้ว")

    def handle_event(self, event):
        if self.show_password_form:
            self.old_password_input.handle_event(event)
            self.new_password_input.handle_event(event)
            self.confirm_password_input.handle_event(event)
            self.save_password_button.handle_event(event)
            self.cancel_password_button.handle_event(event)
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._save_password_form()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._cancel_password_form()
            return

        if self.show_confirm:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._cancel_confirm()
                return
            self.confirm_yes.handle_event(event)
            self.confirm_no.handle_event(event)
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.manager.close_settings()   # Esc ซ้ำอีกที = ปิดหน้าตั้งค่า กลับหน้าเดิม
            return

        self.back_button.handle_event(event)
        self.sound_toggle.handle_event(event)
        self.music_slider.handle_event(event)
        self.effects_slider.handle_event(event)
        self.speech_slider.handle_event(event)
        self.test_sound_button.handle_event(event)
        for _, btn in self.speed_buttons:
            btn.handle_event(event)
        self.change_password_button.handle_event(event)
        self.exit_button.handle_event(event)
        self.logout_button.handle_event(event)

    def update(self, dt):
        self.time += dt
        if self.show_password_form:
            self.old_password_input.update(dt)
            self.new_password_input.update(dt)
            self.confirm_password_input.update(dt)

        # เช็กผลลัพธ์การทดสอบเสียงจริง หลังจากรอให้ worker thread มีเวลาพูดเสร็จแล้ว
        if self._pending_test_check > 0:
            self._pending_test_check -= dt
            if self._pending_test_check <= 0:
                sounds = self.manager.sounds
                fail_now = sounds.speak_stats["fail"]
                if fail_now > self._pending_test_fail_count_before:
                    self.manager.toast.show(f"เสียงพูดล้มเหลวจริง: {sounds.last_error}", duration=6.0)
                elif sounds.is_speaking:
                    # ยังพูดไม่จบ (ประโยคยาว) รอเช็กอีกรอบ
                    self._pending_test_check = 1.5
                else:
                    self.manager.toast.show(
                        "ระบบส่งคำสั่งพูดสำเร็จโดยไม่มี error ถ้ายังไม่ได้ยินเสียง ให้เช็กลำโพง/"
                        "ตัวเลือกเสียงพูดของ Windows (Settings > Time & Language > Speech)", duration=6.0)

    def draw(self, surface):
        fx.draw_gradient_background(surface)
        fx.draw_ambient_blobs(surface, self.time)
        data = self.manager.player_data

        card = pygame.Rect(40, 125, config.SCREEN_WIDTH - 80, 465)
        fx.draw_card(surface, card)

        title_font = config.get_font(28, bold=True)
        title = title_font.render("ตั้งค่า", True, config.COLOR_TEXT)
        surface.blit(title, (60, 90))

        label_font = config.get_font(20)
        value_font = config.get_font(24, bold=True)

        # เสียงเอฟเฟกต์ (เปิด/ปิด)
        sound_label = label_font.render("เสียงทั้งหมด", True, config.COLOR_TEXT)
        surface.blit(sound_label, (60, 160))
        self.sound_toggle.text = "เปิดอยู่" if data.get("sound_on", True) else "ปิดอยู่"
        self.sound_toggle.base_color = config.COLOR_SUCCESS if data.get("sound_on", True) else config.COLOR_LOCK
        self.sound_toggle.draw(surface)

        # สไลเดอร์เสียงพื้นหลัง / เสียงเอฟเฟกต์ (แยกกัน)
        music_label = label_font.render("เสียงพื้นหลัง", True, config.COLOR_TEXT)
        surface.blit(music_label, (60, 222))
        self.music_slider.draw(surface)
        music_pct = value_font.render(f"{int(round(self.music_slider.value * 100))}%", True, config.COLOR_SECONDARY)
        surface.blit(music_pct, (620, 226))

        effects_label = label_font.render("เสียงเอฟเฟกต์", True, config.COLOR_TEXT)
        surface.blit(effects_label, (60, 272))
        self.effects_slider.draw(surface)
        effects_pct = value_font.render(f"{int(round(self.effects_slider.value * 100))}%", True, config.COLOR_SECONDARY)
        surface.blit(effects_pct, (620, 276))

        speech_label = label_font.render("เสียงโจทย์", True, config.COLOR_TEXT)
        surface.blit(speech_label, (60, 322))
        speech_hint = config.get_font(13).render("(เสียงพูดอ่านคำ/โจทย์)", True, config.COLOR_TEXT_MUTED)
        surface.blit(speech_hint, (60 + speech_label.get_width() + 8, 328))
        self.speech_slider.draw(surface)
        speech_pct = value_font.render(f"{int(round(self.speech_slider.value * 100))}%", True, config.COLOR_SECONDARY)
        surface.blit(speech_pct, (620, 326))

        # ปุ่มทดสอบเสียงจริง + สถานะเอนจินเสียงพูดปัจจุบัน (ให้เห็นตรง ๆ ว่าใช้ SAPI หรือ pyttsx3 หรือไม่มีเลย)
        self.test_sound_button.draw(surface)
        mascot.draw_achievement_icon(
            surface, (self.test_sound_button.rect.x + 26, self.test_sound_button.rect.centery), 18, "speaker")
        engine_label = {"sapi": "SAPI5 (Windows)", "pyttsx3": "pyttsx3"}.get(
            self.manager.sounds.engine_type, "ไม่พบระบบเสียงพูด")
        engine_font = config.get_font(13)
        engine_surf = engine_font.render(f"เอนจิน: {engine_label}", True, config.COLOR_TEXT_MUTED)
        surface.blit(engine_surf, (640, 194))
        th_ok = self.manager.sounds.thai_voice_available
        th_color = config.COLOR_SUCCESS if th_ok else config.COLOR_TEXT_MUTED
        th_surf = engine_font.render(
            f"เสียงไทย: {'มี' if th_ok else 'ไม่มี (อ่านได้แค่คำอังกฤษ)'}", True, th_color)
        surface.blit(th_surf, (640, 211))

        # ความเร็วเสียงพูด (ใช้ตอนฟังคำศัพท์/ฟังโจทย์ในหน้าบทเรียน)
        speed_label = label_font.render("ความเร็วเสียงพูด", True, config.COLOR_TEXT)
        surface.blit(speed_label, (60, 395))
        current_rate = data.get("speech_rate", 1.0)
        for value, btn in self.speed_buttons:
            is_selected = abs(value - current_rate) < 1e-6
            btn.base_color = config.COLOR_SECONDARY if is_selected else config.COLOR_BG_LIGHT
            btn.text_color = config.COLOR_TEXT_DARK if is_selected else config.COLOR_TEXT
            btn.draw(surface)

        # รหัสผ่าน
        password_label = label_font.render("รหัสผ่าน", True, config.COLOR_TEXT)
        surface.blit(password_label, (60, 455))
        password_status = "ตั้งไว้แล้ว" if storage.has_password(data) else "ยังไม่ได้ตั้ง"
        status_surf = config.get_font(14).render(password_status, True, config.COLOR_TEXT_MUTED)
        surface.blit(status_surf, (60, 482))
        self.change_password_button.draw(surface)

        # ออกจากเกม / ออกจากระบบ
        self.exit_button.draw(surface)
        self.logout_button.draw(surface)

        self.back_button.draw(surface)

        if self.show_password_form:
            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            surface.blit(overlay, (0, 0))

            box = pygame.Rect(config.SCREEN_WIDTH // 2 - 220, 140, 440, 350)
            pygame.draw.rect(surface, config.COLOR_BG_LIGHT, box, border_radius=16)
            pygame.draw.rect(surface, config.COLOR_ACCENT, box, width=2, border_radius=16)

            form_title_font = config.get_font(22, bold=True)
            form_title = form_title_font.render("เปลี่ยนรหัสผ่าน", True, config.COLOR_TEXT)
            surface.blit(form_title, form_title.get_rect(center=(config.SCREEN_WIDTH // 2, 170)))

            small_label_font = config.get_font(14)
            old_label = small_label_font.render("รหัสผ่านเดิม", True, config.COLOR_TEXT_MUTED)
            surface.blit(old_label, (self.old_password_input.rect.x, self.old_password_input.rect.y - 18))
            new_label = small_label_font.render("รหัสผ่านใหม่", True, config.COLOR_TEXT_MUTED)
            surface.blit(new_label, (self.new_password_input.rect.x, self.new_password_input.rect.y - 18))
            confirm_label = small_label_font.render("ยืนยันรหัสผ่านใหม่", True, config.COLOR_TEXT_MUTED)
            surface.blit(confirm_label,
                         (self.confirm_password_input.rect.x, self.confirm_password_input.rect.y - 18))

            self.old_password_input.draw(surface)
            self.new_password_input.draw(surface)
            self.confirm_password_input.draw(surface)

            if self.password_form_error:
                err_font = config.get_font(14, bold=True)
                err_surf = err_font.render(self.password_form_error, True, config.COLOR_DANGER)
                surface.blit(err_surf, err_surf.get_rect(center=(config.SCREEN_WIDTH // 2, 395)))

            self.save_password_button.draw(surface)
            self.cancel_password_button.draw(surface)

        elif self.show_confirm:
            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            surface.blit(overlay, (0, 0))

            box = pygame.Rect(config.SCREEN_WIDTH // 2 - 260, 180, 520, 180)
            pygame.draw.rect(surface, config.COLOR_BG_LIGHT, box, border_radius=16)
            pygame.draw.rect(surface, config.COLOR_DANGER, box, width=2, border_radius=16)

            warn_font = config.get_font(22, bold=True)
            message = ("ต้องการออกจากเกมใช่หรือไม่?" if self.show_confirm == "exit"
                       else "ต้องการออกจากระบบใช่หรือไม่?")
            warn = warn_font.render(message, True, config.COLOR_TEXT)
            surface.blit(warn, warn.get_rect(center=(config.SCREEN_WIDTH // 2, 220)))
            sub_font = config.get_font(16)
            sub_text = ("ความคืบหน้าจะถูกบันทึกไว้ก่อนปิดเกม" if self.show_confirm == "exit"
                        else "จะกลับไปหน้าแรก (หน้าล็อกอิน) ความคืบหน้าถูกบันทึกไว้แล้ว")
            sub = sub_font.render(sub_text, True, config.COLOR_TEXT_MUTED)
            surface.blit(sub, sub.get_rect(center=(config.SCREEN_WIDTH // 2, 248)))

            self.confirm_yes.draw(surface)
            self.confirm_no.draw(surface)
