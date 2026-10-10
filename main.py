"""
main.py
-------
จุดเริ่มต้นของเกม DracoLearn
ติดตั้งและรัน:
    pip install -r requirements.txt
    python main.py

หมายเหตุ: ต้องติดตั้ง pyttsx3 ด้วย (อยู่ใน requirements.txt แล้ว) ไม่งั้นเสียงพูด (TTS)
จะไม่ทำงานเลย - คำสั่งเก่า "pip install pygame numpy" ที่เคยเขียนไว้ตรงนี้ไม่มี pyttsx3
จึงเป็นสาเหตุที่พบบ่อยที่สุดที่ทำให้ "ฟังเสียง"/"ฟังโจทย์" ไม่พูดอะไรเลย
บน Windows ถ้ายังไม่พูดอีก ให้รัน `python test_tts.py` เพื่อดูสาเหตุที่แท้จริง
"""

import sys

import pygame

from game import config
from game.display import ScaledDisplay
from game.sounds import SoundManager
from game.widgets import Toast
from game.screens.base import ScreenManager
from game.screens.home import HomeScreen
from game.screens.dashboard import DashboardScreen
from game.screens.path import PathScreen
from game.screens.lesson import LessonScreen
from game.screens.survival import SurvivalScreen
from game.screens.challenger_board import ChallengerBoardScreen
from game.screens.summary import SummaryScreen
from game.screens.profile import ProfileScreen
from game.screens.settings_screen import SettingsScreen
from game.screens.wardrobe import WardrobeScreen
from game.screens.stats import StatsScreen


def main():
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=256)
    pygame.init()

    # หน้าต่างปรับขนาดตามหน้าจอ: เกมวาดลงผืนผ้าใบ 900x640 แล้วขยายให้พอดีหน้าต่าง (ดู game/display.py)
    display = ScaledDisplay(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, config.GAME_TITLE,
                            letterbox_color=config.COLOR_BG_BOTTOM)
    screen = display.canvas
    clock = pygame.time.Clock()

    sounds = SoundManager()
    manager = ScreenManager(sounds)
    manager.toast = Toast()

    manager.register("home", HomeScreen(manager))
    manager.register("dashboard", DashboardScreen(manager))
    manager.register("path", PathScreen(manager))
    manager.register("lesson", LessonScreen(manager))
    manager.register("survival", SurvivalScreen(manager))
    manager.register("challenger_board", ChallengerBoardScreen(manager))
    manager.register("summary", SummaryScreen(manager))
    manager.register("profile", ProfileScreen(manager))
    manager.register("settings", SettingsScreen(manager))
    manager.register("wardrobe", WardrobeScreen(manager))
    manager.register("stats", StatsScreen(manager))

    sounds.start_music()
    manager.go_to("home")

    running = True
    while running:
        dt = clock.tick(config.FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif display.handle_system_event(event):
                continue  # ย่อ/ขยายหน้าต่าง หรือ F11 เต็มจอ - จัดการเสร็จแล้ว
            else:
                manager.handle_event(display.translate_event(event))  # แปลงพิกัดเมาส์เป็นพิกัดเกม

        manager.update(dt)
        manager.toast.update(dt)

        manager.draw(screen)
        manager.toast.draw(screen)

        display.present()

    manager.save()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
