"""
stats.py
--------
ตรรกะล้วน ๆ (ไม่แตะ pygame) ของหน้าสถิติ: XP 7 วัน / ความแม่นยำแยกตาม Unit / หัวข้อที่ผิดบ่อย
อ่านจากโปรไฟล์ผู้เล่น (dict) และทนต่อข้อมูลเซฟที่เสียหาย
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional

from . import content

WEEKDAYS_TH = ["จ.", "อ.", "พ.", "พฤ.", "ศ.", "ส.", "อา."]
_AXIS_STEPS = [10, 20, 30, 50, 80, 100, 150, 200, 300, 500, 800, 1000]


def _count(v) -> int:
    return v if isinstance(v, int) and not isinstance(v, bool) and v > 0 else 0


def _dict(v) -> dict:
    return v if isinstance(v, dict) else {}


@dataclass
class DayXP:
    day: date
    xp: int
    label: str
    is_today: bool


def xp_last_days(data: dict, days: int = 7, today: Optional[date] = None) -> List[DayXP]:
    """XP รายวันย้อนหลัง `days` วัน เรียงเก่า -> ใหม่ (วันสุดท้ายคือวันนี้)"""
    today = today or date.today()
    hist = _dict(data.get("xp_history"))
    out = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        out.append(DayXP(d, _count(hist.get(d.isoformat())), WEEKDAYS_TH[d.weekday()], i == 0))
    return out


def nice_axis_max(peak: int) -> int:
    """ค่าสูงสุดของแกน Y ที่ 'กลม ๆ' และไม่ต่ำกว่า peak"""
    peak = max(0, peak)
    for step in _AXIS_STEPS:
        if peak <= step:
            return step
    return ((peak + 499) // 500) * 500


def xp_summary(data: dict, days: int = 7, today: Optional[date] = None) -> dict:
    series = xp_last_days(data, days, today)
    total = sum(d.xp for d in series)
    active = sum(1 for d in series if d.xp > 0)
    best = max(series, key=lambda d: d.xp)
    return {"total": total, "average": round(total / len(series)) if series else 0,
            "active_days": active, "best_xp": best.xp, "best_day": best.day if best.xp else None}


@dataclass
class UnitAccuracy:
    unit_id: str
    title: str
    correct: int
    wrong: int

    @property
    def total(self) -> int:
        return self.correct + self.wrong

    @property
    def percent(self) -> Optional[int]:
        return None if self.total == 0 else round(100 * self.correct / self.total)


def unit_accuracy(data: dict) -> List[UnitAccuracy]:
    """แถวของ Unit 1..5 ตามลำดับ + แถว Challenger ท้ายสุด"""
    us = _dict(data.get("unit_stats"))
    rows = []
    for u in content.UNITS:
        st = _dict(us.get(u.id))
        rows.append(UnitAccuracy(u.id, u.title, _count(st.get("correct")), _count(st.get("wrong"))))
    st = _dict(us.get("challenger"))
    rows.append(UnitAccuracy("challenger", "Challenger", _count(st.get("correct")), _count(st.get("wrong"))))
    return rows


def overall_accuracy(data: dict) -> Optional[int]:
    rows = unit_accuracy(data)
    c = sum(r.correct for r in rows)
    t = sum(r.total for r in rows)
    return None if t == 0 else round(100 * c / t)


def accuracy_level(percent: Optional[int]) -> str:
    if percent is None:
        return "none"
    return "good" if percent >= 80 else "ok" if percent >= 60 else "bad"


@dataclass
class Topic:
    qid: str
    title: str      # ชื่อหัวข้อที่โชว์ (vocab หรือชื่อบทเรียน)
    where: str      # Unit / บทเรียน
    wrong: int
    total: int

    @property
    def percent_wrong(self) -> int:
        return round(100 * self.wrong / self.total) if self.total else 0


def topic_of_question(qid: str) -> Optional[Topic]:
    q = content.QUESTION_MAP.get(qid)
    if q is None:
        return None
    home = content.QUESTION_HOME.get(qid)
    where = f"{home[0].title} · {home[1].title}" if home else "Challenger"
    title = q.vocab or q.correct_answer or q.prompt
    return Topic(qid, title, where, 0, 0)


def wrong_topics(data: dict, limit: int = 5) -> List[Topic]:
    """ข้อที่ตอบผิดบ่อยสุด (ผิด >= 1) เรียงจากผิดมาก -> น้อย; เท่ากันดูสัดส่วนผิด แล้วค่อยรหัสข้อ"""
    qs = _dict(data.get("question_stats"))
    out = []
    for qid, st in qs.items():
        st = _dict(st)
        w, c = _count(st.get("w")), _count(st.get("c"))
        if w == 0:
            continue
        t = topic_of_question(qid)
        if t is None:
            continue
        t.wrong, t.total = w, w + c
        out.append(t)
    out.sort(key=lambda t: (-t.wrong, -t.percent_wrong, t.qid))
    return out[:limit]
