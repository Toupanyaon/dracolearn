"""
screens/lesson.py
--------------------
หน้าทำแบบฝึกหัด รองรับคำถาม 5 รูปแบบ: mcq, word_order, translate_type + โจทย์ฟัง listen_mcq (ฟังแล้วเลือก) / listen_type (ฟังแล้วพิมพ์ตาม)
มีแถบความคืบหน้า, หัวใจ, ปุ่มตรวจคำตอบ (กดไม่ได้ถ้ายังไม่ตอบ), feedback,
หักหัวใจเมื่อตอบผิด, เพิ่ม XP เมื่อตอบถูก, และหน้าต่างแจ้งเตือนเมื่อหัวใจหมด
"""

import random
from collections import Counter
import time

import pygame

from .base import Screen
from .. import config, content, storage, achievements, mascot, fx
from ..widgets import Button, ProgressBar, HeartMeter, TextInputBox


class LessonScreen(Screen):
    def __init__(self, manager):
        super().__init__(manager)
        self.progress_bar = ProgressBar((40, 70, config.SCREEN_WIDTH - 80, 18))
        self.hearts = HeartMeter((config.SCREEN_WIDTH - 56 - (config.MAX_HEARTS * 28 - 6), 25))

        self.check_button = Button((config.SCREEN_WIDTH // 2 - 110, 500, 220, 54), "ตรวจคำตอบ",
                                    sounds=manager.sounds, on_click=self._check_answer)
        self.next_button = Button((config.SCREEN_WIDTH // 2 - 110, 500, 220, 54), "ข้อถัดไป",
                                   sounds=manager.sounds, on_click=self._next_question)
        self.speak_button = Button((config.SCREEN_WIDTH // 2 + 140, 500, 170, 54), "   ฟังเสียง",
                                    sounds=manager.sounds, on_click=self._speak_current,
                                    base_color=config.COLOR_ACCENT, hover_color=(150, 120, 255))
        # ปุ่มให้พูดทวนโจทย์ปัจจุบันซ้ำได้ (นอกเหนือจากที่พูดอัตโนมัติตอนขึ้นคำถามใหม่ใน _setup_question)
        self.listen_prompt_button = Button((90, 126, 150, 40), "   ฟังโจทย์",
                                            sounds=manager.sounds, on_click=self._speak_prompt,
                                            base_color=config.COLOR_ACCENT, hover_color=(150, 120, 255))
        # ปุ่มเปิด/ปิดการอ่านคำที่กด (ข้อเรียงคำ/เลือกตอบ) - จำค่าไว้ในโปรไฟล์ผู้เล่น (read_words_on_tap)
        self.read_toggle_button = Button((250, 126, 170, 40), "", font=config.get_font(18, bold=True),
                                          sounds=manager.sounds, on_click=self._toggle_read_words)
        # ปุ่มลำโพงใหญ่กลางการ์ด (โชว์เฉพาะโจทย์ฟัง listen_mcq / listen_type) กดฟังเสียงซ้ำได้ไม่จำกัด
        self.listen_big_button = Button((config.SCREEN_WIDTH // 2 - 30 - 60, 205, 120, 56), "",
                                         sounds=manager.sounds, on_click=self._replay_audio)
        self.quit_button = Button((30, 20, 120, 44), "ออก", sounds=manager.sounds,
                                   on_click=lambda: manager.go_to("dashboard"),
                                   base_color=config.COLOR_BG_LIGHT, hover_color=config.COLOR_DANGER)

        # โหมดทบทวนฝึกฝนเพื่อฟื้นฟูหัวใจ: ตอบถูกครบ config.PRACTICE_CORRECT_TO_REGEN ข้อ ได้หัวใจคืน 1 ดวง
        self.practice_button = Button((config.SCREEN_WIDTH // 2 - 190, 350, 380, 56),
                                       "🔥 ฝึกฝนเพื่อฟื้นฟูหัวใจ", sounds=manager.sounds,
                                       on_click=self._start_practice_mode,
                                       base_color=config.COLOR_SUCCESS, hover_color=(60, 170, 110))
        self.out_button = Button((config.SCREEN_WIDTH // 2 - 130, 420, 260, 54), "กลับไปพักหัวใจก่อน",
                                  sounds=manager.sounds, on_click=lambda: manager.go_to("dashboard"))

        self.text_input = TextInputBox((config.SCREEN_WIDTH // 2 - 200, 300, 400, 52),
                                        placeholder="พิมพ์คำตอบภาษาอังกฤษ...")

        self.effects = fx.ParticleSystem()  # คอนเฟตตี้ + ข้อความ +XP ลอย ตอนตอบถูก
        self.time = 0.0
        self.bg_top_cur = None     # สีพื้นหลังที่กำลังแสดงอยู่ (ไล่เข้าหาสีเป้าหมายของข้อปัจจุบันทีละนิด)
        self.bg_bottom_cur = None
        self.mascot_mood_timer = 0.0
        self.mascot_mood = "happy"

        self._reset_state()

    def _reset_state(self):
        self.audio_unavailable = False  # True = เล่นเสียงไม่ได้ (ปิดเสียง/ไม่มี TTS) โจทย์ฟังจะโชว์ข้อความแทน ไม่ให้ตอบไม่ได้
        self.unit = None
        self.lesson = None
        self.questions = []
        self.index = 0
        self.phase = "answering"  # answering | feedback | out_of_hearts
        self.correct_count = 0
        self.wrong_count = 0
        self.xp_earned = 0
        self.vocab_learned = []
        self.start_time = time.time()

        self.mcq_option_rects = []
        self.shown_options = []   # ตัวเลือกของข้อ mcq ข้อปัจจุบัน "หลังสลับตำแหน่งแล้ว" (สลับใหม่ทุกครั้งที่ขึ้นข้อใหม่)
        self.selected_option = None
        self.was_correct = False

        self.word_tiles = []      # คำที่ยังอยู่ใน word bank (ยังไม่ได้เลือก)
        self.built_words = []     # คำที่ผู้เล่นเลือกมาเรียงแล้ว
        self.word_tile_rects = []
        self.built_word_rects = []

        # --- โหมดทบทวนฝึกฝนเพื่อฟื้นฟูหัวใจ ---
        self.mode = "normal"          # "normal" | "practice"
        self.practice_correct = 0     # จำนวนข้อที่ตอบถูกแล้วในรอบฝึกฝนปัจจุบัน
        self._practice_question = None       # โจทย์ข้อปัจจุบันของโหมดฝึกฝน (ไว้เลี่ยงสุ่มซ้ำติดกัน)
        self._saved_normal_questions = None  # เก็บชุดคำถามของบทเรียนเดิมไว้ ระหว่างพักไปฝึกฝน
        self._saved_normal_index = 0         # เก็บตำแหน่งข้อเดิมไว้ กลับมาเล่นต่อจากตรงนี้พอดี

    def on_enter(self):
        self._reset_state()
        self.unit = self.manager.context.get("active_unit")
        self.lesson = self.manager.context.get("active_lesson")
        self.questions = content.get_questions(self.lesson.question_ids)
        self.bg_top_cur, self.bg_bottom_cur = content.lesson_background(self.lesson, 0)  # เริ่มที่สีข้อแรกทันที
        self._setup_question()

    def _setup_question(self):
        self.phase = "answering"
        self.mascot_mood, self.mascot_mood_timer = "happy", 0.0  # ขึ้นข้อใหม่ = สีหน้าเริ่มใหม่
        self.selected_option = None
        q = self._current_question()
        self._shuffle_options(q)
        self.word_tiles = list(q.word_bank)
        random.shuffle(self.word_tiles)
        self.built_words = []
        self.text_input.clear()
        self.audio_unavailable = False
        if self._is_listening(q):
            # โจทย์ฟัง: เล่นเสียงให้ฟังอัตโนมัติ (ไม่อ่านตัวโจทย์ เพราะเป็นแค่คำสั่งสั้น ๆ) ถ้าเล่นไม่ได้ให้แสดงเป็นข้อความแทน
            self.audio_unavailable = not self.manager.sounds.speak(q.audio_text, lang=content.LEARN_LANG)
        else:
            text, lang = self._prompt_speech(q)
            self.manager.sounds.speak(text, lang=lang)  # พูดทวนโจทย์ให้ฟังอัตโนมัติทุกครั้งที่ขึ้นคำถามใหม่ (ภาษาตาม q.prompt_lang: th/en)

    @staticmethod
    def _prompt_speech(q):
        """(ข้อความ, ภาษา) ที่ใช้อ่านโจทย์ข้อนี้ออกเสียง: โจทย์ปกติอ่านตัวโจทย์ตามภาษาของโจทย์
        แต่ข้อที่มี audio_text (เช่น คอร์สไทยที่โจทย์เป็นอังกฤษแต่มีคำไทยให้ฟัง) อ่านคำนั้นด้วยเสียงของภาษาที่เรียน
        เพราะเสียงอังกฤษอ่านอักษรไทยไม่ได้"""
        if q.audio_text and q.qtype not in ("listen_mcq", "listen_type"):
            return q.audio_text, content.LEARN_LANG
        return content.prompt_for_speech(q.prompt), q.prompt_lang

    def _visible_options(self, q):
        """ตัวเลือกที่แสดงจริง (โหมด Challenger ซ่อนตัวเลือกผิดได้ด้วยไอเท็ม 50:50) - หน้าบทเรียนปกติแสดงครบ"""
        return self._options_for(q)

    def _shuffle_options(self, q):
        """สลับตำแหน่งตัวเลือก mcq / listen_mcq แบบสุ่มทุกครั้งที่ขึ้นข้อใหม่ (ทั้งโหมดปกติและ Challenger)
        ในคลังโจทย์เฉลยถูกเขียนไว้ตัวเลือกแรกเกือบทุกข้อ ถ้าไม่สลับ เฉลยจะอยู่ช่องซ้ายบนตลอด
        สลับเฉพาะลำดับที่โชว์ ไม่แตะ q.options เดิม (ข้ออื่น/เทสต์ที่อ้างลำดับเดิมจึงไม่กระทบ)"""
        options = list(q.options)
        random.shuffle(options)
        self.shown_options = options

    def _options_for(self, q):
        """ตัวเลือกที่ต้องวาด: ใช้ชุดที่สลับไว้แล้วของข้อนี้ (ลำดับคงเดิมทุกเฟรมและตอนเฉลย)
        ถ้าชุดที่สลับไว้ไม่ตรงกับข้อนี้ (เช่นสลับข้อโดยไม่ผ่าน _setup_question) จะสลับใหม่ให้เอง"""
        if Counter(self.shown_options) != Counter(q.options):
            self._shuffle_options(q)
        return self.shown_options

    def _start_practice_mode(self):
        """เข้าสู่โหมดทบทวนฝึกฝนเพื่อฟื้นฟูหัวใจ (กดจากหน้าจอ 'หัวใจหมดแล้ว')
        เก็บชุดคำถามของบทเรียนเดิมไว้ก่อน แล้วเริ่มสุ่มโจทย์จากคลังคำที่เคยตอบผิด"""
        self.mode = "practice"
        self.practice_correct = 0
        self._practice_question = None
        self._saved_normal_questions = self.questions
        self._saved_normal_index = self.index
        self._start_practice_question()

    def _start_practice_question(self):
        """สุ่มโจทย์ 1 ข้อสำหรับโหมดฝึกฝน: เอาจากคลังคำที่เคยตอบผิด (wrong_question_ids) ก่อน
        ถ้าไม่เคยตอบผิดข้อไหนเลย (ไม่น่าเกิดขึ้นเพราะหัวใจหมดต้องเคยตอบผิดมาแล้ว) จะสุ่มจากคลังทั้งหมดแทน
        เลี่ยงไม่ให้สุ่มข้อเดิมซ้ำติดกัน 2 ครั้งถ้ามีตัวเลือกมากกว่า 1 ข้อ"""
        data = self.manager.player_data
        wrong_ids = [i for i in (data.get("wrong_question_ids") or []) if i in content.QUESTION_MAP]
        # ลำดับความสำคัญ: ข้อบทเรียนที่เคยตอบผิด > ข้อ Challenger ที่เคยตอบผิด > โจทย์บทเรียนทั้งหมด
        # (โจทย์ Challenger ยากกว่าบทเรียนมาก จึงไม่ดึงมาให้ถ้ายังมีข้อบทเรียนให้ทบทวน)
        lesson_wrong = [i for i in wrong_ids if i in content.LESSON_QUESTION_IDS]
        pool = content.get_questions(lesson_wrong or wrong_ids) if (lesson_wrong or wrong_ids) \
            else content.lesson_questions()
        if not pool:
            pool = content.lesson_questions()  # กันไว้เผื่อคลังว่างจริง ๆ (ไม่ควรเกิดขึ้น)

        choices = [q for q in pool if q is not self._practice_question] if len(pool) > 1 else pool
        self._practice_question = random.choice(choices)
        self.questions = [self._practice_question]
        self.index = 0
        self._setup_question()

    def _current_question(self) -> content.Question:
        return self.questions[self.index]

    @staticmethod
    def _kind(q) -> str:
        """ชนิดช่องตอบของโจทย์: listen_mcq ใช้ช่องตอบแบบ mcq, listen_type ใช้ช่องพิมพ์แบบ translate_type"""
        return {"listen_mcq": "mcq", "listen_type": "translate_type"}.get(q.qtype, q.qtype)

    @staticmethod
    def _is_listening(q) -> bool:
        return q.qtype in ("listen_mcq", "listen_type")

    @staticmethod
    def _answer_audio(q) -> str:
        """ข้อความที่ใช้อ่านออกเสียงคำเฉลย: โจทย์ฟังใช้ audio_text (คำตอบอาจเป็นไทย) ส่วนข้ออื่นใช้คำตอบอังกฤษตามเดิม"""
        return q.audio_text or q.correct_answer

    def _has_answer(self) -> bool:
        q = self._current_question()
        kind = self._kind(q)
        if kind == "mcq":
            return self.selected_option is not None
        if kind == "word_order":
            return len(self.built_words) > 0
        if kind == "translate_type":
            return len(self.text_input.text.strip()) > 0
        return False

    def _submitted_answer_text(self) -> str:
        q = self._current_question()
        kind = self._kind(q)
        if kind == "mcq":
            return self.selected_option or ""
        if kind == "word_order":
            return " ".join(self.built_words)
        if kind == "translate_type":
            return self.text_input.text.strip()
        return ""

    def _check_answer(self):
        if self.phase != "answering" or not self._has_answer():
            return  # ป้องกันการตรวจคำตอบถ้ายังไม่ได้เลือก/กรอกคำตอบ

        q = self._current_question()
        self.was_correct = content.is_correct_answer(q, self._submitted_answer_text())  # รองรับคำตอบหลายรูปแบบ (ดู content.py)
        self.phase = "feedback"
        self.manager.sounds.speak(self._answer_audio(q), lang=content.LEARN_LANG)  # พูดออกเสียงคำตอบที่ถูกต้องให้ฟังทันทีหลังตรวจ (โจทย์ฟังใช้ audio_text)

        data = self.manager.player_data
        storage.record_answer(data, q.id, self.was_correct, content.unit_id_of_question(q.id))  # สถิติหน้าสถิติ

        if self.mode == "practice":
            # โหมดฝึกฝนฟื้นฟูหัวใจ: ไม่หักหัวใจ (หัวใจหมดอยู่แล้ว เป้าหมายคือฟื้นฟู ไม่ใช่ลงโทษซ้ำ)
            if self.was_correct:
                storage.remove_wrong_question(data, q.id)  # แก้ตัวสำเร็จ เอาออกจากคลังทบทวน
                self.practice_correct += 1
                self.manager.sounds.play_correct()
                burst_pos = (config.SCREEN_WIDTH // 2, 330)
                self.effects.spawn_confetti(burst_pos, count=16)
                self.mascot_mood = "excited"
                self.mascot_mood_timer = 1.2
                if self.practice_correct >= config.PRACTICE_CORRECT_TO_REGEN:
                    storage.regen_heart(data, config.PRACTICE_HEART_REWARD)
                    self.manager.toast.show(
                        f"ฟื้นฟูหัวใจสำเร็จ! ได้หัวใจคืนมา {config.PRACTICE_HEART_REWARD} ดวง 💛", duration=3.0)
            else:
                storage.record_wrong_question(data, q.id)  # ยังตอบผิดอยู่ วนอยู่ในคลังทบทวนต่อ
                self.manager.sounds.play_wrong()
                self.mascot_mood = "sad"
                self.mascot_mood_timer = 1.2
            self.manager.save()
            return  # โหมดฝึกฝนไม่มีทาง "หัวใจหมด" ซ้ำ (หัวใจหมดอยู่แล้วตั้งแต่ต้น) จึงไม่ต้องเช็ก out_of_hearts

        if self.was_correct:
            self.correct_count += 1
            self.xp_earned += config.XP_PER_CORRECT
            storage.add_xp(data, config.XP_PER_CORRECT)
            data["correct_today"] = data.get("correct_today", 0) + 1
            storage.remove_wrong_question(data, q.id)  # เคยตอบผิดข้อนี้มาก่อน แต่ตอนนี้ตอบถูกแล้ว ถือว่าแก้ตัวสำเร็จ
            if q.vocab:
                self.vocab_learned.append(q.vocab)
            self.manager.sounds.play_correct()

            # เอฟเฟกต์ฉลอง: คอนเฟตตี้ระเบิด + ข้อความ +XP ลอยขึ้น
            burst_pos = (config.SCREEN_WIDTH // 2, 330)
            self.effects.spawn_confetti(burst_pos, count=24)
            self.effects.spawn_floating_text(f"+{config.XP_PER_CORRECT} XP", burst_pos, config.COLOR_SECONDARY)
            self.mascot_mood = "excited"
            self.mascot_mood_timer = 1.2
        else:
            self.wrong_count += 1
            data["hearts"] = max(0, data.get("hearts", config.START_HEARTS) - 1)
            storage.record_wrong_question(data, q.id)  # จำไว้เป็นคลังสำหรับโหมดฝึกฝนฟื้นฟูหัวใจในอนาคต
            self.manager.sounds.play_wrong()
            self.mascot_mood = "sad"
            self.mascot_mood_timer = 1.2

        self.manager.save()

        if data.get("hearts", 0) <= 0:
            self.phase = "out_of_hearts"

    def _speak_choice(self, text):
        """อ่านออกเสียงคำ/ตัวเลือกที่ผู้เล่นเพิ่งกด (ก่อนกดตรวจคำตอบ) ช่วยให้ฝึกฟังไปด้วย
        - อ่านเฉพาะข้อความภาษาอังกฤษ (ตัวเลือกภาษาไทยข้าม เพราะเครื่องส่วนใหญ่ไม่มีเสียงไทย)
        - ถ้าปิดเสียง/ไม่มีระบบเสียงพูด จะเงียบไปเฉย ๆ ไม่เด้งแจ้งเตือน (กดบ่อย ๆ จะรำคาญ)
        - speak() ตัดเสียงเก่าที่ยังพูดค้างให้เอง กดรัว ๆ จึงได้ยินคำล่าสุดเสมอ"""
        if text and content.detect_lang(text) == content.LEARN_LANG and self._read_words_enabled():
            self.manager.sounds.speak(text, lang=content.LEARN_LANG)

    def _read_words_enabled(self) -> bool:
        return bool(self.manager.player_data.get("read_words_on_tap", True))

    def _toggle_read_words(self):
        """สลับเปิด/ปิดการอ่านคำที่กด แล้วบันทึกลงโปรไฟล์ ถ้าปิดระหว่างที่กำลังอ่านอยู่จะเงียบทันที"""
        data = self.manager.player_data
        data["read_words_on_tap"] = not self._read_words_enabled()
        if not data["read_words_on_tap"]:
            self.manager.sounds.stop_speech()
        self.manager.save()

    def _speak_prompt(self):
        """พูดทวนโจทย์ปัจจุบันซ้ำอีกครั้งตามที่ผู้เล่นกดขอฟัง (ปลอดภัย ไม่สปอยล์คำตอบ เพราะเป็นแค่โจทย์)
        โจทย์เป็นภาษาไทย จึงต้องใช้เสียงพูดภาษาไทย (lang="th") ถ้าเครื่องไม่มีเสียงไทยติดตั้งไว้จะไม่มีเสียง
        ออกมาเลย (ต่างจากคำตอบที่เป็นภาษาอังกฤษซึ่งเครื่อง Windows ส่วนใหญ่พูดได้อยู่แล้ว)"""
        q = self._current_question()
        if self._is_listening(q):
            self._replay_audio()  # โจทย์ฟัง: ปุ่ม "ฟังอีกครั้ง" เล่นเสียงของข้อนั้นซ้ำ ไม่อ่านคำสั่งโจทย์
            return
        text, lang = self._prompt_speech(q)
        spoke = self.manager.sounds.speak(text, lang=lang)
        if not spoke:
            if not self.manager.sounds.enabled:
                self.manager.toast.show("เสียงถูกปิดอยู่ (สามารถเปิดเสียงได้ที่หน้าตั้งค่า)")
            elif not self.manager.sounds.tts_available:
                self.manager.toast.show("ไม่พบระบบเสียงพูดในเครื่องนี้ (ลองติดตั้ง pyttsx3)")
            elif lang == "th" and not self.manager.sounds.thai_voice_available:
                self.manager.toast.show("เครื่องนี้ไม่มีเสียงพูดภาษาไทยติดตั้งไว้ จึงอ่านโจทย์ภาษาไทยไม่ได้ "
                                         "(ลองเพิ่มที่ Windows Settings > Time & Language > Speech)")

    def _replay_audio(self):
        """เล่นเสียงของโจทย์ฟังซ้ำ (ปุ่มลำโพงใหญ่ / ปุ่มซ้ายบน) ถ้าเล่นไม่ได้จะแจ้งสาเหตุและสลับไปโชว์ข้อความแทน"""
        q = self._current_question()
        if not self._is_listening(q):
            return
        spoke = self.manager.sounds.speak(q.audio_text, lang=content.LEARN_LANG)
        self.audio_unavailable = not spoke
        if not spoke:
            if not self.manager.sounds.enabled:
                self.manager.toast.show("เสียงถูกปิดอยู่ จึงแสดงคำที่ต้องฟังเป็นข้อความแทน")
            elif not self.manager.sounds.tts_available:
                self.manager.toast.show("ไม่พบระบบเสียงพูดในเครื่องนี้ จึงแสดงคำที่ต้องฟังเป็นข้อความแทน")
            elif content.LEARN_LANG == "th" and not self.manager.sounds.thai_voice_available:
                self.manager.toast.show("เครื่องนี้ไม่มีเสียงพูดภาษาไทยติดตั้งไว้ จึงอ่านโจทย์ภาษาไทยไม่ได้ "
                                         "(ลองเพิ่มที่ Windows Settings > Time & Language > Speech)")

    def _speak_current(self):
        """พูดออกเสียงคำ/ประโยคภาษาอังกฤษที่ถูกต้องของข้อนี้ (โชว์ปุ่มนี้เฉพาะหลังตอบแล้ว กันสปอยล์คำตอบ)"""
        q = self._current_question()
        spoke = self.manager.sounds.speak(self._answer_audio(q), lang=content.LEARN_LANG)
        if not spoke:
            if not self.manager.sounds.enabled:
                self.manager.toast.show("เสียงถูกปิดอยู่ (สามารถเปิดเสียงได้ที่หน้าตั้งค่า)")
            elif not self.manager.sounds.tts_available:
                self.manager.toast.show("ไม่พบระบบเสียงพูดในเครื่องนี้ (ลองติดตั้ง pyttsx3)")

    def _next_question(self):
        if self.phase == "out_of_hearts":
            return

        if self.mode == "practice":
            if self.practice_correct >= config.PRACTICE_CORRECT_TO_REGEN:
                # ฟื้นฟูหัวใจสำเร็จแล้ว - กลับไปเล่นบทเรียนเดิมต่อจากข้อที่ค้างไว้ตอนหัวใจหมดพอดี
                self.mode = "normal"
                self.questions = self._saved_normal_questions
                self.index = self._saved_normal_index
                self._saved_normal_questions = None
                self._setup_question()
            else:
                self._start_practice_question()  # ยังไม่ครบ สุ่มข้อทบทวนข้อถัดไป
            return

        self.index += 1
        if self.index >= len(self.questions):
            self._finish_lesson()
        else:
            self._setup_question()

    def _finish_lesson(self):
        data = self.manager.player_data
        bonus = config.XP_LESSON_BONUS
        storage.add_xp(data, bonus)
        self.xp_earned += bonus

        if self.lesson.id not in data.get("completed_lessons", []):
            data.setdefault("completed_lessons", []).append(self.lesson.id)
            data["lessons_finished_count"] = data.get("lessons_finished_count", 0) + 1
        data["lessons_today"] = data.get("lessons_today", 0) + 1

        perfect = (self.wrong_count == 0)
        newly_unlocked = achievements.check_achievements(data, perfect_lesson=perfect)

        self.manager.save()
        self.manager.sounds.play_lesson_complete()

        elapsed = int(time.time() - self.start_time)
        summary = {
            "lesson_title": self.lesson.title,
            "correct": self.correct_count,
            "wrong": self.wrong_count,
            "xp_earned": self.xp_earned,
            "elapsed_seconds": elapsed,
            "vocab_learned": self.vocab_learned,
            "newly_unlocked": newly_unlocked,
        }
        self.manager.go_to("summary", lesson_summary=summary, replay_unit=self.unit, replay_lesson=self.lesson)

    # -----------------------------------------------------------------
    def handle_event(self, event):
        self.quit_button.handle_event(event)

        if self.phase == "out_of_hearts":
            self.practice_button.handle_event(event)
            self.out_button.handle_event(event)
            return

        self.listen_prompt_button.handle_event(event)  # ฟังโจทย์ซ้ำได้ทุกเฟส (ไม่เกี่ยวกับคำตอบ)
        self.read_toggle_button.handle_event(event)    # เปิด/ปิดการอ่านคำที่กด (ทุกเฟส)
        if self._is_listening(self._current_question()):
            self.listen_big_button.handle_event(event)  # ปุ่มลำโพงใหญ่ของโจทย์ฟัง (ทุกเฟส)

        # กด Enter/Return ส่งคำตอบได้เลย (เหมือนกด "ตรวจคำตอบ") ถ้ายังไม่ได้ตอบจะไม่มีผล
        # ถ้าอยู่หน้าเฉลยแล้ว (feedback) กด Enter ซ้ำอีกทีจะไปข้อถัดไปให้เลย ไม่ต้องเอื้อมไปกดเมาส์
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.phase == "answering" and self._has_answer():
                self._check_answer()
            elif self.phase == "feedback":
                self._next_question()
            return

        q = self._current_question()

        if self.phase == "answering":
            kind = self._kind(q)
            if kind == "mcq":
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    for rect, option in self.mcq_option_rects:
                        if rect.collidepoint(event.pos):
                            self.selected_option = option
                            self.manager.sounds.play_click()
                            self._speak_choice(option)  # ได้ยินเสียงคำที่เลือกก่อนกดตรวจคำตอบ
            elif kind == "word_order":
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    for rect, word in self.word_tile_rects:
                        if rect.collidepoint(event.pos):
                            self.word_tiles.remove(word)
                            self.built_words.append(word)
                            self.manager.sounds.play_click()
                            self._speak_choice(word)  # ได้ยินเสียงคำที่กด ก่อนกดตรวจคำตอบ
                            break
                    else:
                        for rect, word in self.built_word_rects:
                            if rect.collidepoint(event.pos):
                                self.built_words.remove(word)
                                self.word_tiles.append(word)
                                self.manager.sounds.play_click()
                                self._speak_choice(word)
                                break
            elif kind == "translate_type":
                self.text_input.handle_event(event)

            self.check_button.set_disabled(not self._has_answer())
            self.check_button.handle_event(event)
        elif self.phase == "feedback":
            self.next_button.handle_event(event)
            self.speak_button.handle_event(event)

    def update(self, dt):
        self.time += dt
        self.text_input.update(dt)
        self.effects.update(dt)
        if self.lesson is not None:
            # พื้นหลังไล่สีนุ่ม ๆ ไปยังโทนของข้อปัจจุบัน (ข้อคี่/คู่สลับโทนกัน)
            target_top, target_bottom = content.lesson_background(self.lesson, self.index)
            k = min(1.0, dt * 5.0)
            self.bg_top_cur = config.lerp_color(self.bg_top_cur or target_top, target_top, k)
            self.bg_bottom_cur = config.lerp_color(self.bg_bottom_cur or target_bottom, target_bottom, k)
        if self.mascot_mood_timer > 0 and self.phase != "feedback":
            # ระหว่างดูเฉลย (feedback) มาสคอตค้างสีหน้าไว้ ไม่ให้ยิ้มกลับไปเองทั้งที่ยังเห็นข้อความ "ยังไม่ถูก" อยู่
            self.mascot_mood_timer -= dt
            if self.mascot_mood_timer <= 0:
                self.mascot_mood = "happy"

    # -----------------------------------------------------------------
    def _draw_mcq(self, surface, q):
        self.mcq_option_rects = []
        option_w, option_h = 360, 60
        start_y = 300
        for i, option in enumerate(self._visible_options(q)):
            col = i % 2
            row = i // 2
            x = config.SCREEN_WIDTH // 2 - option_w - 10 + col * (option_w + 20)
            y = start_y + row * (option_h + 16)
            rect = pygame.Rect(x, y, option_w, option_h)

            if self.phase == "feedback":
                is_correct_option = option.strip().lower() == q.correct_answer.strip().lower()
                if is_correct_option:
                    color = config.COLOR_SUCCESS
                elif option == self.selected_option:
                    color = config.COLOR_DANGER
                else:
                    color = config.COLOR_BG_LIGHT
            else:
                color = config.COLOR_ACCENT if option == self.selected_option else config.COLOR_BG_LIGHT

            pygame.draw.rect(surface, color, rect, border_radius=12)
            pygame.draw.rect(surface, config.COLOR_WHITE, rect, width=2, border_radius=12)
            # ตัวเลือกยาว: ลดขนาดฟอนต์/ขึ้นบรรทัดใหม่ให้อยู่ในกล่อง (สูงสุด 2 บรรทัด)
            font, lines = self._fit_wrapped(option, option_w - 24, 2, (20, 18, 16, 14))
            text_color = config.COLOR_WHITE if color != config.COLOR_BG_LIGHT else config.COLOR_TEXT
            line_h = font.get_linesize()
            top = rect.centery - line_h * len(lines) // 2
            for li, line in enumerate(lines):
                text = font.render(line, True, text_color)
                surface.blit(text, text.get_rect(midtop=(rect.centerx, top + li * line_h)))

            self.mcq_option_rects.append((rect, option))

    def _word_order_style(self, q):
        """เลือกขนาดฟอนต์/ระยะห่างของแผ่นคำ ให้ประโยคเฉลยทั้งประโยคพอดีแถวเดียวในกรอบ (ประโยคยาวในโจทย์ยาก ๆ)"""
        inner_w = 640 - 28
        words = q.correct_answer.split() or [""]
        for size, pad in ((20, 24), (18, 20), (16, 16), (14, 14)):
            font = config.get_font(size)
            total = sum(font.size(w)[0] + pad for w in words) + 10 * (len(words) - 1)
            if total <= inner_w:
                break
        return font, pad

    def _draw_word_order(self, surface, q):
        font, pad = self._word_order_style(q)
        left = config.SCREEN_WIDTH // 2 - 320
        right = config.SCREEN_WIDTH // 2 + 320

        # จัดตำแหน่งคำที่เลือกแล้ว (built sentence) - ถ้าล้นกรอบให้ขึ้นแถวใหม่ แล้วขยายกรอบลง
        row_h = 50
        placed, bx, row = [], left + 14, 0
        for word in self.built_words:
            w = font.size(word)[0] + pad
            if bx + w > right - 14 and bx > left + 14:
                bx, row = left + 14, row + 1
            placed.append((word, pygame.Rect(bx, 290 + 10 + row * row_h, w, 40)))
            bx += w + 10
        built_area = pygame.Rect(left, 290, 640, 60 + row * row_h)
        pygame.draw.rect(surface, config.COLOR_BG_LIGHT, built_area, border_radius=12)
        pygame.draw.rect(surface, config.COLOR_WHITE, built_area, width=2, border_radius=12)

        self.built_word_rects = []
        for word, rect in placed:
            color = config.COLOR_SUCCESS if self.phase == "feedback" and self.was_correct else config.COLOR_PRIMARY
            if self.phase == "feedback" and not self.was_correct:
                color = config.COLOR_DANGER
            pygame.draw.rect(surface, color, rect, border_radius=8)
            text = font.render(word, True, config.COLOR_WHITE)
            surface.blit(text, text.get_rect(center=rect.center))
            self.built_word_rects.append((rect, word))

        # คลังคำ (word bank) ที่ยังไม่ได้เลือก
        self.word_tile_rects = []
        tx = left
        ty = built_area.bottom + 30
        for word in self.word_tiles:
            w = font.size(word)[0] + pad
            if tx + w > right:
                tx = left
                ty += 54
            rect = pygame.Rect(tx, ty, w, 40)
            pygame.draw.rect(surface, config.COLOR_BG_LIGHT, rect, border_radius=8)
            pygame.draw.rect(surface, config.COLOR_WHITE, rect, width=1, border_radius=8)
            text = font.render(word, True, config.COLOR_TEXT)
            surface.blit(text, text.get_rect(center=rect.center))
            self.word_tile_rects.append((rect, word))
            tx += w + 10

    def _draw_translate_type(self, surface, q):
        label_font = config.get_font(16)
        label_text = "พิมพ์คำตอบเป็นภาษาอังกฤษ:" if q.prompt_lang == "en" else "พิมพ์คำแปลเป็นภาษาอังกฤษ:"
        label = label_font.render(label_text, True, config.COLOR_TEXT_MUTED)
        surface.blit(label, (self.text_input.rect.x, self.text_input.rect.y - 26))

        if self.phase == "feedback":
            border_color = config.COLOR_SUCCESS if self.was_correct else config.COLOR_DANGER
            pygame.draw.rect(surface, border_color, self.text_input.rect, width=3, border_radius=10)
        self.text_input.active = (self.phase == "answering")
        self.text_input.draw(surface)

    def _draw_listening_prompt(self, surface, q):
        """พื้นที่โจทย์ของโจทย์ฟัง: คำสั่งสั้น ๆ + ปุ่มลำโพงใหญ่ (ถ้าเล่นเสียงไม่ได้ จะโชว์คำเป็นข้อความแทน)"""
        cx = config.SCREEN_WIDTH // 2 - 30
        font, lines = self._fit_wrapped(q.prompt, 540, 1, (22, 20, 18, 16), bold=True)
        text = font.render(lines[0], True, config.COLOR_TEXT)
        surface.blit(text, text.get_rect(center=(cx, 182)))

        if self.audio_unavailable:
            word_font, word_lines = self._fit_wrapped(q.audio_text, 520, 1, (30, 26, 22, 18), bold=True)
            word = word_font.render(word_lines[0], True, config.COLOR_PRIMARY)
            surface.blit(word, word.get_rect(center=(cx, 226)))
            note = config.get_font(14).render("(เล่นเสียงไม่ได้ จึงแสดงเป็นข้อความแทน)", True, config.COLOR_TEXT_MUTED)
            surface.blit(note, note.get_rect(center=(cx, 254)))
            return

        self.listen_big_button.base_color = config.COLOR_PRIMARY
        self.listen_big_button.draw(surface)
        mascot.draw_achievement_icon(surface, self.listen_big_button.rect.center, 26, "speaker")

    def _draw_top_bar(self, surface):
        """แถบด้านบนของหน้าทำโจทย์ (แถบความคืบหน้า + หัวใจ)"""
        data = self.manager.player_data
        if self.mode == "practice":
            # โหมดฝึกฝนฟื้นฟูหัวใจ: แถบนี้โชว์ "ตอบถูกแล้วกี่ข้อจากเป้าหมาย" แทนความคืบหน้าปกติของบทเรียน
            # (สลับสีแถบเป็นเขียวชั่วคราวระหว่างวาด แล้วคืนค่าเดิม กันกระทบสีตอนกลับไปโหมดปกติ)
            original_fg = self.progress_bar.fg_color
            self.progress_bar.fg_color = config.COLOR_SUCCESS
            self.progress_bar.draw(
                surface, self.practice_correct / config.PRACTICE_CORRECT_TO_REGEN,
                label=f"🔥 ฝึกฝนฟื้นฟูหัวใจ: ตอบถูกแล้ว {self.practice_correct}/{config.PRACTICE_CORRECT_TO_REGEN}")
            self.progress_bar.fg_color = original_fg
        else:
            self.progress_bar.draw(surface, (self.index) / len(self.questions),
                                    label=f"ข้อ {self.index + 1}/{len(self.questions)}")
        self.hearts.draw(surface, data.get("hearts", config.START_HEARTS))

    def _display_mood(self) -> str:
        """อารมณ์ที่มาสคอตแสดงจริง: ปกติตามปฏิกิริยาล่าสุด แต่ตอนที่ยังไม่มีปฏิกิริยาและเหลือหัวใจดวงสุดท้าย ให้ทำหน้ากังวล"""
        if (self.mascot_mood == "happy" and self.mode == "normal"
                and self.manager.player_data.get("hearts", config.START_HEARTS) <= 1):
            return "worried"
        return self.mascot_mood

    def _feedback_text(self) -> str:
        return "ถูกต้อง!" if self.was_correct else "ยังไม่ถูกนะ"

    def _next_button_label(self) -> str:
        if self.mode == "practice" and self.practice_correct >= config.PRACTICE_CORRECT_TO_REGEN:
            return "กลับไปเรียนต่อ"
        return "ข้อถัดไป"

    @staticmethod
    def _fit_wrapped(text, max_width, max_lines, sizes, bold=False):
        """เลือกขนาดฟอนต์ที่ใหญ่ที่สุดใน sizes ที่ตัดบรรทัดแล้วไม่เกิน max_lines (ข้อความยาวจะค่อย ๆ ลดขนาดลง)
        คืนค่า (font, lines) - ใช้กับโจทย์/ตัวเลือก/คำอธิบายที่ยาวในโจทย์ระดับสูงของโหมด Challenger"""
        font, lines = None, []
        for size in sizes:
            font = config.get_font(size, bold)
            lines = LessonScreen._wrap_text(text, font, max_width)
            if len(lines) <= max_lines:
                break
        return font, lines

    @staticmethod
    def _wrap_text(text, font, max_width):
        """ตัดข้อความเป็นหลายบรรทัดตามช่องว่าง ให้แต่ละบรรทัดกว้างไม่เกิน max_width (โจทย์ไทยที่สั้นจะได้บรรทัดเดียวเหมือนเดิม)"""
        words = text.split(" ")
        lines, current = [], ""
        for word in words:
            trial = word if not current else current + " " + word
            if font.size(trial)[0] <= max_width or not current:
                current = trial
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def draw(self, surface):
        # พื้นหลังพาสเทลเปลี่ยนตามบทเรียน (ทุกบทสีไม่ซ้ำกัน) และสลับโทนไปมาทุกข้อย่อย
        if self.lesson is not None:
            fallback_top, fallback_bottom = content.lesson_background(self.lesson, self.index)
        else:
            fallback_top, fallback_bottom = config.COLOR_BG_TOP, config.COLOR_BG_BOTTOM
        theme_top = self.bg_top_cur or fallback_top
        theme_bottom = self.bg_bottom_cur or fallback_bottom
        fx.draw_gradient_background(surface, theme_top, theme_bottom)
        fx.draw_ambient_blobs(surface, self.time, tint=theme_top)
        data = self.manager.player_data

        if self.phase == "out_of_hearts":
            title_font = config.get_font(32, bold=True)
            text_font = config.get_font(18)
            mascot.draw_mascot(surface, (config.SCREEN_WIDTH // 2, 100), size=80, mood="sad", t=self.time)
            title = title_font.render("หัวใจหมดแล้ว!", True, config.COLOR_DANGER)
            surface.blit(title, title.get_rect(center=(config.SCREEN_WIDTH // 2, 220)))
            msg = text_font.render("ฝึกทบทวนคำที่เคยตอบผิด ตอบถูกครบ "
                                    f"{config.PRACTICE_CORRECT_TO_REGEN} ข้อ รับหัวใจคืนทันที!",
                                    True, config.COLOR_TEXT_DARK_MUTED)
            surface.blit(msg, msg.get_rect(center=(config.SCREEN_WIDTH // 2, 265)))
            msg2 = text_font.render("หรือพักไว้ก่อน หัวใจจะเต็มใหม่เองในวันถัดไป", True, config.COLOR_TEXT_DARK_MUTED)
            surface.blit(msg2, msg2.get_rect(center=(config.SCREEN_WIDTH // 2, 295)))
            self.practice_button.draw(surface)
            self.out_button.draw(surface)
            self.quit_button.draw(surface)
            return

        q = self._current_question()

        # แถบความคืบหน้า + หัวใจ (แยกเป็นเมธอด เพื่อให้โหมดจับเวลาสืบทอดแล้วเปลี่ยนเป็นแถบเวลาแทนได้)
        self._draw_top_bar(surface)
        self.quit_button.draw(surface)

        # การ์ดพื้นหลังคำถาม ให้ดูเป็นระเบียบและมีมิติแบบ UI สมัยใหม่
        card_rect = pygame.Rect(50, 110, config.SCREEN_WIDTH - 100, 420)
        fx.draw_card(surface, card_rect, radius=24)

        # มาสคอตเบลซคอยแสดงปฏิกิริยา (ยิ้ม/ตื่นเต้น/เศร้า) มุมขวาบนของการ์ด
        mascot.draw_mascot(surface, (card_rect.right - 55, card_rect.y + 55), size=70,
                            mood=self._display_mood(), t=self.time)

        # ปุ่มฟังโจทย์ซ้ำ (มุมซ้ายบนของการ์ด) - พูดทวนตัวคำถามให้ฟังได้ตลอด ไม่ใช่แค่ตอนเฉลย
        self.listen_prompt_button.draw(surface)
        mascot.draw_achievement_icon(
            surface, (self.listen_prompt_button.rect.x + 24, self.listen_prompt_button.rect.centery), 16, "speaker")

        # ปุ่มเปิด/ปิดอ่านคำที่กด: เขียว = เปิด, เทา = ปิด
        reading = self._read_words_enabled()
        self.read_toggle_button.text = "อ่านคำที่กด: เปิด" if reading else "อ่านคำที่กด: ปิด"
        self.read_toggle_button.base_color = config.COLOR_SUCCESS if reading else config.COLOR_BG_LIGHT
        self.read_toggle_button.hover_color = (60, 170, 110) if reading else config.COLOR_TEXT_MUTED
        self.read_toggle_button.text_color = config.COLOR_WHITE if reading else config.COLOR_TEXT
        self.read_toggle_button.draw(surface)

        self.listen_prompt_button.text = "   ฟังอีกครั้ง" if self._is_listening(q) else "   ฟังโจทย์"
        if self._is_listening(q):
            self._draw_listening_prompt(surface, q)
        else:
            # โจทย์ยาว (โหมด Challenger ระดับสูง) ลดขนาดฟอนต์ให้ไม่เกิน 3 บรรทัด จะได้ไม่ชนปุ่ม/ตัวเลือกด้านล่าง
            prompt_font, prompt_lines = self._fit_wrapped(q.prompt, 540, 3, (24, 21, 19, 17), bold=True)
            line_h = prompt_font.get_linesize()
            # โจทย์ 3 บรรทัดห้ามเลื่อนขึ้นไปชนปุ่ม "ฟังโจทย์" (ล่างสุดของปุ่ม = y 166) จึงกั้นบรรทัดแรกไว้ไม่ให้สูงกว่านี้
            first_y = max(200 - (len(prompt_lines) - 1) * line_h // 2, 170 + line_h // 2 + 4)
            for i, line in enumerate(prompt_lines):
                prompt = prompt_font.render(line, True, config.COLOR_TEXT)
                surface.blit(prompt, prompt.get_rect(center=(config.SCREEN_WIDTH // 2 - 30, first_y + i * line_h)))


        kind = self._kind(q)
        if kind == "mcq":
            self._draw_mcq(surface, q)
        elif kind == "word_order":
            self._draw_word_order(surface, q)
        elif kind == "translate_type":
            self._draw_translate_type(surface, q)

        if self.phase == "feedback":
            fb_color = config.COLOR_SUCCESS if self.was_correct else config.COLOR_DANGER
            fb_text = self._feedback_text()
            fb_font = config.get_font(22, bold=True)
            fb_surf = fb_font.render(fb_text, True, fb_color)
            surface.blit(fb_surf, fb_surf.get_rect(center=(config.SCREEN_WIDTH // 2, 450)))

            if q.explanation:
                # คำอธิบายยาว: ลดขนาดฟอนต์ก่อน ถ้ายังไม่พอค่อยขึ้นบรรทัดที่ 2 (ไม่ให้ล้นขอบ/ชนปุ่มข้อถัดไป)
                exp_font, exp_lines = self._fit_wrapped(q.explanation, config.SCREEN_WIDTH - 110, 2,
                                                         (16, 15, 14, 13))
                exp_h = exp_font.get_linesize()
                first = 478 - (len(exp_lines) - 1) * exp_h // 2
                for li, line in enumerate(exp_lines):
                    exp_surf = exp_font.render(line, True, config.COLOR_TEXT_MUTED)
                    surface.blit(exp_surf, exp_surf.get_rect(center=(config.SCREEN_WIDTH // 2, first + li * exp_h)))

            self.next_button.text = self._next_button_label()
            self.next_button.draw(surface)
            self.speak_button.draw(surface)
            # ไอคอนลำโพงวาดด้วยเวกเตอร์ (แทน emoji ที่บางฟอนต์ระบบแสดงเป็นกล่องว่าง)
            mascot.draw_achievement_icon(
                surface, (self.speak_button.rect.x + 26, self.speak_button.rect.centery), 20, "speaker")
        else:
            self.check_button.set_disabled(not self._has_answer())
            self.check_button.draw(surface)

        self.effects.draw(surface)  # คอนเฟตตี้ + ข้อความ +XP ลอย วาดทับบนสุดเสมอ
