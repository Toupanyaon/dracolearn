"""
mascot.py
---------
วาดมาสคอตมังกรน้อย "เบลซ (Blaze)" ด้วยรูปทรงเรขาคณิตของ pygame ล้วน ๆ
ไม่ใช้ภาพจากภายนอก และไม่อ้างอิงหน้าตานกฮูกของ Duolingo แต่อย่างใด
รองรับหลายอารมณ์ (mood) เพื่อสื่อ feedback ในแต่ละหน้าจอ
"""

import math
import pygame

from . import config

BODY_COLOR = (255, 140, 66)
BODY_SHADE = (214, 100, 40)
BELLY_COLOR = (255, 214, 158)
SPIKE_COLOR = (124, 92, 255)
EYE_WHITE = (255, 255, 255)
EYE_BLACK = (40, 30, 30)


# สีตัวมังกรแต่ละแบบ (ตรงกับ id ของช่อง color ใน wardrobe.py): (ตัว, เงา, ท้อง/ปาก, หนาม)
PALETTES = {
    "orange": (BODY_COLOR, BODY_SHADE, BELLY_COLOR, SPIKE_COLOR),
    "blue": ((96, 170, 255), (58, 120, 214), (214, 236, 255), (255, 160, 70)),
    "mint": ((96, 214, 160), (52, 164, 116), (220, 252, 236), (255, 120, 150)),
    "pink": ((255, 138, 190), (214, 90, 142), (255, 224, 238), (110, 90, 220)),
    "purple": ((150, 110, 230), (106, 70, 186), (228, 214, 250), (255, 200, 80)),
    "gold": ((255, 200, 60), (206, 150, 20), (255, 240, 190), (255, 120, 60)),
}

# ชุดที่สวมอยู่ตอนนี้ (ScreenManager ตั้งให้ตามโปรไฟล์ผู้เล่นที่ active) ทุกหน้าที่วาดมาสคอตจึงใส่ชุดเดียวกันอัตโนมัติ
_current_outfit = {"hat": "none", "glasses": "none", "neck": "none", "color": "orange"}


def set_outfit(outfit):
    """ตั้งชุดที่มาสคอตจะใส่ในทุกหน้า (dict ช่อง -> id) ค่าที่ผิดปกติจะถูกแก้ให้ใช้ได้เสมอ"""
    global _current_outfit
    from . import wardrobe  # import ตอนเรียกเพื่อเลี่ยง import วน (wardrobe -> content)
    _current_outfit = wardrobe.normalize_outfit(outfit)


def get_outfit():
    return dict(_current_outfit)


def _pt(x, y):
    return (int(round(x)), int(round(y)))


def _lw(hr, k=0.07, lo=2):
    """ความหนาเส้นที่สเกลตามขนาดหัว"""
    return max(lo, int(hr * k))


def _star_points(cx, cy, r, inner=0.45, rot=-math.pi / 2):
    pts = []
    for i in range(10):
        ang = rot + i * math.pi / 5
        rad = r if i % 2 == 0 else r * inner
        pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad))
    return pts


def _dome(cx, base_y, a, b, steps=18):
    """จุดของครึ่งวงรีด้านบน (ใช้ทำโดมหมวก) กว้างครึ่งละ a สูง b"""
    pts = [(cx - a, base_y)]
    for i in range(1, steps):
        th = math.pi - i * math.pi / steps
        pts.append((cx + a * math.cos(th), base_y - b * math.sin(th)))
    pts.append((cx + a, base_y))
    return pts


# ---------------------------------------------------------------------------
# ของแต่งตัว: ทุกฟังก์ชันรับ (surface, cx, cy, hr, t) โดย (cx, cy) = กึ่งกลางหัว, hr = รัศมีหัว
# ---------------------------------------------------------------------------

def _hat_party(surface, cx, cy, hr, t):
    yb = cy - hr * 0.78
    tip = (cx + hr * 0.08, yb - hr * 0.95)
    pygame.draw.polygon(surface, (255, 90, 150), [(cx - hr * 0.42, yb), (cx + hr * 0.42, yb), tip])
    for k, (fx_, fy_) in enumerate(((-0.12, 0.28), (0.12, 0.5), (-0.02, 0.72))):
        pygame.draw.circle(surface, (255, 230, 90), _pt(cx + hr * fx_ + hr * 0.04, yb - hr * fy_), max(2, int(hr * 0.06)))
    pygame.draw.circle(surface, (255, 230, 90), _pt(*tip), max(3, int(hr * 0.11)))


def _hat_cap(surface, cx, cy, hr, t):
    yb = cy - hr * 0.66
    pygame.draw.polygon(surface, (50, 110, 220), _dome(cx, yb, hr * 0.74, hr * 0.62))
    pygame.draw.ellipse(surface, (30, 75, 170), pygame.Rect(int(cx - hr * 0.12), int(yb - hr * 0.08), int(hr * 1.1), int(hr * 0.22)))
    pygame.draw.circle(surface, (255, 220, 80), _pt(cx, yb - hr * 0.62), max(2, int(hr * 0.07)))


def _hat_chef(surface, cx, cy, hr, t):
    yb = cy - hr * 0.78
    puffs = [(cx - hr * 0.42, yb - hr * 0.42, hr * 0.38), (cx + hr * 0.42, yb - hr * 0.42, hr * 0.38),
             (cx, yb - hr * 0.62, hr * 0.42)]
    for x, y, r in puffs:
        pygame.draw.circle(surface, (205, 205, 220), _pt(x, y), int(r + 2))
    for x, y, r in puffs:
        pygame.draw.circle(surface, (255, 255, 255), _pt(x, y), int(r))
    band = pygame.Rect(int(cx - hr * 0.56), int(yb - hr * 0.2), int(hr * 1.12), int(hr * 0.26))
    pygame.draw.rect(surface, (205, 205, 220), band.inflate(4, 4), border_radius=4)
    pygame.draw.rect(surface, (255, 255, 255), band, border_radius=4)


