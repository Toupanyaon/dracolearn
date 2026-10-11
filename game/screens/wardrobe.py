"""
screens/wardrobe.py
-------------------
ตู้เสื้อผ้าของเบลซ: แต่งตัวให้มาสคอตด้วยหมวก/แว่นตา/เครื่องประดับ/สีตัว
  - ซ้าย: ตัวอย่างมาสคอตที่สวมชุดอยู่ตอนนี้ + ปุ่ม "สุ่มชุด" / "ถอดทั้งหมด"
  - ขวา: แท็บหมวดของ (4 หมวด) + ตารางการ์ดของแต่ละชิ้น กดการ์ดที่ปลดล็อกแล้วเพื่อสวมทันที (บันทึกอัตโนมัติ)
    ของที่ยังล็อกจะโชว์แบบมืด ๆ พร้อมเงื่อนไขปลดล็อก (กดแล้วมีข้อความบอกเงื่อนไข)
ข้อมูลของ/เงื่อนไขอยู่ที่ wardrobe.py ส่วนการวาดตัวมาสคอตอยู่ที่ mascot.py
"""

import random

import pygame

from .base import Screen
from .. import config, fx, mascot, wardrobe
from ..widgets import Button

CARD_W, CARD_H = 166, 132
CARD_GAP = 10
GRID_COLS = 3
GRID_AREA = (320, 146, 550, 444)   # x, y, w, h


