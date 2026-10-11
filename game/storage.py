"""
storage.py
----------
จัดการบันทึก/โหลดความก้าวหน้า "หลายผู้เล่น" ลงไฟล์ JSON เดียว
ผู้เล่นแต่ละคนแยกกันด้วยชื่อ (ไม่สนตัวพิมพ์เล็ก-ใหญ่) -> คนละ Progress คนละ XP
รองรับการย้ายข้อมูลจากไฟล์เซฟรุ่นเก่า (เดี่ยว/ไม่มีระบบโปรไฟล์) มาเป็นรูปแบบใหม่

ระบบรหัสผ่าน (password):
    แต่ละโปรไฟล์เก็บ "password_salt" (สุ่มต่อคน) และ "password_hash"
    (SHA-256 ของ salt+รหัสผ่าน) แทนที่จะเก็บรหัสผ่านตัวจริงเป็นข้อความล้วน
    โปรไฟล์เก่าที่ยังไม่เคยตั้งรหัสผ่าน (password_hash เป็น None) จะยังเข้าเล่นได้
    โดยไม่ต้องใส่รหัส แต่ถ้าใส่รหัสมาตอนล็อกอินจะถือว่าเป็นการ "ตั้งรหัสผ่านครั้งแรก"
    ให้โปรไฟล์นั้นทันที
"""

import hashlib
import json
import os
import secrets
from datetime import date, timedelta

from . import config, content

XP_HISTORY_DAYS = 60  # เก็บประวัติ XP รายวันย้อนหลังกี่วัน (หน้าสถิติแสดง 7 วัน)


def default_profile(name: str = "ผู้เล่น") -> dict:
    return {
        "name": name,
        "total_xp": 0,
        "hearts": config.START_HEARTS,
        "streak": 0,
        "last_played_date": None,        # ISO date string
        "daily_xp_today": 0,
        "daily_xp_date": None,
        "correct_today": 0,
        "lessons_today": 0,
        "completed_lessons": [],         # list[str] lesson id
        "unlocked_achievements": [],     # list[str] achievement id
        "sound_on": True,
        "volume": 1.0,        # ความดังเสียงเอฟเฟกต์ (ไม่รวมเสียงพูด)
        "speech_volume": 1.0, # ความดังเสียงโจทย์/เสียงพูด TTS (แยกจากเสียงเอฟเฟกต์)
        "music_volume": 0.4,  # ความดังเสียงพื้นหลัง (แยกจากเสียงเอฟเฟกต์)
        "speech_rate": 1.0,   # ตัวคูณความเร็วเสียงพูด (0.5x - 1.5x) ตั้งจากหน้าตั้งค่า
        "read_words_on_tap": True,  # อ่านออกเสียงคำ/ตัวเลือกที่กดในข้อเรียงคำ/เลือกตอบ (ปุ่มเปิด-ปิดในหน้าทำโจทย์)
        "outfit": {"hat": "none", "glasses": "none", "neck": "none", "color": "orange"},  # ชุดมาสคอตที่สวมอยู่ (ดู wardrobe.py)
        "outfit_seen": [],               # list[str] id ของแต่งตัวที่เคยแจ้ง "ปลดล็อกแล้ว" ไปแล้ว (กันแจ้งซ้ำ)
        "wrong_question_ids": [],  # list[str] คลังข้อที่เคยตอบผิด ใช้เป็นคลังโจทย์โหมดฝึกฝนฟื้นฟูหัวใจ
        "lessons_finished_count": 0,
        "xp_history": {},                # dict[ISO date -> XP ที่ได้ในวันนั้น] ใช้วาดกราฟหน้าสถิติ
        "unit_stats": {},                # dict[unit_id -> {"correct": n, "wrong": n}]
        "question_stats": {},            # dict[question_id -> {"c": n, "w": n}] หาหัวข้อที่ผิดบ่อย
        "challenger_runs": 0,            # จำนวนรอบ Challenger ที่เล่นแล้ว
        "challenger_best_combo": 0,      # คอมโบสูงสุดที่เคยทำได้
        "challenger_bosses_beaten": 0,   # จำนวนบอสที่เคยล้ม
        "course": content.DEFAULT_COURSE,  # คอร์สที่เรียนอยู่: "en" เรียนอังกฤษ / "th" เรียนไทย (ดู content.COURSES)
        "survival_best_th": 0,           # int - สถิติ Challenger ของคอร์สภาษาไทย (คอร์สอังกฤษใช้ survival_best เดิม)
        "survival_best_level_th": 0,
        "survival_best": 0,              # int - สถิติโหมด Challenger (จำนวนข้อที่ตอบถูกสูงสุดในหนึ่งรอบ)
        "survival_best_level": 0,        # int - ระดับความยากที่ไปถึงในรอบที่ทำสถิติ (ใช้ตัดสินเมื่อคะแนนเท่ากัน)
        "password_salt": None,           # str|None - สุ่มต่อโปรไฟล์ ใช้คู่กับ password_hash
        "password_hash": None,           # str|None - SHA-256(salt + รหัสผ่าน) ไม่เก็บรหัสผ่านจริง
    }