def _hat_wizard(surface, cx, cy, hr, t):
    yb = cy - hr * 0.7
    pygame.draw.polygon(surface, (90, 60, 190), [(cx - hr * 0.5, yb), (cx + hr * 0.5, yb), (cx + hr * 0.2, yb - hr * 0.95)])
    pygame.draw.polygon(surface, (90, 60, 190), [(cx + hr * 0.2, yb - hr * 0.95), (cx + hr * 0.42, yb - hr * 0.82), (cx + hr * 0.3, yb - hr * 0.7)])
    pygame.draw.rect(surface, (255, 210, 70), pygame.Rect(int(cx - hr * 0.5), int(yb - hr * 0.16), int(hr * 1.0), int(hr * 0.14)))
    pygame.draw.ellipse(surface, (60, 38, 150), pygame.Rect(int(cx - hr * 0.92), int(yb - hr * 0.1), int(hr * 1.84), int(hr * 0.3)))
    pygame.draw.polygon(surface, (255, 230, 90), _star_points(cx - hr * 0.08, yb - hr * 0.5, hr * 0.13))
    pygame.draw.polygon(surface, (255, 230, 90), _star_points(cx + hr * 0.14, yb - hr * 0.72, hr * 0.08))


def _hat_pirate(surface, cx, cy, hr, t):
    yb = cy - hr * 0.62
    pygame.draw.polygon(surface, (35, 30, 40), [(cx - hr * 0.95, yb + hr * 0.08), (cx - hr * 0.55, yb - hr * 0.5),
                                                  (cx, yb - hr * 0.72), (cx + hr * 0.55, yb - hr * 0.5),
                                                  (cx + hr * 0.95, yb + hr * 0.08), (cx, yb - hr * 0.1)])
    pygame.draw.rect(surface, (255, 220, 80), pygame.Rect(int(cx - hr * 0.62), int(yb - hr * 0.24), int(hr * 1.24), max(2, int(hr * 0.06))))
    sk = _pt(cx, yb - hr * 0.42)
    pygame.draw.circle(surface, (245, 245, 245), sk, max(3, int(hr * 0.13)))
    for sx in (-1, 1):
        pygame.draw.circle(surface, (35, 30, 40), _pt(cx + sx * hr * 0.05, yb - hr * 0.44), max(1, int(hr * 0.03)))


def _hat_crown(surface, cx, cy, hr, t):
    yb = cy - hr * 0.74
    w, h = hr * 0.62, hr * 0.62
    pts = [(cx - w, yb), (cx - w, yb - h * 0.8), (cx - w * 0.5, yb - h * 0.35), (cx, yb - h),
           (cx + w * 0.5, yb - h * 0.35), (cx + w, yb - h * 0.8), (cx + w, yb)]
    pygame.draw.polygon(surface, (255, 200, 40), pts)
    pygame.draw.rect(surface, (230, 160, 20), pygame.Rect(int(cx - w), int(yb - hr * 0.1), int(w * 2), int(hr * 0.1)))
    for gx, col in ((-w * 0.5, (230, 60, 80)), (0, (70, 140, 255)), (w * 0.5, (230, 60, 80))):
        pygame.draw.circle(surface, col, _pt(cx + gx, yb - hr * 0.2), max(2, int(hr * 0.06)))


def _hat_horns(surface, cx, cy, hr, t):
    for side in (-1, 1):
        base_x = cx + side * hr * 0.5
        base_y = cy - hr * 0.78
        pts = [(base_x - hr * 0.14, base_y + hr * 0.1), (base_x + hr * 0.14, base_y + hr * 0.1),
               (base_x + side * hr * 0.42, base_y - hr * 0.55)]
        pygame.draw.polygon(surface, (200, 30, 50), pts)
        pygame.draw.polygon(surface, (140, 15, 35), [(base_x, base_y + hr * 0.1), (base_x + hr * 0.14, base_y + hr * 0.1),
                                                      (base_x + side * hr * 0.42, base_y - hr * 0.55)])


def _hat_flame(surface, cx, cy, hr, t):
    yb = cy - hr * 0.8
    for i, dx in enumerate((-0.5, -0.25, 0.0, 0.25, 0.5)):
        flick = math.sin(t * 7 + i * 1.7) * hr * 0.06
        height = hr * (0.55 if i % 2 else 0.75) + flick
        x = cx + dx * hr
        w = hr * 0.14
        pygame.draw.polygon(surface, (255, 90, 40), [(x - w, yb + hr * 0.04), (x + w, yb + hr * 0.04), (x, yb - height)])
        pygame.draw.polygon(surface, (255, 215, 80), [(x - w * 0.5, yb + hr * 0.04), (x + w * 0.5, yb + hr * 0.04), (x, yb - height * 0.62)])
    pygame.draw.rect(surface, (255, 200, 40), pygame.Rect(int(cx - hr * 0.6), int(yb), int(hr * 1.2), max(3, int(hr * 0.1))), border_radius=3)


def _eye_centers(cx, cy, hr):
    dx, dy = hr * 0.38, -hr * 0.05
    return (cx - dx, cy + dy), (cx + dx, cy + dy)


def _glasses_round(surface, cx, cy, hr, t):
    (lx, ly), (rx, ry) = _eye_centers(cx, cy, hr)
    w = _lw(hr)
    for ex, ey in ((lx, ly), (rx, ry)):
        pygame.draw.circle(surface, (60, 45, 40), _pt(ex, ey), int(hr * 0.3), w)
    pygame.draw.line(surface, (60, 45, 40), _pt(lx + hr * 0.3, ly), _pt(rx - hr * 0.3, ry), w)
    pygame.draw.line(surface, (60, 45, 40), _pt(lx - hr * 0.3, ly), _pt(lx - hr * 0.62, ly - hr * 0.05), w)
    pygame.draw.line(surface, (60, 45, 40), _pt(rx + hr * 0.3, ry), _pt(rx + hr * 0.62, ry - hr * 0.05), w)