class WardrobeScreen(Screen):
    def __init__(self, manager):
        super().__init__(manager)
        self.time = 0.0
        self.tab = "hat"
        self.card_rects = []   # [(rect, item_id)]  item_id เป็น id ของจริง หรือ "<slot>:none"

        tab_font = config.get_font(18, bold=True)
        self.tab_buttons = {}
        tab_w, tab_gap = 130, 10
        for i, slot in enumerate(wardrobe.SLOTS):
            btn = Button((320 + i * (tab_w + tab_gap), 92, tab_w, 44), wardrobe.SLOT_NAMES[slot], font=tab_font,
                         sounds=manager.sounds, on_click=lambda s=slot: self._set_tab(s))
            self.tab_buttons[slot] = btn

        side_font = config.get_font(20, bold=True)
        self.random_button = Button((48, 454, 234, 44), "สุ่มชุด", font=side_font, sounds=manager.sounds,
                                    on_click=self._randomize, base_color=config.COLOR_ACCENT,
                                    hover_color=(150, 120, 255))
        self.undress_button = Button((48, 508, 234, 44), "ถอดทั้งหมด", font=side_font, sounds=manager.sounds,
                                     on_click=self._undress, base_color=config.COLOR_BG, hover_color=config.COLOR_LOCK)
        self.back_button = Button((config.SCREEN_WIDTH - 170, 24, 140, 46), "< กลับ", font=config.get_font(20, bold=True),
                                  sounds=manager.sounds, on_click=lambda: manager.go_to("dashboard"),
                                  base_color=config.COLOR_BG_LIGHT, hover_color=config.COLOR_ACCENT)
        self._dim_cache = {}

    # ------------------------------------------------------------------
    def on_enter(self):
        self.time = 0.0
        self.tab = "hat"
        self.manager.apply_outfit()                 # แก้ชุดที่ผิดปกติ/ใส่ของที่ยังไม่ปลดล็อกในเซฟ ก่อนโชว์
        wardrobe.newly_unlocked(self.manager.player_data)  # เข้าตู้แล้วถือว่าเห็นของใหม่แล้ว (ไม่ต้องแจ้งซ้ำที่หน้าหลัก)
        self.manager.save()

    @property
    def data(self):
        return self.manager.player_data

    def _set_tab(self, slot):
        self.tab = slot

    def _commit(self):
        self.manager.apply_outfit()
        self.manager.save()

    def _equip(self, item_id):
        if wardrobe.equip(self.data, item_id):
            self._commit()
            return True
        return False

    def _undress(self):
        wardrobe.undress(self.data)
        self._commit()
        self.manager.toast.show("ถอดของแต่งตัวทั้งหมดแล้ว (สีตัวยังเหมือนเดิม)")

    def _randomize(self):
        """สุ่มชุดจากของที่ปลดล็อกแล้ว (หมวก/แว่น/เครื่องประดับอาจสุ่มได้ 'ไม่สวม' ด้วย) + สุ่มสีตัว"""
        unlocked = set(wardrobe.unlocked_ids(self.data))
        outfit = {}
        for slot in wardrobe.SLOTS:
            choices = [i.id for i in wardrobe.items_in_slot(slot) if i.id in unlocked]
            if slot != "color":
                choices.append(wardrobe.NONE_ID)
            outfit[slot] = random.choice(choices)
        self.data["outfit"] = outfit
        self._commit()

    # ------------------------------------------------------------------
    def update(self, dt):
        self.time += dt

    def handle_event(self, event):
        self.back_button.handle_event(event)
        self.random_button.handle_event(event)
        self.undress_button.handle_event(event)
        for btn in self.tab_buttons.values():
            btn.handle_event(event)

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for rect, item_id in self.card_rects:
                if rect.collidepoint(event.pos):
                    self._click_card(item_id)
                    break

    def _click_card(self, item_id):
        if ":" in item_id:   # "<slot>:none"
            self._equip(item_id)
            self.manager.sounds.play_click()
            return
        item = wardrobe.ITEM_MAP[item_id]
        if wardrobe.is_unlocked(item, self.data):
            self._equip(item_id)
            self.manager.sounds.play_click()
        else:
            self.manager.toast.show(f"{item.name} ยังล็อกอยู่: {wardrobe.requirement_text(item)}", duration=3.0)

    # ------------------------------------------------------------------
    def _wrap(self, text, font, max_width, max_lines=2):
        from ..i18n import tr
        text = tr(text)
        words, lines, cur = list(text), [], ""
        if " " in text:
            words = text.split(" ")
            sep = " "
        else:
            sep = ""     # ข้อความไทยไม่มีช่องว่าง ตัดทีละตัวอักษร
        for w in words:
            trial = (cur + sep + w) if cur else w
            if font.size(trial)[0] <= max_width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = lines[-1].rstrip() + "…"
        return lines

    def _dim_surface(self, size):
        surf = self._dim_cache.get(size)
        if surf is None:
            surf = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.rect(surf, (20, 14, 34, 150), (0, 0, size[0], size[1]), border_radius=14)
            self._dim_cache[size] = surf
        return surf

    @staticmethod
    def _draw_lock(surface, cx, cy):
        pygame.draw.arc(surface, config.COLOR_TEXT, pygame.Rect(cx - 7, cy - 13, 14, 16), 0, 3.1416, 3)
        pygame.draw.rect(surface, config.COLOR_TEXT, pygame.Rect(cx - 9, cy - 4, 18, 14), border_radius=3)
        pygame.draw.circle(surface, config.COLOR_BG, (cx, cy + 3), 2)

    def _card_entries(self):
        """(id สำหรับกด, ชื่อ, ชุดตัวอย่างบนการ์ด, Item หรือ None) ของแท็บปัจจุบัน"""
        current = wardrobe.normalize_outfit(self.data.get("outfit"), self.data)
        base = dict(wardrobe.DEFAULT_OUTFIT)
        base["color"] = current["color"]
        entries = []
        if self.tab != "color":
            entries.append((f"{self.tab}:none", "ไม่สวม", dict(base), None))
        for item in wardrobe.items_in_slot(self.tab):
            preview = dict(base)
            preview[item.slot] = item.id
            entries.append((item.id, item.name, preview, item))
        return current, entries

    def draw(self, surface):
        fx.draw_gradient_background(surface)
        fx.draw_ambient_blobs(surface, self.time)
        data = self.data

        title_font = config.get_font(30, bold=True)
        title = title_font.render("ตู้เสื้อผ้าของเบลซ", True, config.COLOR_TEXT)
        surface.blit(title, (36, 30))
        self.back_button.draw(surface)

        # --- การ์ดซ้าย: ตัวอย่างมาสคอต ---
        preview_card = pygame.Rect(30, 90, 270, 500)
        fx.draw_card(surface, preview_card)
        mascot.draw_mascot(surface, (preview_card.centerx, 238), size=140, mood="happy", t=self.time,
                           outfit=wardrobe.normalize_outfit(data.get("outfit"), data))
        got, total = wardrobe.unlocked_count(data)
        count_font = config.get_font(18, bold=True)
        count = count_font.render(f"ปลดล็อกแล้ว {got}/{total} ชิ้น", True, config.COLOR_SECONDARY)
        surface.blit(count, count.get_rect(center=(preview_card.centerx, 424)))
        self.random_button.draw(surface)
        self.undress_button.draw(surface)

        # --- แท็บ + ตารางของ ---
        for slot, btn in self.tab_buttons.items():
            selected = (slot == self.tab)
            btn.base_color = config.COLOR_ACCENT if selected else config.COLOR_BG_LIGHT
            btn.hover_color = (150, 120, 255) if selected else config.COLOR_LOCK
            btn.draw(surface)

        grid_card = pygame.Rect(*GRID_AREA)
        fx.draw_card(surface, grid_card)

        current, entries = self._card_entries()
        self.card_rects = []
        name_font = config.get_font(16, bold=True)
        req_font = config.get_font(12)
        label_font = config.get_font(13, bold=True)
        left = grid_card.x + (grid_card.width - (GRID_COLS * CARD_W + (GRID_COLS - 1) * CARD_GAP)) // 2
        top = grid_card.y + 14
        for idx, (item_id, name, preview, item) in enumerate(entries):
            col, row = idx % GRID_COLS, idx // GRID_COLS
            rect = pygame.Rect(left + col * (CARD_W + CARD_GAP), top + row * (CARD_H + CARD_GAP), CARD_W, CARD_H)
            locked = item is not None and not wardrobe.is_unlocked(item, data)
            equipped = (item is None and current[self.tab] == wardrobe.NONE_ID) or \
                       (item is not None and current.get(item.slot) == item.id)

            pygame.draw.rect(surface, config.COLOR_BG, rect, border_radius=14)
            border = config.COLOR_SUCCESS if equipped else config.COLOR_LOCK
            pygame.draw.rect(surface, border, rect, width=3 if equipped else 2, border_radius=14)

            # ขนาด 40 ที่ y+46: หมวกสูงสุดไม่เกินขอบบนการ์ด ตัว/หางจบก่อนบรรทัดชื่อ (y+96)
            mascot.draw_mascot(surface, (rect.centerx, rect.y + 46), size=40, mood="happy", t=self.time, outfit=preview)
            name_surf = name_font.render(name, True, config.COLOR_TEXT)
            surface.blit(name_surf, name_surf.get_rect(center=(rect.centerx, rect.y + 97)))

            if locked:
                surface.blit(self._dim_surface((rect.width, rect.height)), rect.topleft)
                self._draw_lock(surface, rect.right - 20, rect.y + 24)
                lines = self._wrap(wardrobe.requirement_text(item), req_font, rect.width - 16)
                for li, line in enumerate(lines):
                    t = req_font.render(line, True, config.COLOR_SECONDARY)
                    surface.blit(t, t.get_rect(center=(rect.centerx, rect.y + 113 + li * 13)))
            elif equipped:
                tag = label_font.render("สวมอยู่", True, config.COLOR_WHITE)
                tag_rect = tag.get_rect(center=(rect.centerx, rect.y + 117))
                pygame.draw.rect(surface, config.COLOR_SUCCESS, tag_rect.inflate(16, 4), border_radius=8)
                surface.blit(tag, tag_rect)
            self.card_rects.append((rect, item_id))

        hint_font = config.get_font(14)
        hint = hint_font.render("กดที่การ์ดเพื่อสวม", True, config.COLOR_TEXT)
        surface.blit(hint, hint.get_rect(center=(preview_card.centerx, 574)))
