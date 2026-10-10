"""
achievements.py
----------------
ตรวจสอบเงื่อนไขและปลดล็อก Achievement ให้ผู้เล่น
เรียกใช้จากหลายจุด (หลังเรียนจบบท, หลัง login) จึงแยกออกมาไว้ที่เดียว
กัน logic ซ้ำซ้อนกระจายอยู่หลายไฟล์
"""

from typing import List

from . import config, content, wardrobe


def check_achievements(data: dict, perfect_lesson: bool = False) -> List[str]:
    """ตรวจว่ามี Achievement ใดปลดล็อกใหม่บ้าง คืนลิสต์ id ที่เพิ่งปลดล็อกในการเรียกครั้งนี้"""
    unlocked = set(data.get("unlocked_achievements", []))
    newly = []

    level = config.level_from_xp(data.get("total_xp", 0))
    total_lessons = len(content.all_lessons_flat())
    wardrobe_unlocked, wardrobe_total = wardrobe.unlocked_count(data)

    checks = {
        "first_lesson": len(data.get("completed_lessons", [])) >= 1,
        "streak_3": data.get("streak", 0) >= 3,
        "level_5": level >= 5,
        "perfect_lesson": perfect_lesson,
        "five_lessons": data.get("lessons_finished_count", 0) >= 5,
        # --- เพิ่มใหม่ ---
        "all_lessons": len(data.get("completed_lessons", [])) >= total_lessons,
        "streak_7": data.get("streak", 0) >= 7,
        "xp_1000": data.get("total_xp", 0) >= 1000,
        "survival_legend": data.get("survival_best_level", 0) >= content.DIFFICULTY_LEVELS,
        "wardrobe_complete": wardrobe_unlocked >= wardrobe_total,
    }

    for achievement_id, condition_met in checks.items():
        if condition_met and achievement_id not in unlocked:
            unlocked.add(achievement_id)
            newly.append(achievement_id)

    data["unlocked_achievements"] = list(unlocked)
    return newly