def _glasses_sunglasses(surface, cx, cy, hr, t):
    (lx, ly), (rx, ry) = _eye_centers(cx, cy, hr)
    w = _lw(hr)
    pygame.draw.line(surface, (25, 25, 35), _pt(lx, ly), _pt(rx, ry), w)
    for ex, ey in ((lx, ly), (rx, ry)):
        rect = pygame.Rect(0, 0, int(hr * 0.68), int(hr * 0.5))
        rect.center = _pt(ex, ey)
        pygame.draw.ellipse(surface, (25, 25, 35), rect)
        pygame.draw.line(surface, (255, 255, 255), _pt(ex - hr * 0.16, ey - hr * 0.1), _pt(ex - hr * 0.04, ey - hr * 0.16), max(1, w - 1))


def _glasses_goggles(surface, cx, cy, hr, t):
    (lx, ly), (rx, ry) = _eye_centers(cx, cy, hr)
    w = _lw(hr, 0.08, 3)
    pygame.draw.line(surface, (70, 70, 90), _pt(cx - hr * 0.98, ly), _pt(cx + hr * 0.98, ry), w)
    for ex, ey in ((lx, ly), (rx, ry)):
        pygame.draw.circle(surface, (130, 205, 255), _pt(ex, ey), int(hr * 0.3))
        pygame.draw.circle(surface, (200, 200, 215), _pt(ex, ey), int(hr * 0.3), w)
        pygame.draw.circle(surface, (255, 255, 255), _pt(ex - hr * 0.09, ey - hr * 0.09), max(1, int(hr * 0.06)))


def _glasses_star(surface, cx, cy, hr, t):
    (lx, ly), (rx, ry) = _eye_centers(cx, cy, hr)
    w = _lw(hr, 0.05, 1)
    pygame.draw.line(surface, (200, 120, 30), _pt(lx, ly), _pt(rx, ry), w + 1)
    for ex, ey in ((lx, ly), (rx, ry)):
        pts = _star_points(ex, ey, hr * 0.4, 0.5)
        pygame.draw.polygon(surface, (255, 220, 80), pts)
        pygame.draw.polygon(surface, (220, 130, 30), pts, w)


def _neck_bowtie(surface, cx, cy, hr, t):
    y = cy + hr * 0.98
    for side in (-1, 1):
        pygame.draw.polygon(surface, (225, 50, 80), [(cx, y), (cx + side * hr * 0.5, y - hr * 0.2), (cx + side * hr * 0.5, y + hr * 0.2)])
    pygame.draw.circle(surface, (170, 25, 55), _pt(cx, y), max(3, int(hr * 0.1)))


def _neck_scarf(surface, cx, cy, hr, t):
    y = cy + hr * 0.95
    band = pygame.Rect(0, 0, int(hr * 1.55), int(hr * 0.3))
    band.center = _pt(cx, y)
    pygame.draw.ellipse(surface, (60, 130, 230), band)
    for k in (-0.45, -0.15, 0.15, 0.45):
        pygame.draw.line(surface, (255, 255, 255), _pt(cx + hr * k, y - hr * 0.1), _pt(cx + hr * k, y + hr * 0.12), max(1, int(hr * 0.04)))
    tail = [(cx + hr * 0.3, y + hr * 0.05), (cx + hr * 0.62, y + hr * 0.1), (cx + hr * 0.7, y + hr * 0.62), (cx + hr * 0.4, y + hr * 0.58)]
    pygame.draw.polygon(surface, (50, 115, 215), tail)
    pygame.draw.line(surface, (255, 255, 255), _pt(cx + hr * 0.42, y + hr * 0.4), _pt(cx + hr * 0.68, y + hr * 0.44), max(1, int(hr * 0.04)))


def _neck_medal(surface, cx, cy, hr, t):
    y0 = cy + hr * 0.98
    my = cy + hr * 1.5
    w = _lw(hr, 0.09, 3)
    pygame.draw.line(surface, (60, 120, 230), _pt(cx - hr * 0.34, y0), _pt(cx, my - hr * 0.12), w)
    pygame.draw.line(surface, (230, 60, 80), _pt(cx + hr * 0.34, y0), _pt(cx, my - hr * 0.12), w)
    pygame.draw.circle(surface, (210, 150, 20), _pt(cx, my), int(hr * 0.2))
    pygame.draw.circle(surface, (255, 215, 70), _pt(cx, my), int(hr * 0.16))
    pygame.draw.polygon(surface, (255, 245, 190), _star_points(cx, my, hr * 0.11))


def _neck_cape_front(surface, cx, cy, hr, t):
    """ส่วนหน้าของผ้าคลุม: ปกคอ + กระดุมทอง (ตัวผ้าคลุมวาดไว้ด้านหลังตัวมังกร ดู _back_cape)"""
    y = cy + hr * 0.96
    band = pygame.Rect(0, 0, int(hr * 1.5), int(hr * 0.22))
    band.center = _pt(cx, y)
    pygame.draw.ellipse(surface, (205, 40, 65), band)
    pygame.draw.circle(surface, (255, 205, 60), _pt(cx, y + hr * 0.02), max(3, int(hr * 0.1)))


def _back_cape(surface, cx, cy, hr, t):
    sway = math.sin(t * 2.2) * hr * 0.08
    pts = [(cx - hr * 0.62, cy + hr * 0.92), (cx + hr * 0.62, cy + hr * 0.92),
           (cx + hr * 1.5 + sway, cy + hr * 2.3), (cx + hr * 0.4, cy + hr * 2.38), (cx - hr * 0.4, cy + hr * 2.38),
           (cx - hr * 1.5 - sway, cy + hr * 2.3)]
    pygame.draw.polygon(surface, (205, 40, 65), pts)
    pygame.draw.polygon(surface, (150, 20, 45), [(cx, cy + hr * 0.92), (cx + hr * 0.62, cy + hr * 0.92),
                                                   (cx + hr * 1.5 + sway, cy + hr * 2.3), (cx + hr * 0.4, cy + hr * 2.38), (cx, cy + hr * 2.38)])


