"""
screens/survival.py
--------------------
โหมด Challenger (จับเวลา/Survival): ตอบคำถามให้ได้มากที่สุดก่อนเวลาหมด

กติกา (ค่าทั้งหมดปรับได้ใน game/config.py ส่วน SURVIVAL_*):
    - เริ่มด้วยเวลา 60 วินาที
    - ตอบถูก  +5 วินาที / ตอบผิด -5 วินาที
    - เวลาหมด (เหลือ 0) = ตาย จบเกม
    - คำถามยากขึ้นเรื่อย ๆ: ตอบถูกครบทุก 3 ข้อ ขึ้นระดับความยากถัดไป (ระดับ 1-10)
        ระดับ 1-3 = พื้นฐาน (A1, โจทย์บทเรียนปกติ) -> ระดับ 4-10 = โจทย์ Challenger เฉพาะโหมดนี้ (A2+ -> C2)
        ระดับความยากของแต่ละข้อดูได้ที่ content.question_difficulty() ชื่อระดับดูที่ content.level_name()
    - ไม่หักหัวใจและไม่ให้ XP (กันปั๊ม XP ในตารางคะแนน) แต่บันทึกสถิติ "ตอบถูกสูงสุด"
      ไว้ที่โปรไฟล์ (survival_best) และข้อที่ตอบผิดจะเข้าคลังทบทวนของโหมดฝึกฝนฟื้นฟูหัวใจ
    - คอมโบ: ตอบถูกติดกันทุก SURVIVAL_COMBO_STEP ข้อ ได้เวลาเพิ่ม +1 วินาที (สูงสุด SURVIVAL_COMBO_BONUS_MAX) ตอบผิดคอมโบขาด
    - ไอเท็มช่วยชีวิต (มีอย่างละ 1 ตอนเริ่มรอบ): 50:50 (ซ่อนตัวเลือกผิด 2 ข้อ), แช่แข็งเวลา, ข้ามข้อ
    - บอส: ตอบข้อปกติครบ SURVIVAL_BOSS_EVERY ข้อ บอสโผล่ = ข้อยาก 3 ข้อติดต่อกัน (ห้ามใช้ไอเท็ม)
      ชนะ = +15 วินาทีและได้ไอเท็มสุ่ม 1 ชิ้น / แพ้ (ตอบผิดสักข้อ) = โดนหักเวลาเพิ่ม
    - มีตารางคะแนนแยกเฉพาะโหมดนี้ (screens/challenger_board.py) ไม่ปนกับตาราง XP

สืบทอดจาก LessonScreen เพื่อใช้ตัววาดโจทย์ทั้ง 3 รูปแบบ + ระบบเสียงพูดเดิมทั้งหมด
"""

import random
from collections import deque

import pygame

from .lesson import LessonScreen
from .. import config, content, storage, achievements, mascot, fx
from ..widgets import Button, ProgressBar

# บทเรียนสมมติ ใช้แค่ให้ตัววาดพื้นหลังของ LessonScreen มีสีประจำโหมด (โทนส้มอมแดงอ่อน = เร่งด่วน)
_SURVIVAL_LESSON = content.Lesson("survival", "โหมดจับเวลา", [])

LIFELINES = ("fifty", "freeze", "skip")
LIFELINE_LABEL = {"fifty": "50:50", "freeze": "แช่แข็ง", "skip": "ข้าม"}
LIFELINE_KEYS = {"fifty": "K_F1", "freeze": "K_F2", "skip": "K_F3"}
LOW_TIME_SECONDS = 10      # เวลาเหลือน้อยกว่านี้ แถบเวลาเปลี่ยนเป็นสีแดง
MAX_FRAME_DT = 0.1         # กันเฟรมกระตุกครั้งเดียวกินเวลาผู้เล่นไปเยอะ


