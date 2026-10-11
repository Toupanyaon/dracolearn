"""
config.py
---------
ค่าคงที่ต่าง ๆ ที่ใช้ทั่วทั้งเกม: ขนาดหน้าจอ, สี, ฟอนต์, เส้นทางไฟล์
แยกไว้ที่เดียวเพื่อให้ปรับธีมสี/ขนาดได้ง่ายโดยไม่ต้องไล่แก้หลายไฟล์
"""

import os
import pygame

# ---------------------------------------------------------------------------
# หน้าจอ
# ---------------------------------------------------------------------------
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 640
FPS = 60
GAME_TITLE = "DracoLearn - เรียนอังกฤษกับเบลซมังกรน้อย"

# ---------------------------------------------------------------------------
# โทนสี (ธีมมังกรไฟ: ส้ม / ม่วงเข้ม / ครีม) - ออกแบบใหม่ ไม่ใช้โทนเขียวของ Duolingo
# ---------------------------------------------------------------------------
COLOR_BG = (30, 22, 46)              # ม่วงเข้มเกือบดำ - พื้นหลังหลัก (fallback เดี่ยว)
COLOR_BG_TOP = (88, 204, 2)          # เขียวสด (โทน Duolingo) - สีบนของพื้นหลังไล่เฉด
COLOR_BG_BOTTOM = (70, 163, 2)       # เขียวเข้มขึ้นเล็กน้อย - สีล่างของพื้นหลังไล่เฉด
COLOR_BG_LIGHT = (45, 34, 66)        # ม่วงอ่อนกว่า - การ์ด/พาเนล
COLOR_PRIMARY = (255, 131, 61)       # ส้มมังกร - ปุ่มหลัก/ไฮไลต์
COLOR_PRIMARY_DARK = (214, 100, 40)  # ส้มเข้ม - เงา/กดปุ่ม
COLOR_SECONDARY = (255, 196, 61)     # เหลืองทอง - XP / ดาว
COLOR_ACCENT = (124, 92, 255)        # ม่วงสว่าง - ไฮไลต์รอง
COLOR_SUCCESS = (76, 201, 130)       # เขียว - ตอบถูก
COLOR_DANGER = (235, 87, 87)         # แดง - ตอบผิด / หัวใจ
COLOR_TEXT = (245, 240, 250)         # ตัวอักษรหลัก (บนพื้นเข้ม)
COLOR_TEXT_MUTED = (180, 170, 200)   # ตัวอักษรรอง
COLOR_TEXT_DARK = (62, 46, 84)       # ตัวอักษรเข้ม (ใช้เมื่อวางบนพื้นหลังพาสเทลโดยตรง)
COLOR_TEXT_DARK_MUTED = (108, 92, 130)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_LOCK = (70, 62, 90)            # โหนดบทเรียนที่ยังล็อกอยู่

# ---------------------------------------------------------------------------
# ไฟล์บันทึกความก้าวหน้า (เก็บไว้ข้าง ๆ ตัวสคริปต์)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_FILE = os.path.join(BASE_DIR, "save_data.json")

# ---------------------------------------------------------------------------
# ค่ากลไกเกม (Gamification)
# ---------------------------------------------------------------------------
XP_PER_CORRECT = 10
XP_LESSON_BONUS = 20
START_HEARTS = 3
MAX_HEARTS = 3
PRACTICE_CORRECT_TO_REGEN = 5   # ต้องตอบถูกกี่ข้อในโหมดฝึกฝนฟื้นฟูหัวใจ ถึงจะได้หัวใจคืน
PRACTICE_HEART_REWARD = 1       # ได้หัวใจคืนกี่ดวงต่อการฝึกฝนสำเร็จ 1 รอบ
MIN_PASSWORD_LENGTH = 4       # ความยาวรหัสผ่านขั้นต่ำตอนตั้งรหัสผ่านครั้งแรก/เปลี่ยนรหัสผ่าน