HAT_DRAWERS = {"party": _hat_party, "cap": _hat_cap, "chef": _hat_chef, "wizard": _hat_wizard, "pirate": _hat_pirate,
               "crown": _hat_crown, "horns": _hat_horns, "flame": _hat_flame}
GLASSES_DRAWERS = {"round": _glasses_round, "sunglasses": _glasses_sunglasses, "goggles": _glasses_goggles,
                   "star": _glasses_star}
NECK_DRAWERS = {"bowtie": _neck_bowtie, "scarf": _neck_scarf, "medal": _neck_medal, "cape": _neck_cape_front}


# ---------------------------------------------------------------------------
# ใบหน้า/อารมณ์: ทุกอารมณ์ต่างกันที่ "ตา + คิ้ว + ปาก + สัญลักษณ์ประกอบ" พร้อมกัน (ไม่ใช่แค่ปากอย่างเดียว) เพื่อให้อ่านออกแม้ตัวเล็ก
#   happy    ยิ้มกว้างปากปิด แก้มแดง ตามีประกายสะท้อน คิ้วโค้งสบาย ๆ
#   excited  ตาโตสองประกาย คิ้วยกสูง อ้าปากกว้างเห็นฟัน+ลิ้น แก้มแดง ประกายดาวลอยรอบหัว
#   sad      เปลือกตาตกเฉียง คิ้วหัวคิ้วยกขึ้น ตาแดงฉ่ำ ปากคว่ำสั่น มีน้ำตาไหลลงเป็นช่วง ๆ
#   worried  ตาโตแต่รูม่านตาเล็กกวาดมองไปมา คิ้วหัวคิ้วยกสูง ปากหยัก เหงื่อหยด ตัวสั่นเบา ๆ
#   sleepy   หลับตาโค้ง คิ้วตก ปากเล็กกลมหายใจเข้าออก มีตัว Z ลอยขึ้น
# ขนาด/ความหนาทุกอย่างสเกลตามรัศมีหัว (hr) จึงชัดทั้งตอนตัวใหญ่ (หน้าแรก) และตัวเล็ก (ในบทเรียน/ตู้เสื้อผ้า)
# ---------------------------------------------------------------------------
MOODS = ("happy", "excited", "sad", "worried", "sleepy")

EYE_OUTLINE = (70, 45, 40)
MOUTH_INSIDE = (125, 28, 48)
TONGUE = (255, 125, 145)
BLUSH = (255, 105, 130)
TEAR = (125, 195, 255)

# ปัจจัยการเคลื่อนไหวของตัวตามอารมณ์: (ความสูงลอยตัวเทียบ size, ความเร็ว, แรงสั่นแนวนอนเทียบ size)
_MOTION = {
    "happy": (0.040, 2.0, 0.0),
    "excited": (0.040, 5.5, 0.0),     # เด้งถี่ ๆ
    "sad": (0.018, 1.2, 0.0),         # ลอยช้า ๆ ห่อเหี่ยว
    "worried": (0.018, 2.2, 0.012),   # สั่นเบา ๆ
    "sleepy": (0.030, 1.0, 0.0),      # หายใจช้า ๆ
}


def _dark(color, k=0.4):
    return tuple(int(c * k) for c in color)


def _blit_alpha(surface, draw_fn, size, topleft, alpha=255):
    """วาดลงพื้นผิวโปร่งใสเล็ก ๆ แล้วแปะ (ใช้กับแก้มจาง ๆ / ของที่ค่อย ๆ จาง)"""
    w, h = max(2, int(size[0])), max(2, int(size[1]))
    layer = pygame.Surface((w, h), pygame.SRCALPHA)
    draw_fn(layer)
    if alpha < 255:
        layer.set_alpha(max(0, min(255, int(alpha))))
    surface.blit(layer, (int(topleft[0]), int(topleft[1])))


def _thick_arc(surface, color, cx, cy, rx, ry, a0, a1, width, steps=18):
    """ส่วนโค้งของวงรีเส้นหนาแบบเรียบ (pygame.draw.arc เส้นหนาจะเป็นรอยขรุขระ/ขาดเป็นช่วง ๆ)
    มุมใช้ระบบเดียวกับ pygame.draw.arc: ทวนเข็มนาฬิกาตามที่เห็นบนจอ (π..2π = ครึ่งล่าง)"""
    pts = [(cx + rx * math.cos(a0 + (a1 - a0) * k / steps), cy - ry * math.sin(a0 + (a1 - a0) * k / steps))
           for k in range(steps + 1)]
    pygame.draw.lines(surface, color, False, [_pt(*p) for p in pts], max(1, int(width)))
    if width >= 3:   # ปลาย/ข้อต่อมน ไม่เป็นเหลี่ยม
        for p in (pts[0], pts[-1]):
            pygame.draw.circle(surface, color, _pt(*p), int(width / 2))


def _sparkle(surface, x, y, r, color):
    """ประกายดาว 4 แฉก"""
    pts = []
    for i in range(8):
        ang = -math.pi / 2 + i * math.pi / 4
        rad = r if i % 2 == 0 else r * 0.32
        pts.append((x + math.cos(ang) * rad, y + math.sin(ang) * rad))
    pygame.draw.polygon(surface, color, pts)


def _teardrop(surface, x, y, r, color=TEAR, alpha=255):
    """หยดน้ำ (ใช้เป็นน้ำตา/เหงื่อ) จุดศูนย์กลางวงกลมอยู่ที่ (x, y) ปลายแหลมชี้ขึ้น"""
    size = (r * 4, r * 5)

    def draw(layer):
        ox, oy = r * 2, r * 3
        pygame.draw.polygon(layer, color, [(ox - r * 0.85, oy - r * 0.35), (ox + r * 0.85, oy - r * 0.35), (ox, oy - r * 2.3)])
        pygame.draw.circle(layer, color, _pt(ox, oy), max(2, int(r)))
        pygame.draw.circle(layer, (255, 255, 255), _pt(ox - r * 0.35, oy - r * 0.2), max(1, int(r * 0.32)))
        pygame.draw.circle(layer, _dark(color, 0.55), _pt(ox, oy), max(2, int(r)), 1)

    _blit_alpha(surface, draw, size, (x - r * 2, y - r * 3), alpha)