class SurvivalScreen(LessonScreen):
    def __init__(self, manager):
        super().__init__(manager)
        center_x = config.SCREEN_WIDTH // 2
        self.timer_bar = ProgressBar((40, 70, config.SCREEN_WIDTH - 80, 18))
        self.retry_button = Button((center_x - 320, 492, 200, 54), "เล่นอีกครั้ง",
                                    sounds=manager.sounds, on_click=self._restart)
        self.board_button = Button((center_x - 100, 492, 200, 54), "ตารางคะแนน",
                                    sounds=manager.sounds, on_click=lambda: manager.go_to("challenger_board"),
                                    base_color=config.COLOR_ACCENT, hover_color=(150, 120, 255))
        self.menu_button = Button((center_x + 120, 492, 200, 54), "กลับ Dashboard",
                                   sounds=manager.sounds, on_click=lambda: manager.go_to("dashboard"),
                                   base_color=config.COLOR_BG_LIGHT, hover_color=config.COLOR_ACCENT)
        self.lifeline_buttons = {}
        for i, name in enumerate(LIFELINES):
            self.lifeline_buttons[name] = Button(
                (center_x - 240 + i * 164, 570, 152, 44), LIFELINE_LABEL[name], font=config.get_font(18, bold=True),
                sounds=manager.sounds, on_click=lambda n=name: self.use_lifeline(n),
                base_color=config.COLOR_ACCENT, hover_color=(150, 120, 255))
        self.quit_button.on_click = self._quit  # กดออกกลางคัน ก็ยังเก็บสถิติของรอบนั้นให้
        self._survival_reset()

    # ------------------------------------------------------------------
    # สถานะของรอบเล่น
    # ------------------------------------------------------------------
    def _survival_reset(self):
        self.time_left = float(config.SURVIVAL_START_SECONDS)
        self.time_cap = float(config.SURVIVAL_START_SECONDS)  # เวลาสูงสุดที่เคยมีในรอบนี้ ใช้คิดความยาวแถบเวลา
        self.level = 1
        self.correct_count = 0
        self.wrong_count = 0
        self.vocab_learned = []
        self.pending_death = False   # ตอบผิดจนเวลาหมด: ให้ดูเฉลยก่อน แล้วค่อยขึ้นหน้าตาย
        self.new_record = False
        self._recent_ids = deque(maxlen=6)  # ข้อที่เพิ่งออกไป ไว้เลี่ยงสุ่มซ้ำติดกัน
        self.combo = 0
        self.best_combo = 0
        self.combo_bonus_now = 0      # โบนัสเวลาจากคอมโบของข้อล่าสุด
        self.boss_just_lost = False   # ข้อล่าสุดเป็นข้อที่ทำให้แพ้บอส
        self.lifelines = dict(config.SURVIVAL_START_LIFELINES)
        self.hidden_options = set()   # ตัวเลือกที่ถูกซ่อนด้วย 50:50 ในข้อปัจจุบัน
        self.freeze_left = 0.0        # เวลาที่เหลือของไอเท็มแช่แข็ง (วินาที)
        self.boss = None              # None หรือ {"done": จำนวนด่านที่ผ่านแล้ว, "total": จำนวนด่านทั้งหมด}
        self.since_boss = 0           # ข้อปกติที่ตอบแล้วนับจากบอสครั้งล่าสุด
        self.bosses_beaten = 0
        self.run_committed = False    # เก็บสถิติสะสมของรอบนี้ลงโปรไฟล์ไปแล้วหรือยัง (กันนับซ้ำ)

    def on_enter(self):
        self._reset_state()
        self.mode = "survival"
        self.unit = None
        self.lesson = _SURVIVAL_LESSON
        self.bg_top_cur, self.bg_bottom_cur = content.lesson_background(self.lesson, 0)
        self._start_run()

    def _start_run(self):
        self._survival_reset()
        self.effects = fx.ParticleSystem()
        self.timer_bar._animated_ratio = 1.0  # แถบเวลาเริ่มเต็มทันที ไม่ไล่ขึ้นมาจาก 0
        self.mascot_mood = "happy"
        self.mascot_mood_timer = 0.0
        self._ask_next_question()

    def _restart(self):
        self._start_run()

    # ------------------------------------------------------------------
    # เลือกคำถาม: ยากขึ้นตามจำนวนข้อที่ตอบถูก
    # ------------------------------------------------------------------
    def _target_level(self) -> int:
        return min(content.DIFFICULTY_LEVELS, 1 + self.correct_count // config.SURVIVAL_CORRECT_PER_LEVEL)

    def _pick_question(self, level: int) -> content.Question:
        pool = content.questions_at_level(level)
        fresh = [q for q in pool if q.id not in self._recent_ids]
        if not fresh:  # คลังระดับนี้เล็กกว่าที่จำไว้ -> ขอแค่ไม่ซ้ำกับข้อล่าสุด
            last = self._recent_ids[-1] if self._recent_ids else None
            fresh = [q for q in pool if q.id != last] or pool
        return random.choice(fresh)

    def _ask_next_question(self):
        new_level = self._target_level()
        if new_level > self.level:
            self.manager.sounds.play_achievement()
            self.effects.spawn_floating_text(f"ระดับ {new_level}! {content.level_name(new_level)}",
                                              (config.SCREEN_WIDTH // 2, 150), config.COLOR_ACCENT)
        self.level = new_level

        if self.boss is None and self.since_boss >= config.SURVIVAL_BOSS_EVERY:
            self.boss = {"done": 0, "total": config.SURVIVAL_BOSS_QUESTIONS}
            self.since_boss = 0
            self.manager.sounds.play_achievement()
            self.effects.spawn_floating_text("BOSS มาแล้ว! ตอบถูกติดกัน " + str(self.boss["total"]) + " ข้อ",
                                              (config.SCREEN_WIDTH // 2, 255), config.COLOR_DANGER)
        ask_level = self.level
        if self.boss is not None:
            ask_level = min(content.DIFFICULTY_LEVELS, self.level + config.SURVIVAL_BOSS_LEVEL_BOOST)

        self.hidden_options = set()
        q = self._pick_question(ask_level)
        self._recent_ids.append(q.id)
        self.questions = [q]
        self.index = 0
        self._setup_question()

    # ------------------------------------------------------------------
    # ตรวจคำตอบ / เวลา
    # ------------------------------------------------------------------
    def _check_answer(self):
        if self.phase != "answering" or not self._has_answer():
            return

        q = self._current_question()
        self.was_correct = content.is_correct_answer(q, self._submitted_answer_text())
        self.phase = "feedback"
        self.manager.sounds.speak(self._answer_audio(q), lang="en")

        data = self.manager.player_data
        storage.record_answer(data, q.id, self.was_correct, "challenger")  # สถิติหน้าสถิติ (นับรวมเป็นแถว Challenger)
        burst_pos = (config.SCREEN_WIDTH // 2, 330)

        in_boss = self.boss is not None
        self.boss_just_lost = False
        if not in_boss:
            self.since_boss += 1
        if self.was_correct:
            self.correct_count += 1
            self.combo += 1
            self.best_combo = max(self.best_combo, self.combo)
            self.combo_bonus_now = self.combo_bonus(self.combo)
            self.time_left += config.SURVIVAL_CORRECT_BONUS + self.combo_bonus_now
            self.time_cap = max(self.time_cap, self.time_left)
            storage.remove_wrong_question(data, q.id)
            if q.vocab:
                self.vocab_learned.append(q.vocab)
            self.manager.sounds.play_correct()
            self.effects.spawn_confetti(burst_pos, count=20)
            self.effects.spawn_floating_text(f"+{config.SURVIVAL_CORRECT_BONUS + self.combo_bonus_now} วินาที",
                                              burst_pos, config.COLOR_SUCCESS)
            self.mascot_mood = "excited"
            if in_boss:
                self._boss_progress()
        else:
            self.wrong_count += 1
            self.combo = 0
            self.combo_bonus_now = 0
            penalty = config.SURVIVAL_WRONG_PENALTY
            if in_boss:
                self.boss_just_lost = True
                penalty += config.SURVIVAL_BOSS_FAIL_PENALTY
                self.boss = None
                self.effects.spawn_floating_text("แพ้บอส!", (config.SCREEN_WIDTH // 2, 255), config.COLOR_DANGER)
            self.time_left = max(0.0, self.time_left - penalty)
            storage.record_wrong_question(data, q.id)
            self.manager.sounds.play_wrong()
            self.effects.spawn_floating_text(f"-{penalty} วินาที", burst_pos, config.COLOR_DANGER)
            self.mascot_mood = "sad"
            if self.time_left <= 0:
                self.pending_death = True
        self.mascot_mood_timer = 1.2
        self.manager.save()

    @staticmethod
    def combo_bonus(combo: int) -> int:
        """โบนัสเวลา (วินาที) ที่ได้เพิ่มเมื่อคอมโบถึงค่านี้: +1 ต่อทุก SURVIVAL_COMBO_STEP ข้อ สูงสุด SURVIVAL_COMBO_BONUS_MAX"""
        return min(config.SURVIVAL_COMBO_BONUS_MAX, max(0, combo) // config.SURVIVAL_COMBO_STEP)

    def _boss_progress(self):
        """ตอบถูกข้อบอส: นับด่านที่ผ่าน ถ้าครบทุกด่าน = ชนะบอส (ได้เวลา + ไอเท็มสุ่ม)"""
        self.boss["done"] += 1
        if self.boss["done"] < self.boss["total"]:
            return
        self.boss = None
        self.bosses_beaten += 1
        self.time_left += config.SURVIVAL_BOSS_WIN_BONUS
        self.time_cap = max(self.time_cap, self.time_left)
        reward = random.choice(LIFELINES)
        self.lifelines[reward] = self.lifelines.get(reward, 0) + 1
        self.manager.sounds.play_achievement()
        self.effects.spawn_confetti((config.SCREEN_WIDTH // 2, 330), count=40)
        self.effects.spawn_floating_text(f"ชนะบอส! +{config.SURVIVAL_BOSS_WIN_BONUS} วินาที + {LIFELINE_LABEL[reward]}",
                                          (config.SCREEN_WIDTH // 2, 255), config.COLOR_SECONDARY)

    # ------------------------------------------------------------------
    # ไอเท็มช่วยชีวิต
    # ------------------------------------------------------------------
    def can_use_lifeline(self, name: str) -> bool:
        if self.phase != "answering" or self.boss is not None or self.lifelines.get(name, 0) <= 0:
            return False
        q = self._current_question()
        if name == "fifty":
            return (self._kind(q) == "mcq" and not self.hidden_options
                    and len(self._options_for(q)) - len(self.hidden_options) > 2)
        if name == "freeze":
            return self.freeze_left <= 0
        return True  # skip

    def use_lifeline(self, name: str) -> bool:
        """ใช้ไอเท็ม คืน True ถ้าใช้สำเร็จ (ใช้ไม่ได้ = ไม่เสียไอเท็ม)"""
        if not self.can_use_lifeline(name):
            return False
        self.lifelines[name] -= 1
        pos = (config.SCREEN_WIDTH // 2, 255)
        if name == "fifty":
            q = self._current_question()
            wrong = [o for o in self._options_for(q) if o.strip().lower() != q.correct_answer.strip().lower()]
            self.hidden_options = set(random.sample(wrong, 2))
            if self.selected_option in self.hidden_options:
                self.selected_option = None
            self.effects.spawn_floating_text("50:50 ตัดตัวเลือกผิด 2 ข้อ", pos, config.COLOR_ACCENT)
        elif name == "freeze":
            self.freeze_left = float(config.SURVIVAL_FREEZE_SECONDS)
            self.effects.spawn_floating_text(f"เวลาหยุด {config.SURVIVAL_FREEZE_SECONDS} วินาที", pos, (90, 200, 255))
        else:
            self.manager.sounds.stop_speech()
            self.effects.spawn_floating_text("ข้ามข้อนี้", pos, config.COLOR_SECONDARY)
            self._ask_next_question()
        return True

    def _visible_options(self, q):
        return [o for o in self._options_for(q) if o not in self.hidden_options]

    def _commit_run(self):
        """เก็บสถิติสะสมของรอบนี้ลงโปรไฟล์ (นับครั้งเดียวต่อรอบ)"""
        if self.run_committed:
            return
        self.run_committed = True
        data = self.manager.player_data
        if self.correct_count + self.wrong_count == 0:
            return  # ออกก่อนตอบสักข้อ ไม่นับเป็นรอบ
        data["challenger_runs"] = data.get("challenger_runs", 0) + 1
        data["challenger_best_combo"] = max(data.get("challenger_best_combo", 0), self.best_combo)
        data["challenger_bosses_beaten"] = data.get("challenger_bosses_beaten", 0) + self.bosses_beaten

    def _next_question(self):
        if self.phase == "dead":
            return
        if self.pending_death:
            self._die()
            return
        self._ask_next_question()

    def _commit_best(self) -> bool:
        """อัปเดตสถิติสูงสุดของโปรไฟล์ถ้ารอบนี้ทำได้ดีกว่า คืน True ถ้าเป็นสถิติใหม่"""
        data = self.manager.player_data
        if self.correct_count > data.get("survival_best", 0):
            data["survival_best"] = self.correct_count
            data["survival_best_level"] = self.level
            return True
        return False

    def _die(self):
        """เวลาหมด = ตาย: เก็บสถิติสูงสุด แล้วแสดงหน้าสรุปผลรอบนี้"""
        self.phase = "dead"
        self.pending_death = False
        self.time_left = 0.0
        self.new_record = self._commit_best()
        self._commit_run()

        # ตรวจ Achievement ทันทีตอนจบรอบ (ไม่ต้องรอไปเรียนบทเรียนปกติ) เผื่อเพิ่งทำสถิติ
        # ระดับ Challenger ใหม่ (survival_legend) หรือเพิ่ง XP/Wardrobe ครบเงื่อนไขพอดีจากรอบนี้
        data = self.manager.player_data
        newly = achievements.check_achievements(data)
        if newly:
            first = content.ACHIEVEMENT_MAP.get(newly[0])
            if first:
                self.manager.toast.show(f"ปลดล็อกความสำเร็จ: {first.title}!", duration=3.0)
            self.manager.sounds.play_achievement()

        self.manager.sounds.stop_speech()
        self.manager.sounds.play_wrong()
        self.manager.save()

    def _quit(self):
        if self.phase != "dead":
            self._commit_best()
            self._commit_run()
            self.manager.save()
        self.manager.go_to("dashboard")

    def update(self, dt):
        super().update(dt)
        if self.phase == "dead" or self.lesson is not _SURVIVAL_LESSON:
            return
        counting = self.phase == "answering" or (
            self.phase == "feedback" and not config.SURVIVAL_PAUSE_ON_FEEDBACK)
        if counting and self.freeze_left > 0:
            self.freeze_left = max(0.0, self.freeze_left - min(dt, MAX_FRAME_DT))  # เวลาหยุดนิ่งระหว่างแช่แข็ง
        elif counting:
            self.time_left -= min(dt, MAX_FRAME_DT)
            if self.time_left <= 0:
                self._die()

    # ------------------------------------------------------------------
    # เหตุการณ์ / การวาด
    # ------------------------------------------------------------------
    def handle_event(self, event):
        if self.phase == "dead":
            self.quit_button.handle_event(event)
            self.retry_button.handle_event(event)
            self.board_button.handle_event(event)
            self.menu_button.handle_event(event)
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._restart()
            return
        if self.phase == "answering":
            for name, btn in self.lifeline_buttons.items():
                btn.set_disabled(not self.can_use_lifeline(name))
                btn.handle_event(event)
            if event.type == pygame.KEYDOWN:
                for name in LIFELINES:
                    if event.key == getattr(pygame, LIFELINE_KEYS[name], None):
                        self.use_lifeline(name)
                        return
        super().handle_event(event)

    def _draw_top_bar(self, surface):
        t = max(0.0, self.time_left)
        original_fg = self.timer_bar.fg_color
        self.timer_bar.fg_color = config.COLOR_DANGER if t <= LOW_TIME_SECONDS else config.COLOR_SUCCESS
        label = f"เหลือเวลา {t:.1f} วินาที"
        if self.freeze_left > 0:
            self.timer_bar.fg_color = (90, 200, 255)
            label = f"แช่แข็งเวลา! {self.freeze_left:.1f} วินาที (เหลือ {t:.1f})"
        self.timer_bar.draw(surface, t / self.time_cap, label=label)
        self.timer_bar.fg_color = original_fg

        info_font = config.get_font(20, bold=True)
        info = info_font.render(
            f"ระดับ {self.level}/{content.DIFFICULTY_LEVELS} {content.level_name(self.level)}"
            f"   ตอบถูก {self.correct_count} ข้อ",
            True, config.COLOR_TEXT_DARK)
        surface.blit(info, info.get_rect(topright=(config.SCREEN_WIDTH - 40, 28)))

    def _display_mood(self) -> str:
        """เวลาเหลือน้อย (แถบเวลาเป็นสีแดง) และยังไม่มีปฏิกิริยาใหม่ -> มาสคอตทำหน้ากังวล เหงื่อตก"""
        if self.mascot_mood == "happy" and self.time_left <= LOW_TIME_SECONDS:
            return "worried"
        return self.mascot_mood

    def _feedback_text(self) -> str:
        if self.was_correct:
            extra = f" (คอมโบ x{self.combo} +{self.combo_bonus_now})" if self.combo_bonus_now else (
                f" (คอมโบ x{self.combo})" if self.combo >= 2 else "")
            return f"ถูกต้อง! +{config.SURVIVAL_CORRECT_BONUS + self.combo_bonus_now} วินาที{extra}"
        lost = config.SURVIVAL_WRONG_PENALTY + (config.SURVIVAL_BOSS_FAIL_PENALTY if self.boss_just_lost else 0)
        return f"ยังไม่ถูกนะ -{lost} วินาที" + (" (แพ้บอส)" if self.boss_just_lost else "")

    def _next_button_label(self) -> str:
        return "ดูผลคะแนน" if self.pending_death else "ข้อถัดไป"

    def draw(self, surface):
        if self.phase != "dead":
            super().draw(surface)
            self._draw_challenger_overlay(surface)
            return
        self._draw_dead(surface)

    def _draw_challenger_overlay(self, surface):
        """ส่วนเสริมของ Challenger แบบโหด: ป้ายบอส, คอมโบ, ปุ่มไอเท็ม"""
        if self.boss is not None:
            pill = pygame.Rect(450, 118, 190, 32)
            pygame.draw.rect(surface, config.COLOR_DANGER, pill, border_radius=16)
            t = config.get_font(17, bold=True).render(
                f"BOSS  ด่าน {self.boss['done'] + 1}/{self.boss['total']}", True, config.COLOR_WHITE)
            surface.blit(t, t.get_rect(center=pill.center))
        font = config.get_font(18, bold=True)
        if self.combo >= 2:
            c = font.render(f"คอมโบ x{self.combo}", True, config.COLOR_TEXT_DARK)
            surface.blit(c, (40, 568))
            nxt = config.SURVIVAL_COMBO_STEP - self.combo % config.SURVIVAL_COMBO_STEP
            if self.combo_bonus(self.combo) < config.SURVIVAL_COMBO_BONUS_MAX:
                small = config.get_font(14).render(f"อีก {nxt} ข้อ โบนัสเวลา +1", True, config.COLOR_TEXT_DARK_MUTED)
                surface.blit(small, (40, 592))
        for name, btn in self.lifeline_buttons.items():
            n = self.lifelines.get(name, 0)
            btn.text = f"{LIFELINE_LABEL[name]} x{n}"
            btn.set_disabled(not self.can_use_lifeline(name))
            btn.draw(surface)
        if self.boss is not None:
            hint = config.get_font(14).render("บอส: ห้ามใช้ไอเท็ม", True, config.COLOR_TEXT_DARK_MUTED)
            surface.blit(hint, hint.get_rect(midtop=(config.SCREEN_WIDTH // 2, 616)))

    def _draw_dead(self, surface):
        fx.draw_gradient_background(surface, self.bg_top_cur, self.bg_bottom_cur)
        fx.draw_ambient_blobs(surface, self.time, tint=self.bg_top_cur)
        center_x = config.SCREEN_WIDTH // 2

        mascot.draw_mascot(surface, (center_x, 108), size=100, mood="sad", t=self.time)
        title_font = config.get_font(34, bold=True)
        title = title_font.render("หมดเวลา! คุณตายแล้ว", True, config.COLOR_DANGER)
        surface.blit(title, title.get_rect(center=(center_x, 226)))

        card = pygame.Rect(center_x - 260, 258, 520, 210)
        fx.draw_card(surface, card)
        total = self.correct_count + self.wrong_count
        accuracy = int(self.correct_count / total * 100) if total else 0
        best = self.manager.player_data.get("survival_best", 0)
        lines = [
            f"ตอบถูก {self.correct_count} ข้อ / ตอบผิด {self.wrong_count} ข้อ (แม่นยำ {accuracy}%)",
            f"ไปถึงระดับความยาก {self.level}/{content.DIFFICULTY_LEVELS} ({content.level_name(self.level)})",
            f"สถิติสูงสุด: {best} ข้อ",
        ]
        rank = storage.survival_rank(self.manager.root, self.manager.current_profile_key)
        if rank:
            lines.append(f"อันดับที่ {rank[0]} จาก {rank[1]} คนในตาราง Challenger")
        lines.append(f"คอมโบสูงสุด x{self.best_combo} · ล้มบอส {self.bosses_beaten} ตัว")
        stat_font = config.get_font(20)
        y = 280
        for line in lines:
            surf = stat_font.render(line, True, config.COLOR_TEXT_MUTED)
            surface.blit(surf, surf.get_rect(center=(center_x, y)))
            y += 31
        if self.new_record:
            rec_font = config.get_font(22, bold=True)
            rec = rec_font.render("สถิติใหม่!", True, config.COLOR_SECONDARY)
            surface.blit(rec, rec.get_rect(center=(center_x, y + 6)))

        self.retry_button.draw(surface)
        self.board_button.draw(surface)
        self.menu_button.draw(surface)
        self.quit_button.draw(surface)