# --- โหมดจับเวลา (Survival): คำถามยากขึ้นเรื่อย ๆ, เวลาหมด = ตาย ---
SURVIVAL_START_SECONDS = 60       # เวลาเริ่มต้น (วินาที)
SURVIVAL_CORRECT_BONUS = 5        # ตอบถูก: เพิ่มเวลา (วินาที)
SURVIVAL_WRONG_PENALTY = 5        # ตอบผิด: ลดเวลา (วินาที)
SURVIVAL_CORRECT_PER_LEVEL = 3    # ตอบถูกทุกกี่ข้อ ถึงจะขึ้นระดับความยากถัดไป
SURVIVAL_PAUSE_ON_FEEDBACK = True # True = หยุดนับเวลาตอนดูเฉลย (ก่อนกด "ข้อถัดไป")

# --- Challenger แบบโหด: คอมโบ / ไอเท็มช่วยชีวิต / บอส ---
SURVIVAL_COMBO_STEP = 3           # ตอบถูกติดกันทุกกี่ข้อ ได้โบนัสเวลาเพิ่ม +1 วินาที
SURVIVAL_COMBO_BONUS_MAX = 5      # โบนัสคอมโบสูงสุด (วินาที) ที่บวกเพิ่มจาก SURVIVAL_CORRECT_BONUS
SURVIVAL_START_LIFELINES = {"fifty": 1, "freeze": 1, "skip": 1}  # ไอเท็มที่มีตอนเริ่มรอบ
SURVIVAL_FREEZE_SECONDS = 8       # ไอเท็มแช่แข็ง: หยุดเวลากี่วินาที
SURVIVAL_BOSS_EVERY = 8           # ตอบข้อปกติครบกี่ข้อ บอสโผล่มา
SURVIVAL_BOSS_QUESTIONS = 3       # บอสมีกี่ด่าน (ต้องถูกติดกันทุกข้อ)
SURVIVAL_BOSS_LEVEL_BOOST = 2     # ข้อบอสยากกว่าระดับปัจจุบันกี่ระดับ (สูงสุดไม่เกินระดับสูงสุด)
SURVIVAL_BOSS_WIN_BONUS = 15      # ชนะบอส: เพิ่มเวลา (วินาที) + ได้ไอเท็มสุ่ม 1 ชิ้น
SURVIVAL_BOSS_FAIL_PENALTY = 10   # แพ้บอส: หักเวลาเพิ่มจากโทษตอบผิดปกติ (วินาที)


def level_from_xp(total_xp: int) -> int:
    """คำนวณ Level จาก XP สะสมทั้งหมด"""
    return total_xp // 100 + 1


def xp_into_current_level(total_xp: int) -> int:
    """XP ที่สะสมมาแล้วภายใน Level ปัจจุบัน (0-99)"""
    return total_xp % 100


def lerp(a: float, b: float, t: float) -> float:
    """ค่าคั่นกลางเชิงเส้นระหว่าง a กับ b ตามสัดส่วน t ใช้ทำแอนิเมชันขยาย/หด (scale) แบบลื่นไหล"""
    return a + (b - a) * t


def lerp_color(c1, c2, t: float):
    """ผสมสีสองสีตามสัดส่วน t (0.0 = c1 ล้วน, 1.0 = c2 ล้วน) ใช้ทำแอนิเมชันสีลื่นไหล"""
    t = max(0.0, min(1.0, t))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


# ---------------------------------------------------------------------------
# ฟอนต์ - โหลดครั้งเดียวหลัง pygame.init() แล้ว cache ไว้
# ---------------------------------------------------------------------------
_font_cache = {}


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _font_cache:
        # ลองใช้ฟอนต์ที่รองรับภาษาไทยก่อน ถ้าไม่มีให้ fallback เป็นฟอนต์ระบบ
        candidates = ["tahoma", "leelawadee", "angsananew", "arial"]
        chosen = None
        available = pygame.font.get_fonts()
        for name in candidates:
            if name.replace(" ", "") in available:
                chosen = name
                break
        from .i18n import TFont  # นำเข้าตอนใช้งาน กัน import วน (i18n -> content)
        _font_cache[key] = TFont(pygame.font.SysFont(chosen, size, bold=bold))  # ห่อให้แปลข้อความตามภาษาเมนู
    return _font_cache[key]