def _draw_eyes(surface, cx, cy, hr, mood, t, body_color):
    eye_dx, eye_dy = hr * 0.38, -hr * 0.05
    lw = _lw(hr, 0.07, 2)
    blink = mood != "sleepy" and math.sin(t * 1.3) > 0.97   # กระพริบตาเป็นช่วงสั้น ๆ
    for side in (-1, 1):
        ex, ey = cx + side * eye_dx, cy + eye_dy
        if mood == "sleepy":
            # หลับตา: เส้นโค้งคว่ำ (∪) + ขนตาสั้น ๆ ที่หางตา
            rr = hr * 0.22
            _thick_arc(surface, EYE_OUTLINE, ex, ey + rr * 0.05, rr, rr * 0.75, math.pi * 1.08, math.pi * 1.92, lw)
            pygame.draw.line(surface, EYE_OUTLINE, _pt(ex + side * rr, ey + rr * 0.1),
                             _pt(ex + side * (rr + hr * 0.1), ey + rr * 0.45), max(1, lw - 1))
            continue
        if blink:
            rr = hr * 0.22
            pygame.draw.line(surface, EYE_OUTLINE, _pt(ex - rr, ey), _pt(ex + rr, ey), lw)
            continue

        if mood == "excited":
            R, pr, gaze = hr * 0.27, hr * 0.165, (0.0, -hr * 0.05)
        elif mood == "worried":
            R, pr = hr * 0.26, hr * 0.075
            gaze = (math.sin(t * 2.6) * hr * 0.09, hr * 0.01)       # กวาดตามองไปมาอย่างกระวนกระวาย
        elif mood == "sad":
            R, pr, gaze = hr * 0.23, hr * 0.135, (-side * hr * 0.03, hr * 0.07)   # มองลงต่ำ
        else:
            R, pr, gaze = hr * 0.22, hr * 0.12, (math.sin(t * 0.8) * hr * 0.02, 0.0)

        pygame.draw.circle(surface, EYE_WHITE, _pt(ex, ey), int(R))
        pygame.draw.circle(surface, EYE_OUTLINE, _pt(ex, ey), int(R), max(1, int(hr * 0.035)))
        gx = max(-(R - pr), min(R - pr, gaze[0]))
        gy = max(-(R - pr), min(R - pr, gaze[1]))
        px, py = ex + gx, ey + gy
        pygame.draw.circle(surface, EYE_BLACK, _pt(px, py), max(2, int(pr)))
        # ประกายสะท้อนในตา: ทำให้ตาดูมีชีวิตและอ่านอารมณ์ออกง่ายขึ้น
        hl = max(1, int(pr * (0.5 if mood == "sad" else 0.38)))
        pygame.draw.circle(surface, EYE_WHITE, _pt(px + pr * 0.38, py - pr * 0.38), hl)
        if mood in ("excited", "sad"):
            pygame.draw.circle(surface, EYE_WHITE, _pt(px - pr * 0.4, py + pr * 0.42), max(1, int(hl * 0.55)))

        if mood == "sad":
            # เปลือกตาบนตกเฉียง (หัวตาสูง หางตาต่ำ) + ขอบตาล่างแดงฉ่ำ
            o = side
            pad = 2
            lid = [(ex + o * (R + pad), ey - R - pad), (ex - o * (R + pad), ey - R - pad),
                   (ex - o * (R + pad), ey - R * 0.5), (ex + o * (R + pad), ey + R * 0.1)]
            pygame.draw.polygon(surface, body_color, lid)
            pygame.draw.line(surface, EYE_OUTLINE, _pt(ex - o * R, ey - R * 0.5), _pt(ex + o * R, ey + R * 0.1), lw)
            _thick_arc(surface, TEAR, ex, ey, R * 0.88, R * 0.88, math.pi * 1.2, math.pi * 1.8, max(2, int(hr * 0.05)), steps=10)


def _draw_mouth(surface, cx, cy, hr, mood, t, body_color):
    lw = _lw(hr, 0.07, 2) + 1
    ink = _dark(body_color, 0.38)
    if mood == "happy":
        _thick_arc(surface, ink, cx, cy + hr * 0.37, hr * 0.42, hr * 0.28, math.pi * 1.1, math.pi * 1.9, lw)
        for side in (-1, 1):   # ลักยิ้มที่มุมปาก
            pygame.draw.line(surface, ink, _pt(cx + side * hr * 0.41, cy + hr * 0.47),
                             _pt(cx + side * hr * 0.46, cy + hr * 0.41), max(1, lw - 1))
    elif mood == "excited":
        a, b, top = hr * 0.36, hr * 0.31, cy + hr * 0.38
        pts = [(cx + a * math.cos(math.pi * k / 16), top + b * math.sin(math.pi * k / 16)) for k in range(17)]
        pygame.draw.polygon(surface, MOUTH_INSIDE, pts)
        # ลิ้น (ตัดให้อยู่ในปาก) + ฟันบน
        pygame.draw.ellipse(surface, TONGUE, pygame.Rect(int(cx - a * 0.55), int(top + b * 0.52), int(a * 1.1), int(b * 0.5)))
        pygame.draw.rect(surface, EYE_WHITE, pygame.Rect(int(cx - a * 0.7), int(top), int(a * 1.4), max(2, int(b * 0.24))))
        pygame.draw.polygon(surface, ink, pts, max(1, lw - 1))
    elif mood == "sad":
        wob = math.sin(t * 13) * hr * 0.012          # ปากสั่นนิด ๆ
        _thick_arc(surface, ink, cx, cy + hr * 0.66 + wob, hr * 0.3, hr * 0.2, math.pi * 0.1, math.pi * 0.9, lw)
    elif mood == "worried":
        n, half = 5, hr * 0.3
        pts = [(cx - half + i * (2 * half / (n - 1)),
                cy + hr * 0.53 + (hr * 0.045 if i % 2 else -hr * 0.045) + math.sin(t * 7 + i) * hr * 0.01)
               for i in range(n)]
        pygame.draw.lines(surface, ink, False, pts, lw)
    else:  # sleepy: ปากเล็กกลม ๆ ขยาย/หดตามจังหวะหายใจ
        pulse = (math.sin(t * 1.6) + 1) / 2
        rx, ry = hr * (0.08 + 0.03 * pulse), hr * (0.06 + 0.06 * pulse)
        rect = pygame.Rect(0, 0, int(rx * 2), int(ry * 2))
        rect.center = _pt(cx, cy + hr * 0.52)
        pygame.draw.ellipse(surface, MOUTH_INSIDE, rect)
        pygame.draw.ellipse(surface, ink, rect, max(1, lw - 1))


