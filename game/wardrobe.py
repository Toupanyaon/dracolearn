"""
wardrobe.py
-----------
ระบบแต่งตัวมาสคอต "เบลซ": แคตตาล็อกของแต่งตัว + เงื่อนไขปลดล็อก + ตัวช่วยจัดการชุดที่สวมอยู่
ไฟล์นี้ไม่พึ่ง pygame (ทดสอบง่าย) ส่วนการ "วาด" ของแต่ละชิ้นอยู่ใน mascot.py (ใช้ id เดียวกัน)

ช่องแต่งตัว (slot) มี 4 ช่อง:
    hat      หมวก
    glasses  แว่นตา
    neck     เครื่องประดับคอ/ตัว (โบว์ ผ้าพันคอ เหรียญ ผ้าคลุม)
    color    สีตัวมังกร (ต้องมีเสมอ 1 สี - ค่าเริ่มต้น "ส้มไฟ")

เงื่อนไขปลดล็อกคำนวณจากความก้าวหน้าของผู้เล่น "ทุกครั้งที่ถาม" (ไม่เก็บสถานะปลดล็อกลงไฟล์เซฟ)
และใช้เฉพาะข้อมูลที่ไม่ลดลงเอง (เลเวล, จำนวนบทที่เรียนจบ, achievement, สถิติระดับ Challenger สูงสุด)
ของที่ปลดล็อกแล้วจึงไม่ถูกล็อกกลับ ในไฟล์เซฟเก็บแค่ "ชุดที่สวมอยู่" (outfit) กับ "ชิ้นที่เคยแจ้งปลดล็อกแล้ว" (outfit_seen)

วิธีเพิ่มของแต่งตัวใหม่: เพิ่ม Item ใน ITEMS ที่นี่ + เพิ่มฟังก์ชันวาดของ id เดียวกันใน mascot.py
(test_wardrobe.py เช็กว่าทุก id มีฟังก์ชันวาดครบ)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from . import config, content

SLOTS = ["hat", "glasses", "neck", "color"]
SLOT_NAMES = {"hat": "หมวก", "glasses": "แว่นตา", "neck": "เครื่องประดับ", "color": "สีตัว"}
NONE_ID = "none"   # ไม่สวมอะไรในช่องนั้น (ใช้ได้ทุกช่องยกเว้น color)

DEFAULT_OUTFIT = {"hat": NONE_ID, "glasses": NONE_ID, "neck": NONE_ID, "color": "orange"}


@dataclass(frozen=True)
class Item:
    id: str
    slot: str
    name: str                 # ชื่อภาษาไทยที่แสดงบนการ์ด
    condition: Tuple = ("free",)  # ("free",) | ("level", n) | ("lessons", n) | ("achievement", id) | ("survival_level", n)


ITEMS: List[Item] = [
    # ---- หมวก ----
    Item("party", "hat", "หมวกปาร์ตี้"),
    Item("cap", "hat", "หมวกแก๊ป", ("lessons", 1)),
    Item("chef", "hat", "หมวกเชฟ", ("level", 3)),
    Item("wizard", "hat", "หมวกพ่อมด", ("achievement", "five_lessons")),
    Item("pirate", "hat", "หมวกโจรสลัด", ("survival_level", 4)),
    Item("crown", "hat", "มงกุฎราชา", ("level", 8)),
    Item("horns", "hat", "เขาปีศาจ", ("survival_level", 7)),
    Item("flame", "hat", "มงกุฎเพลิง", ("survival_level", 10)),
    # ---- แว่นตา ----
    Item("round", "glasses", "แว่นกลม", ("level", 2)),
    Item("sunglasses", "glasses", "แว่นกันแดด", ("achievement", "streak_3")),
    Item("goggles", "glasses", "โกเกิลนักรบ", ("survival_level", 5)),
    Item("star", "glasses", "แว่นดาว", ("level", 6)),
    # ---- เครื่องประดับ ----
    Item("bowtie", "neck", "โบว์ไท"),
    Item("scarf", "neck", "ผ้าพันคอ", ("lessons", 3)),
    Item("medal", "neck", "เหรียญเกียรติยศ", ("achievement", "perfect_lesson")),
    Item("cape", "neck", "ผ้าคลุมฮีโร่", ("survival_level", 6)),
    # ---- สีตัว ----
    Item("orange", "color", "ส้มไฟ"),
    Item("blue", "color", "ฟ้าน้ำแข็ง", ("level", 4)),
    Item("mint", "color", "เขียวมิ้นต์", ("level", 6)),
    Item("pink", "color", "ชมพูบลอสซัม", ("lessons", 8)),
    Item("purple", "color", "ม่วงราตรี", ("survival_level", 8)),
    Item("gold", "color", "ทองคำ", ("survival_level", 10)),
]
ITEM_MAP: Dict[str, Item] = {i.id: i for i in ITEMS}


def items_in_slot(slot: str) -> List[Item]:
    return [i for i in ITEMS if i.slot == slot]


def _progress_value(kind: str, data: dict):
    if kind == "level":
        return config.level_from_xp(data.get("total_xp", 0))
    if kind == "lessons":
        return len(set(data.get("completed_lessons", [])))
    if kind == "survival_level":
        from . import storage  # นำเข้าตอนใช้งาน: ระดับสูงสุดที่เคยไปถึงในคอร์สไหนก็ได้
        return max(storage.survival_stat(data, c)[1] for c in content.COURSES)
    return 0


def is_unlocked(item: Item, data: dict) -> bool:
    kind = item.condition[0]
    if kind == "free":
        return True
    if kind == "achievement":
        return item.condition[1] in data.get("unlocked_achievements", [])
    return _progress_value(kind, data) >= item.condition[1]


def requirement_text(item: Item) -> str:
    """ข้อความบอกเงื่อนไขปลดล็อก (แสดงบนการ์ดที่ยังล็อกอยู่ / ตอนกดของที่ล็อก)"""
    kind = item.condition[0]
    if kind == "free":
        return "ใส่ได้เลย"
    if kind == "level":
        return f"ถึงเลเวล {item.condition[1]}"
    if kind == "lessons":
        return f"เรียนจบ {item.condition[1]} บท"
    if kind == "achievement":
        ach = content.ACHIEVEMENT_MAP.get(item.condition[1])
        return f"ได้ความสำเร็จ \"{ach.title}\"" if ach else "ปลดล็อกความสำเร็จ"
    if kind == "survival_level":
        n = item.condition[1]
        return f"Challenger ถึงระดับ {n} ({content.level_name(n)})"
    return ""


def unlocked_ids(data: dict) -> List[str]:
    return [i.id for i in ITEMS if is_unlocked(i, data)]


def unlocked_count(data: dict) -> Tuple[int, int]:
    """(ชิ้นที่ปลดล็อกแล้ว, ชิ้นทั้งหมด) นับเฉพาะของจริง ไม่นับ 'ไม่สวม'"""
    return len(unlocked_ids(data)), len(ITEMS)


# ---------------------------------------------------------------------------
# ชุดที่สวมอยู่ (data["outfit"])
# ---------------------------------------------------------------------------

def normalize_outfit(outfit, data: Optional[dict] = None) -> dict:
    """คืนชุดที่ใช้ได้จริงเสมอ: ช่องที่ไม่มี/id แปลก/(ถ้าส่ง data มา) ของที่ยังไม่ปลดล็อก -> กลับเป็นค่าเริ่มต้นของช่องนั้น
    ใช้กับไฟล์เซฟเก่า/ไฟล์ที่ถูกแก้มือ/โปรไฟล์ที่เพิ่งรีเซ็ต ไม่ให้เกมพังหรือใส่ของที่ยังไม่ได้ปลดล็อก"""
    result = dict(DEFAULT_OUTFIT)
    if not isinstance(outfit, dict):
        return result
    for slot in SLOTS:
        item_id = outfit.get(slot)
        if item_id == NONE_ID and slot != "color":
            result[slot] = NONE_ID
            continue
        item = ITEM_MAP.get(item_id) if isinstance(item_id, str) else None
        if item is None or item.slot != slot:
            continue
        if data is not None and not is_unlocked(item, data):
            continue
        result[slot] = item.id
    return result


def equip(data: dict, item_id: str) -> bool:
    """สวมของลงโปรไฟล์ (ต้องปลดล็อกแล้วเท่านั้น) คืน True ถ้าสวมสำเร็จ
    item_id เป็น "<slot>:none" เพื่อถอดช่องนั้น (เช่น "hat:none") ใช้ไม่ได้กับ color"""
    outfit = normalize_outfit(data.get("outfit"), data)
    if ":" in item_id:
        slot, _, ident = item_id.partition(":")
        if ident != NONE_ID or slot not in SLOTS or slot == "color":
            return False
        outfit[slot] = NONE_ID
        data["outfit"] = outfit
        return True
    item = ITEM_MAP.get(item_id)
    if item is None or not is_unlocked(item, data):
        return False
    outfit[item.slot] = item.id
    data["outfit"] = outfit
    return True


def undress(data: dict) -> None:
    """ถอดหมวก/แว่น/เครื่องประดับทั้งหมด (สีตัวไม่เปลี่ยน)"""
    outfit = normalize_outfit(data.get("outfit"), data)
    for slot in ("hat", "glasses", "neck"):
        outfit[slot] = NONE_ID
    data["outfit"] = outfit


def newly_unlocked(data: dict) -> List[Item]:
    """ของที่ปลดล็อกแล้วแต่ยังไม่เคยแจ้งผู้เล่น (ไม่นับของที่ใส่ได้ตั้งแต่แรก) และอัปเดต outfit_seen ให้ทันที"""
    seen = set(data.get("outfit_seen", []))
    fresh = [i for i in ITEMS if i.condition[0] != "free" and is_unlocked(i, data) and i.id not in seen]
    if fresh:
        data["outfit_seen"] = sorted(seen | {i.id for i in fresh})
    return fresh