def _default_root() -> dict:
    return {"profiles": {}, "last_active": None}


def _normalize_key(name: str) -> str:
    return name.strip().lower()


def load_all() -> dict:
    """โหลดข้อมูลผู้เล่นทั้งหมด (ทุกโปรไฟล์) ถ้าไฟล์ไม่มี/เสียหายจะคืนค่าเริ่มต้นแทนการพัง"""
    if not os.path.exists(config.SAVE_FILE):
        return _default_root()

    try:
        with open(config.SAVE_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            raise ValueError("save file is not a JSON object")
    except (json.JSONDecodeError, ValueError, OSError):
        return _default_root()

    # --- ย้ายข้อมูลจากไฟล์เซฟรุ่นเก่า (ยังไม่มีระบบหลายโปรไฟล์) ---
    if "profiles" not in raw:
        legacy_name = raw.get("name", "ผู้เล่น") or "ผู้เล่น"
        key = _normalize_key(legacy_name)
        profile = default_profile(legacy_name)
        for field, value in profile.items():
            profile[field] = raw.get(field, value)
        return {"profiles": {key: profile}, "last_active": key}

    root = _default_root()
    profiles = raw.get("profiles")
    root["profiles"] = profiles if isinstance(profiles, dict) else {}
    root["last_active"] = raw.get("last_active")

    # เติมฟิลด์ที่อาจขาดไปในแต่ละโปรไฟล์ (เผื่อกรณีอัปเดตเกมแล้วมีฟิลด์ใหม่)
    defaults = default_profile()
    for key, profile in list(root["profiles"].items()):
        if not isinstance(profile, dict):
            root["profiles"][key] = default_profile(key)
            continue
        if "speech_volume" not in profile:
            # เซฟเก่า: เสียงพูดเคยผูกกับสไลเดอร์เอฟเฟกต์ ให้สืบทอดค่าเดิมไปก่อน
            profile["speech_volume"] = profile.get("volume", 1.0)
        for field, value in defaults.items():
            profile.setdefault(field, value)
        # หัวใจสูงสุดลดเหลือ config.MAX_HEARTS แล้ว: เซฟเก่าที่มีหัวใจเกินให้ปรับลงมาไม่เกินค่าใหม่
        if isinstance(profile.get("hearts"), int):
            profile["hearts"] = max(0, min(config.MAX_HEARTS, profile["hearts"]))
        _seed_xp_history(profile)
        profile.pop("daily_goal_xp", None)  # ฟิลด์เก่าจากระบบเป้าหมาย XP ต่อวันที่เอาออกแล้ว

    return root


def _seed_xp_history(profile: dict) -> None:
    """เซฟเก่าไม่มีประวัติ XP รายวัน: ใส่ XP ของ 'วันนี้' ที่มีอยู่แล้วลงไปก่อน และกันข้อมูลเสีย"""
    hist = profile.get("xp_history")
    if not isinstance(hist, dict):
        hist = {}
        profile["xp_history"] = hist
    for k in ("unit_stats", "question_stats"):
        if not isinstance(profile.get(k), dict):
            profile[k] = {}
    d, xp = profile.get("daily_xp_date"), profile.get("daily_xp_today", 0)
    if isinstance(d, str) and isinstance(xp, int) and xp > 0 and d not in hist:
        hist[d] = xp
    _prune_xp_history(hist)


def _prune_xp_history(hist: dict) -> None:
    cutoff = (date.today() - timedelta(days=XP_HISTORY_DAYS)).isoformat()
    for k in [k for k in hist if not isinstance(k, str) or k < cutoff]:
        del hist[k]


def save_all(root: dict) -> None:
    try:
        with open(config.SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(root, f, ensure_ascii=False, indent=2)
    except OSError:
        # บันทึกไม่สำเร็จ (เช่น สิทธิ์ไฟล์ไม่พอ) - ไม่ทำให้เกมล่ม แค่เสียความคืบหน้าล่าสุด
        pass


def get_or_create_profile(root: dict, name: str):
    """คืน (key, profile) ของผู้เล่นชื่อนี้ - ถ้ามีอยู่แล้วจะโหลดของเดิม (คนละคนกันด้วยชื่อ)
    ถ้ายังไม่มีจะสร้างโปรไฟล์ใหม่ให้ และตั้งเป็นผู้เล่นล่าสุดที่ active อยู่"""
    key = _normalize_key(name)
    if key not in root["profiles"]:
        root["profiles"][key] = default_profile(name.strip())
    else:
        # อัปเดตชื่อที่แสดงผลให้ตรงกับตัวพิมพ์ล่าสุดที่ผู้เล่นพิมพ์ (เผื่อพิมพ์ตัวใหญ่-เล็กต่างไปนิดหน่อย)
        root["profiles"][key]["name"] = name.strip()
    root["last_active"] = key
    return key, root["profiles"][key]


def find_profile(root: dict, name: str):
    """คืนโปรไฟล์ที่มีอยู่แล้วของชื่อนี้ (dict) โดย 'ไม่สร้างใหม่'
    คืน None ถ้ายังไม่เคยมีชื่อนี้เล่นเกมนี้มาก่อน - ใช้เช็กก่อนตรวจรหัสผ่านตอนล็อกอิน"""
    return root["profiles"].get(_normalize_key(name))


def profile_exists(root: dict, name: str) -> bool:
    """True ถ้าเคยมีผู้เล่นชื่อนี้ (ไม่สนตัวพิมพ์เล็ก-ใหญ่) มาก่อนแล้ว"""
    return find_profile(root, name) is not None


# ---------------------------------------------------------------------------
# ระบบรหัสผ่าน: ไม่เก็บรหัสผ่านจริงลงไฟล์ เก็บแค่ salt + hash (SHA-256)
# ---------------------------------------------------------------------------

def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def has_password(profile: dict) -> bool:
    """True ถ้าโปรไฟล์นี้เคยตั้งรหัสผ่านไว้แล้ว"""
    return bool(profile.get("password_hash"))


def set_password(profile: dict, password: str) -> None:
    """ตั้ง/เปลี่ยนรหัสผ่านของโปรไฟล์นี้ - สุ่ม salt ใหม่ทุกครั้งที่ตั้ง"""
    salt = secrets.token_hex(16)
    profile["password_salt"] = salt
    profile["password_hash"] = _hash_password(password, salt)


def verify_password(profile: dict, password: str) -> bool:
    """ตรวจรหัสผ่าน - ถ้าโปรไฟล์นี้ยังไม่เคยตั้งรหัสผ่านไว้เลย (บัญชีเก่า) ให้ผ่านเสมอ
    เพื่อไม่ให้เซฟเกมเก่าที่ไม่มีรหัสผ่านเข้าเกมไม่ได้"""
    if not has_password(profile):
        return True
    salt = profile.get("password_salt") or ""
    return _hash_password(password, salt) == profile.get("password_hash")


def reset_profile(root: dict, key: str) -> dict:
    """รีเซ็ตความก้าวหน้าเฉพาะโปรไฟล์นี้ (ไม่กระทบผู้เล่นคนอื่นในเครื่องเดียวกัน)"""
    profile = root["profiles"].get(key)
    name = profile.get("name", key) if profile else key
    fresh = default_profile(name)
    if profile is not None:
        profile.clear()
        profile.update(fresh)
    else:
        root["profiles"][key] = fresh
    return root["profiles"][key]


def leaderboard(root: dict, limit: int = 8):
    """คืนลิสต์ (ชื่อ, XP, Streak) ของผู้เล่นทุกคนที่เคยเล่นเกมนี้บนเครื่องนี้ เรียงจาก XP มากไปน้อย"""
    rows = [(p.get("name", "?"), p.get("total_xp", 0), p.get("streak", 0))
            for p in root["profiles"].values()]
    rows.sort(key=lambda r: r[1], reverse=True)
    return rows[:limit]


def survival_fields(course=None):
    """ชื่อฟิลด์สถิติ Challenger (คะแนนสูงสุด, ระดับที่ไปถึง) ของคอร์สนั้น: แต่ละคอร์สแยกสถิติและตารางคะแนนกัน
    คอร์สอังกฤษใช้ชื่อเดิม (เซฟเก่าใช้ต่อได้) คอร์สอื่นต่อท้ายด้วยรหัสคอร์ส"""
    course = course if course in content.COURSES else content.COURSE
    if course == content.DEFAULT_COURSE:
        return "survival_best", "survival_best_level"
    return f"survival_best_{course}", f"survival_best_level_{course}"


def survival_stat(data: dict, course=None):
    """(คะแนนสูงสุด, ระดับที่ไปถึง) ของโปรไฟล์ในคอร์สนั้น (ค่าเสียหายนับเป็น 0)"""
    best_f, level_f = survival_fields(course)
    def num(v):
        return v if isinstance(v, int) and not isinstance(v, bool) and v > 0 else 0
    return num(data.get(best_f)), num(data.get(level_f))


def survival_leaderboard(root: dict, limit: int = 10, course=None):
    """ตารางคะแนนของโหมด Challenger แยกจากตาราง XP: คืนลิสต์ (key, ชื่อ, ตอบถูกสูงสุด, ระดับที่ไปถึง)
    เรียงจากตอบถูกมากไปน้อย ถ้าเท่ากันดูระดับที่ไปถึง แล้วค่อยเรียงตามชื่อ
    คนที่ยังไม่เคยเล่นโหมดนี้ (สถิติ 0) จะไม่อยู่ในตาราง"""
    rows = []
    for key, p in root["profiles"].items():
        best, level = survival_stat(p, course)
        if best > 0:
            rows.append((key, p.get("name", "?"), best, level))
    rows.sort(key=lambda r: (-r[2], -r[3], r[1].lower()))
    return rows[:limit]


def survival_rank(root: dict, key: str, course=None):
    """คืน (อันดับ, จำนวนผู้เล่นในตาราง) ของโปรไฟล์นี้ในตารางโหมด Challenger หรือ None ถ้ายังไม่มีสถิติ"""
    rows = survival_leaderboard(root, limit=len(root["profiles"]), course=course)
    for rank, row in enumerate(rows, start=1):
        if row[0] == key:
            return rank, len(rows)
    return None


def today_str() -> str:
    return date.today().isoformat()


def register_login_for_streak(data: dict) -> bool:
    """เรียกตอนเข้าเกม: อัปเดต Streak ตามวันที่ล่าสุดที่เล่น
    คืนค่า True ถ้า Streak เพิ่มขึ้นในการเรียกครั้งนี้ (ใช้โชว์ toast ฉลอง)"""
    today = today_str()
    last = data.get("last_played_date")

    if last == today:
        return False  # เล่นไปแล้ววันนี้ ไม่ต้องอัปเดตซ้ำ

    if last is None:
        data["streak"] = 1
    else:
        try:
            last_date = date.fromisoformat(last)
            delta_days = (date.today() - last_date).days
        except ValueError:
            delta_days = 999

        if delta_days == 1:
            data["streak"] = data.get("streak", 0) + 1
        else:
            data["streak"] = 1  # ขาดช่วง -> เริ่มนับใหม่

    data["last_played_date"] = today
    # รีเซ็ต XP/เควสรายวันเมื่อขึ้นวันใหม่ และเติมหัวใจให้เต็มในวันใหม่
    if data.get("daily_xp_date") != today:
        data["daily_xp_today"] = 0
        data["correct_today"] = 0
        data["lessons_today"] = 0
        data["daily_xp_date"] = today
        data["hearts"] = config.MAX_HEARTS
    return True


def add_xp(data: dict, amount: int) -> None:
    today = today_str()
    if data.get("daily_xp_date") != today:
        data["daily_xp_today"] = 0
        data["correct_today"] = 0
        data["lessons_today"] = 0
        data["daily_xp_date"] = today
    data["total_xp"] = data.get("total_xp", 0) + amount
    data["daily_xp_today"] = data.get("daily_xp_today", 0) + amount
    hist = data.get("xp_history")
    if not isinstance(hist, dict):
        hist = data["xp_history"] = {}
    hist[today] = hist.get(today, 0) + amount
    _prune_xp_history(hist)


def record_answer(data: dict, question_id: str, correct: bool, unit_id: str = "challenger") -> None:
    """นับสถิติการตอบ: แยกตาม Unit (ความแม่นยำ) และแยกตามข้อ (หัวข้อที่ผิดบ่อย)"""
    us = data.get("unit_stats")
    if not isinstance(us, dict):
        us = data["unit_stats"] = {}
    u = us.setdefault(unit_id, {"correct": 0, "wrong": 0})
    u["correct" if correct else "wrong"] = u.get("correct" if correct else "wrong", 0) + 1
    qs = data.get("question_stats")
    if not isinstance(qs, dict):
        qs = data["question_stats"] = {}
    q = qs.setdefault(question_id, {"c": 0, "w": 0})
    q["c" if correct else "w"] = q.get("c" if correct else "w", 0) + 1


# ---------------------------------------------------------------------------
# โหมดทบทวนฝึกฝนเพื่อฟื้นฟูหัวใจ (Practice / Heart Regeneration Mode):
# เมื่อหัวใจหมด แทนที่จะล็อกผู้เล่นไว้เฉย ๆ ให้ไปฝึกทบทวน "คำถามที่เคยตอบผิด" แทน
# ตอบถูกครบตามจำนวนที่กำหนด (config.PRACTICE_CORRECT_TO_REGEN) จะได้หัวใจคืน
# ---------------------------------------------------------------------------

def record_wrong_question(data: dict, question_id: str) -> None:
    """บันทึกว่าเคยตอบข้อนี้ผิด (เก็บแบบไม่ซ้ำ) ใช้เป็นคลังโจทย์สำหรับโหมดฝึกฝนฟื้นฟูหัวใจ"""
    wrong = data.setdefault("wrong_question_ids", [])
    if question_id not in wrong:
        wrong.append(question_id)


def remove_wrong_question(data: dict, question_id: str) -> None:
    """เอาข้อนี้ออกจากคลังทบทวน เมื่อผู้เล่นตอบถูกแล้ว (ถือว่าแก้ตัวสำเร็จ)
    ถ้าตอบผิดข้อนี้อีกในอนาคตจะถูกเพิ่มกลับเข้าคลังใหม่โดยอัตโนมัติ"""
    wrong = data.get("wrong_question_ids")
    if wrong and question_id in wrong:
        wrong.remove(question_id)


def regen_heart(data: dict, amount: int = 1) -> int:
    """คืนหัวใจให้ผู้เล่น (ไม่เกิน config.MAX_HEARTS) คืนค่าจำนวนหัวใจปัจจุบันหลังคืนแล้ว"""
    data["hearts"] = min(config.MAX_HEARTS, data.get("hearts", 0) + amount)
    return data["hearts"]