def _draw_cheeks(surface, cx, cy, hr, mood):
    if mood not in ("happy", "excited", "sleepy"):
        return
    strength = {"happy": 120, "excited": 175, "sleepy": 95}[mood]
    rx, ry = hr * 0.17, hr * 0.1
    for side in (-1, 1):
        x, y = cx + side * hr * 0.64, cy + hr * 0.3
        _blit_alpha(surface, lambda layer: pygame.draw.ellipse(layer, (*BLUSH, strength), layer.get_rect()),
                    (rx * 2, ry * 2), (x - rx, y - ry))


def _draw_brows(surface, cx, cy, hr, mood, t, body_color):
    """คิ้ว: วาดทับแว่นเสมอ เพื่อให้คนใส่แว่นดำ/โกเกิลก็ยังอ่านอารมณ์ออก"""
    col = _dark(body_color, 0.38)
    lw = max(2, int(hr * 0.09))
    # (ยกสูงเพิ่ม, ปลายนอกลดต่ำลง, ปลายใน(หัวคิ้ว)ยกขึ้น, โค้งกลางคิ้ว, ความยาวครึ่งคิ้ว)
    cfg = {
        "happy": (0.00, 0.03, 0.00, 0.03, 0.17),
        "excited": (-0.09, 0.05, 0.0, 0.06, 0.18),
        "sad": (-0.01, 0.07, -0.09, 0.0, 0.17),
        "worried": (-0.05 + math.sin(t * 3) * 0.012, 0.10, -0.13, 0.0, 0.19),
        "sleepy": (0.05, 0.05, 0.0, 0.01, 0.16),
    }[mood]
    lift, outer_dy, inner_dy, arch, half = cfg
    base_y = cy - hr * 0.05 - hr * 0.35 + hr * lift
    for side in (-1, 1):
        bx = cx + side * hr * 0.37
        outer = (bx + side * hr * half, base_y + hr * outer_dy)
        inner = (bx - side * hr * half, base_y + hr * inner_dy)
        mid = (bx, base_y + hr * (outer_dy + inner_dy) / 2 - hr * arch)
        pygame.draw.lines(surface, col, False, [_pt(*outer), _pt(*mid), _pt(*inner)], lw)


def _draw_mood_extras(surface, cx, cy, hr, mood, t):
    """สัญลักษณ์ประกอบอารมณ์ที่วาดทับหน้า/หัว (น้ำตา เหงื่อ Z ประกายดาว)"""
    if mood == "excited":
        # ประกายดาวโคจรรอบ ๆ ขอบหัว (ไม่ผ่านกลางหน้า และไม่สูงเกินหัวมาก เพื่อไม่ทับข้อความเหนือมาสคอต)
        for i in range(3):
            ang = t * 3.2 + i * (2 * math.pi / 3)
            twinkle = 0.65 + 0.35 * math.sin(t * 9 + i * 2.1)
            _sparkle(surface, cx + math.cos(ang) * hr * 1.15, cy - hr * 0.15 + math.sin(ang) * hr * 0.8,
                     hr * 0.14 * twinkle, config.COLOR_SECONDARY)
    elif mood == "sad":
        R = hr * 0.23
        for k, side in enumerate((-1, 1)):
            p = (t * 0.75 + k * 0.5) % 1.0
            x = cx + side * hr * 0.38 + side * hr * 0.1
            y = cy - hr * 0.05 + R * 0.75 + p * hr * 0.7
            fade = 255 if p < 0.7 else int(255 * (1 - p) / 0.3)
            _teardrop(surface, x, y, max(2, hr * 0.085 * (1 - 0.25 * p)), alpha=fade)
    elif mood == "worried":
        p = (math.sin(t * 2.4) + 1) / 2
        _teardrop(surface, cx + hr * 0.78, cy - hr * 0.3 + p * hr * 0.22, max(2, hr * 0.1))
    elif mood == "sleepy":
        for i in range(3):
            p = (t * 0.4 + i / 3.0) % 1.0
            s = hr * (0.07 + 0.09 * p)
            x = cx + hr * (0.85 + 0.45 * p)
            y = cy - hr * (0.05 + 0.8 * p)
            fade = 255 if p < 0.65 else int(255 * (1 - p) / 0.35)
            w = max(2, int(hr * 0.045))

            def draw(layer, s=s, w=w):
                m = layer.get_width() / 2
                pts = [(m - s, m - s), (m + s, m - s), (m - s, m + s), (m + s, m + s)]
                pygame.draw.lines(layer, (235, 240, 255), False, pts, w)
                pygame.draw.lines(layer, (70, 60, 140), False, pts, 1)

            side_len = s * 2 + w * 4
            _blit_alpha(surface, draw, (side_len, side_len), (x - side_len / 2, y - side_len / 2), fade)



