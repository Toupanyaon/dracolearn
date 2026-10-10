"""
screens/base.py
----------------
Screen: คลาสตั้งต้นให้ทุกหน้าจอสืบทอด (handle_event / update / draw)
ScreenManager: ถือ "ข้อมูลทุกโปรไฟล์" (self.root) และโปรไฟล์ผู้เล่นที่ active
               อยู่ตอนนี้ (self.player_data) พร้อมจัดการสลับหน้าจอ/สลับผู้เล่น
"""

import pygame

from .. import storage, mascot, wardrobe


class Screen:
    def __init__(self, manager):
        self.manager = manager

    def on_enter(self):
        """เรียกทุกครั้งที่เข้าสู่หน้าจอนี้ - ใช้ setup ค่าเริ่มต้น"""
        pass

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass


class ScreenManager:
    def __init__(self, sounds):
        self.sounds = sounds

        # self.root เก็บข้อมูล "ทุกผู้เล่น" ที่เคยเล่นเกมนี้บนเครื่องนี้ (แยกโปรไฟล์ด้วยชื่อ)
        self.root = storage.load_all()
        self.current_profile_key = self.root.get("last_active")

        if self.current_profile_key and self.current_profile_key in self.root["profiles"]:
            self.player_data = self.root["profiles"][self.current_profile_key]
        else:
            # ยังไม่มีผู้เล่น active คนไหน (เพิ่งเปิดเกมครั้งแรก) - ใช้ค่าเริ่มต้นชั่วคราวไปก่อน
            # จนกว่าผู้เล่นจะกรอกชื่อในหน้า Home แล้วเรียก switch_profile()
            self.current_profile_key = None
            self.player_data = storage.default_profile("")

        self.sounds.set_enabled(self.player_data.get("sound_on", True))
        self.sounds.set_volume(self.player_data.get("volume", 1.0))
        self.sounds.set_speech_volume(self.player_data.get("speech_volume", 1.0))
        self.sounds.set_music_volume(self.player_data.get("music_volume", 0.4))
        self.sounds.set_speech_rate(self.player_data.get("speech_rate", 1.0))

        self.apply_outfit()

        self.screens = {}
        self.current_key = None
        self.current: Screen = None
        self._resume_key = None  # หน้าที่ต้องกลับไป (แบบไม่รีเซ็ตสถานะ) เมื่อปิดหน้าตั้งค่าที่เปิดด้วยปุ่ม Esc
        self.toast = None  # ตั้งค่าจาก main.py (ใช้ widgets.Toast ตัวเดียวใช้ร่วมกันทุกหน้า)

        # ข้อมูลชั่วคราวที่ส่งต่อระหว่างหน้าจอ (เช่น lesson ที่กำลังจะเล่น, ผลสรุปล่าสุด)
        self.context = {}

    def apply_outfit(self):
        """ให้มาสคอตทุกหน้าใส่ชุดของผู้เล่นที่ active อยู่ (เรียกตอนเริ่มเกม/สลับโปรไฟล์/ออกจากระบบ/เปลี่ยนชุด)
        ชุดในไฟล์เซฟที่ผิดปกติหรือใส่ของที่ยังไม่ปลดล็อกอยู่ จะถูกแก้ให้ใช้ได้เสมอ"""
        data = self.player_data
        data["outfit"] = wardrobe.normalize_outfit(data.get("outfit"), data)
        mascot.set_outfit(data["outfit"])

    def switch_profile(self, name: str):
        """สลับไปยังโปรไฟล์ของผู้เล่นชื่อนี้ (คนละชื่อ = คนละคน คนละความก้าวหน้า)
        ถ้าเคยมีชื่อนี้อยู่แล้วจะโหลดของเดิมกลับมาต่อ ถ้าไม่เคยมีจะสร้างโปรไฟล์ใหม่ให้"""
        key, profile = storage.get_or_create_profile(self.root, name)
        self.current_profile_key = key
        self.player_data = profile
        self.sounds.set_enabled(profile.get("sound_on", True))
        self.sounds.set_volume(profile.get("volume", 1.0))
        self.sounds.set_speech_volume(profile.get("speech_volume", 1.0))
        self.sounds.set_music_volume(profile.get("music_volume", 0.4))
        self.sounds.set_speech_rate(profile.get("speech_rate", 1.0))
        self.apply_outfit()
        self.save()
        return profile

    def logout(self):
        """ออกจากระบบ: บันทึกความก้าวหน้าปัจจุบัน แล้วกลับไปหน้าแรก (หน้าล็อกอิน)"""
        self.save()
        self.current_profile_key = None
        self.player_data = storage.default_profile("")
        self.sounds.set_enabled(True)
        self.sounds.set_volume(1.0)
        self.sounds.set_speech_volume(1.0)
        self.sounds.set_music_volume(0.4)
        self.sounds.set_speech_rate(1.0)
        self.apply_outfit()  # หน้าล็อกอินใช้ชุดเริ่มต้น (ไม่เอาชุดของคนที่เพิ่งออกไปมาโชว์)
        self.go_to("home")

    def quit_game(self):
        """ออกจากเกม: บันทึกความก้าวหน้า แล้วส่งสัญญาณปิดโปรแกรมแบบปกติ (main loop จะเซฟซ้ำ/ปิดให้)"""
        self.save()
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def register(self, key, screen: Screen):
        self.screens[key] = screen

    def go_to(self, key, **context):
        self._resume_key = None
        self.context.update(context)
        self.current_key = key
        self.current = self.screens[key]
        self.current.on_enter()

    def open_settings_overlay(self):
        """เปิดหน้าตั้งค่าทับหน้าปัจจุบัน (ใช้กับปุ่ม Esc) โดยจำหน้าเดิมไว้ ปิดแล้วกลับมาต่อจากเดิมเป๊ะ
        (ไม่เรียก on_enter ซ้ำ จึงไม่รีเซ็ตบทเรียนที่กำลังเล่นค้างอยู่)"""
        previous = self.current_key
        self.current_key = "settings"
        self.current = self.screens["settings"]
        self.current.on_enter()
        self._resume_key = previous

    def close_settings(self):
        """ปิดหน้าตั้งค่า: ถ้าเปิดมาจาก Esc ให้กลับหน้าเดิมต่อเลย ไม่งั้นกลับหน้าหลัก (dashboard)"""
        key = self._resume_key
        if key and key in self.screens:
            self._resume_key = None
            self.current_key = key
            self.current = self.screens[key]
            self.save()
        else:
            self.go_to("dashboard")

    def save(self):
        storage.save_all(self.root)

    def handle_event(self, event):
        # Esc = เปิดหน้าตั้งค่าจากทุกหน้า (ยกเว้นหน้าแรกที่ยังไม่ได้เข้าสู่ระบบ ส่วนในหน้าตั้งค่าเอง Esc ใช้ปิด/ย้อนกลับ)
        if (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                and self.current_key not in (None, "home", "settings")):
            self.open_settings_overlay()
            return
        if self.current:
            self.current.handle_event(event)

    def update(self, dt):
        if self.current:
            self.current.update(dt)

    def draw(self, surface):
        if self.current:
            self.current.draw(surface)