def draw_mascot(surface: pygame.Surface, center: tuple, size: int = 120, mood: str = "happy", t: float = 0.0,
                outfit=None):
    """
    วาดมังกรน้อยเบลซ ที่ตำแหน่ง center ขนาดโดยประมาณ size (เส้นผ่านศูนย์กลางหัว)
    mood: "happy" | "excited" | "sad" | "worried" | "sleepy" (ค่าอื่นถือเป็น happy)
    t: เวลา (วินาที) ใช้ทำแอนิเมชันลอยตัวเบา ๆ และกระพริบตา
    outfit: dict ช่อง -> id ของแต่งตัว (หมวก/แว่น/เครื่องประดับ/สีตัว) ไม่ส่งมา = ใช้ชุดของผู้เล่นปัจจุบัน (set_outfit)
    """
    if outfit is None:
        outfit = _current_outfit
    body_color, body_shade, belly_color, spike_color = PALETTES.get(outfit.get("color", "orange"), PALETTES["orange"])

    if mood not in MOODS:
        mood = "happy"
    cx, cy = center
    bob_amp, bob_speed, shiver = _MOTION[mood]
    cy += math.sin(t * bob_speed) * (size * bob_amp)
    cx += math.sin(t * 29) * (size * shiver)     # worried: ตัวสั่นแนวนอนเบา ๆ

    head_r = size * 0.5
    body_r = size * 0.62

    # --- ผ้าคลุม (ด้านหลังตัว) ---
    if outfit.get("neck") == "cape":
        _back_cape(surface, cx, cy, head_r, t)

    # --- หาง ---
    tail_points = [
        (cx - head_r * 0.2, cy + body_r * 0.9),
        (cx - head_r * 1.6, cy + body_r * 1.5),
        (cx - head_r * 0.9, cy + body_r * 1.65),
        (cx - head_r * 0.1, cy + body_r * 1.05),
    ]
    pygame.draw.polygon(surface, body_color, tail_points)

    # --- ลำตัว (วงรี) ---
    body_rect = pygame.Rect(0, 0, body_r * 1.7, body_r * 1.5)
    body_rect.center = (cx, cy + body_r * 0.75)
    pygame.draw.ellipse(surface, body_color, body_rect)
    belly_rect = body_rect.inflate(-body_r * 0.7, -body_r * 0.55)
    belly_rect.centery += body_r * 0.15
    pygame.draw.ellipse(surface, belly_color, belly_rect)

    # --- หนามบนหลัง (สามเหลี่ยมม่วง) ---
    n_spikes = 3
    for i in range(n_spikes):
        sx = cx - head_r * 0.3 + i * head_r * 0.55
        sy = cy - head_r * 0.55
        spike = [(sx, sy), (sx - head_r * 0.16, sy + head_r * 0.5), (sx + head_r * 0.16, sy + head_r * 0.5)]
        pygame.draw.polygon(surface, spike_color, spike)

    # --- หัว (วงกลม) ---
    head_center = (cx, cy)
    pygame.draw.circle(surface, body_color, head_center, head_r)

    # --- ปาก/จมูกยื่น ---
    snout_rect = pygame.Rect(0, 0, head_r * 0.9, head_r * 0.6)
    snout_rect.center = (cx, cy + head_r * 0.35)
    pygame.draw.ellipse(surface, belly_color, snout_rect)

    # --- รูจมูก ---
    pygame.draw.circle(surface, body_shade, (int(cx - head_r * 0.18), int(cy + head_r * 0.32)), max(2, int(head_r * 0.05)))
    pygame.draw.circle(surface, body_shade, (int(cx + head_r * 0.18), int(cy + head_r * 0.32)), max(2, int(head_r * 0.05)))

    # --- ใบหน้า: ตา -> ปาก -> แก้ม (ดูฟังก์ชันด้านบน) ---
    _draw_eyes(surface, cx, cy, head_r, mood, t, body_color)
    _draw_mouth(surface, cx, cy, head_r, mood, t, body_color)
    _draw_cheeks(surface, cx, cy, head_r, mood)

    # --- ของแต่งตัว (วาดทับหน้า: แว่น -> เครื่องประดับคอ -> คิ้ว -> หมวก) ---
    # คิ้ววาดหลังแว่น: คนใส่แว่นดำ/โกเกิล/แว่นดาวจะยังเห็นอารมณ์จากคิ้ว
    glasses_fn = GLASSES_DRAWERS.get(outfit.get("glasses"))
    if glasses_fn:
        glasses_fn(surface, cx, cy, head_r, t)
    neck_fn = NECK_DRAWERS.get(outfit.get("neck"))
    if neck_fn:
        neck_fn(surface, cx, cy, head_r, t)
    _draw_brows(surface, cx, cy, head_r, mood, t, body_color)
    hat_fn = HAT_DRAWERS.get(outfit.get("hat"))
    if hat_fn:
        hat_fn(surface, cx, cy, head_r, t)

    # --- สัญลักษณ์ประกอบอารมณ์ (ประกายดาว/น้ำตา/เหงื่อ/Z) ---
    _draw_mood_extras(surface, cx, cy, head_r, mood, t)




def draw_achievement_icon(surface: pygame.Surface, center: tuple, size: int, icon: str):
    """วาดไอคอนเล็ก ๆ สำหรับ Achievement
    (egg / flame / star / shield / trophy / crown / comet / diamond / medal / closet)"""
    cx, cy = center
    r = size / 2
    if icon == "egg":
        pygame.draw.ellipse(surface, config.COLOR_SECONDARY, (cx - r * 0.7, cy - r, r * 1.4, r * 2))
    elif icon == "flame":
        pts = [(cx, cy - r), (cx + r * 0.6, cy + r * 0.3), (cx, cy + r), (cx - r * 0.6, cy + r * 0.3)]
        pygame.draw.polygon(surface, config.COLOR_DANGER, pts)
        pygame.draw.polygon(surface, config.COLOR_SECONDARY, [(cx, cy - r * 0.4), (cx + r * 0.3, cy + r * 0.3),
                                                                (cx, cy + r * 0.6), (cx - r * 0.3, cy + r * 0.3)])
    elif icon == "star":
        points = []
        for i in range(10):
            ang = math.pi / 2 + i * math.pi / 5
            rad = r if i % 2 == 0 else r * 0.45
            points.append((cx + math.cos(ang) * rad, cy - math.sin(ang) * rad))
        pygame.draw.polygon(surface, config.COLOR_SECONDARY, points)
    elif icon == "shield":
        pts = [(cx, cy - r), (cx + r, cy - r * 0.4), (cx + r * 0.6, cy + r), (cx, cy + r * 0.8),
               (cx - r * 0.6, cy + r), (cx - r, cy - r * 0.4)]
        pygame.draw.polygon(surface, config.COLOR_ACCENT, pts)
    elif icon == "trophy":
        pygame.draw.rect(surface, config.COLOR_SECONDARY, (cx - r * 0.6, cy - r * 0.2, r * 1.2, r * 0.9), border_radius=4)
        pygame.draw.circle(surface, config.COLOR_SECONDARY, (int(cx), int(cy - r * 0.3)), int(r * 0.65))
        pygame.draw.rect(surface, config.COLOR_SECONDARY, (cx - r * 0.35, cy + r * 0.6, r * 0.7, r * 0.25))
    elif icon == "crown":
        # มงกุฎ: ฐานสี่เหลี่ยม + หยักสามเหลี่ยม 3 ยอดด้านบน ตรงกลางมีอัญมณีเล็ก ๆ
        pts = [
            (cx - r, cy + r * 0.5), (cx - r, cy - r * 0.1), (cx - r * 0.6, cy - r * 0.6),
            (cx - r * 0.3, cy - r * 0.05), (cx, cy - r * 0.75), (cx + r * 0.3, cy - r * 0.05),
            (cx + r * 0.6, cy - r * 0.6), (cx + r, cy - r * 0.1), (cx + r, cy + r * 0.5),
        ]
        pygame.draw.polygon(surface, config.COLOR_SECONDARY, pts)
        pygame.draw.circle(surface, config.COLOR_DANGER, (int(cx), int(cy + r * 0.15)), max(2, int(r * 0.18)))
    elif icon == "comet":
        # ดาวหาง: หัวเป็นวงกลม ลากหางเป็นแถบเรียวสีอ่อนลงไปทางขวาล่าง
        tail = [
            (cx - r * 0.35, cy - r * 0.35), (cx + r, cy + r), (cx + r * 0.7, cy + r),
            (cx - r * 0.1, cy + r * 0.15),
        ]
        pygame.draw.polygon(surface, (255, 220, 140), tail)
        pygame.draw.circle(surface, config.COLOR_SECONDARY, (int(cx - r * 0.35), int(cy - r * 0.35)), max(3, int(r * 0.5)))
    elif icon == "diamond":
        # เพชร: สี่เหลี่ยมข้าวหลามตัด + เส้นแบ่งเหลี่ยมมุมด้านในให้ดูมีมิติแวววาว
        pts = [(cx, cy - r), (cx + r * 0.75, cy - r * 0.15), (cx, cy + r), (cx - r * 0.75, cy - r * 0.15)]
        pygame.draw.polygon(surface, (140, 220, 255), pts)
        pygame.draw.line(surface, config.COLOR_WHITE, (cx - r * 0.75, cy - r * 0.15), (cx + r * 0.75, cy - r * 0.15), 2)
        pygame.draw.line(surface, config.COLOR_WHITE, (cx, cy - r), (cx, cy + r), 1)
    elif icon == "medal":
        # เหรียญรางวัล: วงกลมมีดาวตรงกลาง + ริบบิ้นสองแฉกห้อยด้านล่าง
        pygame.draw.polygon(surface, config.COLOR_DANGER,
                             [(cx - r * 0.45, cy - r * 0.1), (cx - r * 0.1, cy + r), (cx, cy + r * 0.4)])
        pygame.draw.polygon(surface, config.COLOR_ACCENT,
                             [(cx + r * 0.45, cy - r * 0.1), (cx + r * 0.1, cy + r), (cx, cy + r * 0.4)])
        pygame.draw.circle(surface, config.COLOR_SECONDARY, (int(cx), int(cy - r * 0.15)), int(r * 0.6))
        points = []
        for i in range(10):
            ang = math.pi / 2 + i * math.pi / 5
            rad = r * 0.3 if i % 2 == 0 else r * 0.12
            points.append((cx + math.cos(ang) * rad, cy - r * 0.15 - math.sin(ang) * rad))
        pygame.draw.polygon(surface, config.COLOR_DANGER, points)
    elif icon == "closet":
        # ตู้เสื้อผ้า: กรอบสี่เหลี่ยมมีเส้นแบ่งบานตรงกลาง + ลูกบิดสองข้าง
        pygame.draw.rect(surface, config.COLOR_ACCENT, (cx - r * 0.8, cy - r, r * 1.6, r * 2), border_radius=3)
        pygame.draw.line(surface, config.COLOR_BG, (cx, cy - r), (cx, cy + r), 2)
        pygame.draw.circle(surface, config.COLOR_SECONDARY, (int(cx - r * 0.25), int(cy)), max(2, int(r * 0.12)))
        pygame.draw.circle(surface, config.COLOR_SECONDARY, (int(cx + r * 0.25), int(cy)), max(2, int(r * 0.12)))
    elif icon == "speaker":
        # ไอคอนลำโพง + คลื่นเสียง วาดด้วยเวกเตอร์ล้วน ๆ (แทน emoji 🔊 ที่ฟอนต์ระบบบางเครื่องแสดงเป็นกล่องว่าง)
        color = config.COLOR_WHITE
        body = [
            (cx - r * 0.85, cy - r * 0.35), (cx - r * 0.35, cy - r * 0.35),
            (cx + r * 0.25, cy - r * 0.85), (cx + r * 0.25, cy + r * 0.85),
            (cx - r * 0.35, cy + r * 0.35), (cx - r * 0.85, cy + r * 0.35),
        ]
        pygame.draw.polygon(surface, color, body)
        pygame.draw.arc(surface, color, (cx + r * 0.05, cy - r * 0.55, r * 0.9, r * 1.1), -0.8, 0.8, 3)
        pygame.draw.arc(surface, color, (cx + r * 0.30, cy - r * 0.85, r * 1.4, r * 1.7), -0.8, 0.8, 3)
    else:
        pygame.draw.circle(surface, config.COLOR_SECONDARY, (int(cx), int(cy)), int(r))
