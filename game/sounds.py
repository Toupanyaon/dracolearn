"""
sounds.py
---------
สังเคราะห์เสียงเอฟเฟกต์ทั้งหมดขึ้นเองด้วยคลื่นไซน์ผ่าน numpy
ทำให้โปรเจกต์รันได้ทันทีโดยไม่ต้องแนบไฟล์เสียงภายนอก
พร้อมระบบ Text-to-Speech (TTS) ออฟไลน์สำหรับออกเสียงคำศัพท์ภาษาอังกฤษ
รองรับทั้ง Windows SAPI5 โดยตรง และ pyttsx3 (macOS / Linux / Windows)
"""

import math
import queue
import re
import sys
import threading

import numpy as np
import pygame

SAMPLE_RATE = 44100


def _voice_supports_language(languages, name: str, voice_id: str, language: str) -> bool:
    if isinstance(languages, (str, bytes)):
        languages = [languages]

    metadata = []
    for value in languages or []:
        if isinstance(value, bytes):
            metadata.append(value.decode("utf-8", errors="replace"))
        else:
            metadata.append(str(value))
    metadata.extend((name, voice_id))
    searchable = " ".join(metadata).lower()
    language_name = {"en": "english", "th": "thai"}.get(language)
    if language_name and re.search(rf"(?<![a-z]){language_name}(?![a-z])", searchable):
        return True
    return bool(re.search(
        rf"(?<![a-z]){re.escape(language)}(?:[-_][a-z0-9]+)?(?![a-z])",
        searchable,
    ))


def _tone(frequency: float, duration_ms: int, volume: float = 0.5, wave: str = "sine") -> pygame.mixer.Sound:
    n_samples = int(SAMPLE_RATE * duration_ms / 1000)
    t = np.linspace(0, duration_ms / 1000, n_samples, endpoint=False)

    if wave == "square":
        signal = np.sign(np.sin(2 * np.pi * frequency * t))
    else:
        signal = np.sin(2 * np.pi * frequency * t)
        signal += 0.25 * np.sin(2 * np.pi * frequency * 2 * t)

    fade_len = max(1, int(n_samples * 0.06))
    envelope = np.ones(n_samples)
    envelope[:fade_len] = np.linspace(0, 1, fade_len)
    envelope[-fade_len:] = np.linspace(1, 0, fade_len) ** 2
    signal *= envelope

    signal = np.clip(signal * volume, -1, 1)
    audio = (signal * 32767).astype(np.int16)
    stereo = np.column_stack([audio, audio])
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))


def _sequence(notes, volume=0.5) -> pygame.mixer.Sound:
    """เรียงเสียงหลายโน้ตต่อกัน (สำหรับ jingle เช่น level up / achievement)"""
    chunks = []
    for freq, dur in notes:
        n_samples = int(SAMPLE_RATE * dur / 1000)
        t = np.linspace(0, dur / 1000, n_samples, endpoint=False)
        signal = np.sin(2 * np.pi * freq * t)
        fade_len = max(1, int(n_samples * 0.1))
        env = np.ones(n_samples)
        env[:fade_len] = np.linspace(0, 1, fade_len)
        env[-fade_len:] = np.linspace(1, 0, fade_len)
        chunks.append(signal * env)
    full = np.concatenate(chunks)
    full = np.clip(full * volume, -1, 1)
    audio = (full * 32767).astype(np.int16)
    stereo = np.column_stack([audio, audio])
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))


def _make_bgm() -> pygame.mixer.Sound:
    """สังเคราะห์เพลงพื้นหลังสั้น ๆ แบบวนลูป (คอร์ด C - Am - F - G เล่นโน้ตไล่ทีละตัวเบา ๆ)
    สร้างด้วยคลื่นไซน์ผ่าน numpy เหมือนเสียงเอฟเฟกต์อื่น จึงไม่ต้องแนบไฟล์เสียงภายนอก"""
    bpm = 96
    eighth = 60.0 / bpm / 2
    chords = [
        (261.63, 329.63, 392.00),   # C
        (220.00, 261.63, 329.63),   # Am
        (174.61, 220.00, 261.63),   # F
        (196.00, 246.94, 293.66),   # G
    ]
    pattern = [0, 1, 2, 1, 0, 1, 2, 1]
    steps_per_chord = len(pattern)
    total = int(SAMPLE_RATE * eighth * steps_per_chord * len(chords))
    buf = np.zeros(total)

    def add_note(start_sample, freq, length_s, amp):
        n = int(SAMPLE_RATE * length_s)
        t = np.arange(n) / SAMPLE_RATE
        wave = np.sin(2 * np.pi * freq * t) + 0.2 * np.sin(2 * np.pi * freq * 2 * t)
        attack = min(n, int(SAMPLE_RATE * 0.01))
        env = np.exp(-t * 3.2)
        env[:attack] *= np.linspace(0, 1, attack)
        note = wave * env * amp
        idx = (start_sample + np.arange(n)) % total   # ส่วนท้ายโน้ตวนกลับไปต้นเพลง ให้ลูปต่อกันเนียน
        np.add.at(buf, idx, note)

    for c_i, chord in enumerate(chords):
        chord_start = int(SAMPLE_RATE * eighth * steps_per_chord * c_i)
        add_note(chord_start, chord[0] / 2, eighth * steps_per_chord * 1.0, 0.30)   # เบสยาวทั้งคอร์ด
        for step, note_idx in enumerate(pattern):
            start = chord_start + int(SAMPLE_RATE * eighth * step)
            add_note(start, chord[note_idx] * 2, 0.9, 0.22)

    peak = float(np.max(np.abs(buf))) or 1.0
    buf = buf / peak * 0.8
    audio = (buf * 32767).astype(np.int16)
    stereo = np.column_stack([audio, audio])
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))


# แฟล็กของ SAPI SpVoice.Speak: พูดแบบ async (คืนค่าทันที) + ล้างคิว/ตัดเสียงเก่าก่อนพูดคำใหม่
_SVS_ASYNC = 1
_SVS_PURGE = 2


class SoundManager:
    """ศูนย์กลางเสียงเอฟเฟกต์และเสียงอ่านคำศัพท์ (TTS) ของเกม เปิด/ปิดเสียงได้จากหน้าตั้งค่า"""

    def __init__(self):
        self.enabled = True
        self.volume = 1.0          # ความดังเสียงเอฟเฟกต์เท่านั้น (ไม่รวมเสียงพูด)
        self.speech_volume = 1.0   # ความดังเสียงโจทย์/เสียงพูด (TTS) แยกอิสระ
        self.music_volume = 0.4    # ความดังเสียงพื้นหลัง (แยกอิสระ)
        self._music_playing = False
        # ตัวคูณความเร็วเสียงพูด (1.0 = ปกติ, 0.5 = ช้าลงครึ่งหนึ่ง, 1.5 = เร็วขึ้น 50%)
        # ต้องตั้งไว้ก่อนเริ่ม _tts_thread เพราะ _init_sapi/_init_pyttsx3 (รันใน worker thread)
        # จะอ่านค่านี้ไปตั้งความเร็วเริ่มต้นของเอนจินตั้งแต่ตอน init เลย
        self.speech_rate = 1.0
        self._pyttsx3_base_wpm = 160  # ความเร็วฐาน (คำ/นาที) ที่ถือว่าเป็น 1.0x ของ pyttsx3

        # --- ระบบออกเสียงคำศัพท์ภาษาอังกฤษ (Text-to-Speech) ---
        # 1. บน Windows: พยายามใช้ SAPI5 (SpVoice) โดยตรงผ่าน COM เพื่อความเสถียรสูงสุด
        #    ไม่เจอบั๊ก run loop / busy flag ของ pyttsx3 ทำให้พูดได้ต่อเนื่องทุกข้อ ไม่เงียบหาย
        # 2. macOS / Linux หรือ Fallback: ใช้ pyttsx3 พร้อมแก้ไขปัญหา proxy._busy
        #    เพื่อป้องกัน pyttsx3 หยุดทำงานหลังจากออกเสียงข้อแรก
        self._tts_queue = queue.Queue()
        self._tts_ready_event = threading.Event()
        self._tts_ready = False
        self._speaking = False
        self._engine_type = None  # "sapi" หรือ "pyttsx3"
        self._sapi_voice = None
        self._sapi_voice_en = None
        self._sapi_voice_th = None
        self._sapi_active_voice = None  # เสียงที่ตั้งไว้ใน SAPI ตอนนี้ (สลับเฉพาะเมื่อต่างจากเดิม ลดการเรียก COM)
        self._pyttsx3_engine = None
        self._pyttsx3_voice_en = None
        self._pyttsx3_voice_th = None
        # เก็บข้อความ error ล่าสุดไว้เสมอ (ทั้งตอน init และตอนพูดจริง) แทนการกลืน exception แบบเงียบ ๆ
        # เพื่อให้ debug ได้ว่าทำไมเสียงไม่ออก แทนที่จะไม่รู้อะไรเลย
        self._last_error = None
        self._speak_success_count = 0
        self._speak_fail_count = 0

        self._tts_thread = threading.Thread(target=self._tts_worker_loop, daemon=True)
        self._tts_thread.start()

        self.hover = _tone(880, 60, 0.30)
        self.click = _tone(520, 100, 0.45)
        self.correct = _sequence([(660, 90), (880, 140)], volume=0.5)
        self.wrong = _tone(180, 220, 0.45, wave="square")
        self.level_up = _sequence([(523, 100), (659, 100), (784, 100), (1047, 200)], volume=0.5)
        self.achievement = _sequence([(784, 90), (988, 90), (1175, 220)], volume=0.5)
        self.lesson_complete = _sequence([(659, 120), (784, 120), (988, 260)], volume=0.5)
        try:
            self.bgm = _make_bgm()
        except Exception:
            self.bgm = None   # สร้างเพลงพื้นหลังไม่ได้ก็ไม่ให้เกมล่ม แค่ไม่มีเพลง

    def _init_sapi(self) -> bool:
        if sys.platform != "win32":
            return False
        try:
            import pythoncom
            import win32com.client
            pythoncom.CoInitialize()
            voice = win32com.client.Dispatch("SAPI.SpVoice")
            voice.Rate = self._sapi_rate_from_multiplier(self.speech_rate)  # -10 ถึง 10
            voice.Volume = int(self.speech_volume * 100)

            # เสียง OneCore (เช่น Pattara ที่ติดตั้งผ่าน Windows Language settings) ไม่ถูกคืนมา
            # จาก SpVoice.GetVoices แม้จะส่ง VoiceCategory=OneCore จึงต้อง enumerate token จาก registry โดยตรง
            all_tokens = []
            try:
                for v in voice.GetVoices():
                    all_tokens.append(v)
            except Exception:
                pass
            for registry_path in (
                r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech_OneCore\Voices",
                r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Speech_OneCore\Voices",
            ):
                try:
                    category = win32com.client.Dispatch("SAPI.SpObjectTokenCategory")
                    category.SetId(registry_path, False)
                    tokens = category.EnumerateTokens()
                    for index in range(tokens.Count):
                        all_tokens.append(tokens.Item(index))
                except Exception:
                    pass  # OneCore voice category อาจไม่มีใน Windows บางรุ่น

            en_token, th_token = None, None
            for v in all_tokens:
                try:
                    desc = v.GetDescription()
                except Exception:
                    continue
                if th_token is None and _voice_supports_language((), desc, "", "th"):
                    th_token = v
                if en_token is None and (
                    _voice_supports_language((), desc, "", "en")
                    or any(name in desc.lower() for name in ("zira", "david"))
                ):
                    en_token = v
            if en_token is not None:
                voice.Voice = en_token
            self._sapi_active_voice = en_token
            self._sapi_voice = voice
            self._sapi_voice_en = en_token
            self._sapi_voice_th = th_token
            self._engine_type = "sapi"
            self._last_error = None
            return True
        except Exception as e:
            self._sapi_voice = None
            self._last_error = f"SAPI init failed: {type(e).__name__}: {e}"
            return False

    def _init_pyttsx3(self) -> bool:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", int(self._pyttsx3_base_wpm * self.speech_rate))
            engine.setProperty("volume", self.speech_volume)
            en_id, th_id = None, None
            for voice in engine.getProperty("voices") or []:
                name = getattr(voice, "name", "") or ""
                voice_id = getattr(voice, "id", "") or ""
                languages = getattr(voice, "languages", ()) or ()
                if th_id is None and _voice_supports_language(languages, name, voice_id, "th"):
                    th_id = voice.id
                if en_id is None and _voice_supports_language(languages, name, voice_id, "en"):
                    en_id = voice.id
            if en_id is not None:
                engine.setProperty("voice", en_id)
            self._pyttsx3_engine = engine
            self._pyttsx3_voice_en = en_id
            self._pyttsx3_voice_th = th_id
            self._engine_type = "pyttsx3"
            self._last_error = None
            return True
        except Exception as e:
            self._pyttsx3_engine = None
            self._last_error = f"pyttsx3 init failed: {type(e).__name__}: {e}"
            return False

    def _tts_worker_loop(self):
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except Exception:
            pythoncom = None

        sapi_error = None
        if self._init_sapi():
            self._tts_ready = True
        else:
            sapi_error = self._last_error
            if self._init_pyttsx3():
                self._tts_ready = True
            else:
                self._tts_ready = False
                pyttsx3_error = self._last_error
                self._last_error = (
                    f"ไม่พบระบบเสียงพูดในเครื่องนี้เลย - SAPI: {sapi_error} | pyttsx3: {pyttsx3_error}"
                )

        self._tts_ready_event.set()

        while True:
            item = self._tts_queue.get()
            if item is None:
                break
            text, lang = item

            if text is None:
                # คำสั่งหยุดพูด (stop_speech) - ทำในเธรดนี้เท่านั้น เพราะเรียก SAPI ข้ามเธรดจากหน้าจอเกมจะค้างรอจนเสียงเดิมอ่านจบ
                try:
                    if self._engine_type == "sapi" and self._sapi_voice:
                        self._sapi_voice.Speak("", _SVS_ASYNC | _SVS_PURGE)
                except Exception:
                    pass
                self._tts_queue.task_done()
                continue

            if self.enabled and self._tts_ready:
                self._speaking = True
                try:
                    if self._engine_type == "sapi" and self._sapi_voice:
                        # สลับเสียงพูดตามภาษาของข้อความก่อนพูดทุกครั้ง (th=เสียงไทยถ้ามี, en=เสียงอังกฤษ)
                        target_voice = self._sapi_voice_th if lang == "th" else self._sapi_voice_en
                        voice = self._sapi_voice
                        if target_voice is not None and target_voice is not self._sapi_active_voice:
                            voice.Voice = target_voice
                            self._sapi_active_voice = target_voice
                        # ความดัง/ความเร็วตั้งที่นี่ (เธรดนี้) ก่อนพูดทุกคำ ไม่ให้หน้าจอเกมไปแตะ COM ข้ามเธรดแล้วค้าง
                        voice.Volume = int(self.speech_volume * 100)
                        voice.Rate = self._sapi_rate_from_multiplier(self.speech_rate)
                        # พูดแบบ async + purge: เริ่มพูดคำนี้ทันทีและตัดคำเก่าที่ยังค้างอยู่ (กดคำรัว ๆ ไม่ต้องรอคำก่อนหน้าจบ)
                        voice.Speak(text, _SVS_ASYNC | _SVS_PURGE)
                        # รอจนพูดจบ แต่ถ้ามีคำใหม่เข้าคิวมาก็เลิกรอทันที แล้วคำใหม่จะตัดคำนี้เอง
                        while not voice.WaitUntilDone(30):
                            if not self._tts_queue.empty():
                                break
                    elif self._engine_type == "pyttsx3" and self._pyttsx3_engine:
                        target_voice_id = self._pyttsx3_voice_th if lang == "th" else self._pyttsx3_voice_en
                        if target_voice_id is not None:
                            self._pyttsx3_engine.setProperty("voice", target_voice_id)
                        self._pyttsx3_engine.setProperty("volume", self.speech_volume)
                        self._pyttsx3_engine.setProperty("rate", int(self._pyttsx3_base_wpm * self.speech_rate))
                        # บั๊กสำคัญของ pyttsx3: หลัง runAndWait จบ proxy._busy จะกลายเป็น False
                        # ทำให้คำสั่ง say ในครั้งถัดไปถูกลบและยกเลิกทันที (ทำให้พูดได้แค่ข้อแรกข้อเดียว)
                        # การตั้ง setBusy(True) ก่อน say ช่วยป้องกันไม่ให้ event loop ตัดจบก่อนพูด
                        if hasattr(self._pyttsx3_engine, "proxy"):
                            self._pyttsx3_engine.proxy.setBusy(True)
                        if hasattr(self._pyttsx3_engine, "_inLoop") and self._pyttsx3_engine._inLoop:
                            self._pyttsx3_engine._inLoop = False
                        self._pyttsx3_engine.say(text)
                        self._pyttsx3_engine.runAndWait()
                    # ถ้าไปถึงบรรทัดนี้โดยไม่ throw ถือว่าพูดสำเร็จ (นับไว้ทดสอบ/ดีบัก)
                    self._speak_success_count += 1
                    self._last_error = None
                except Exception as e:
                    # เดิมโค้ดกลืน exception นี้แบบเงียบ ๆ ทำให้ไม่มีทางรู้เลยว่าทำไมเสียงไม่ออก
                    # ตอนนี้เก็บข้อความ error ไว้ใน self._last_error ให้เรียกดูได้ (เช่นปุ่ม "ทดสอบเสียง")
                    self._speak_fail_count += 1
                    self._last_error = f"พูดไม่สำเร็จ ({self._engine_type}): {type(e).__name__}: {e}"
                    # Self-heal กู้คืนระบบเสียงอัตโนมัติหาก COM หลุด
                    if self._engine_type == "sapi":
                        self._init_sapi()
                    elif self._engine_type == "pyttsx3":
                        self._init_pyttsx3()
                finally:
                    self._speaking = False
            elif not self.enabled:
                pass  # ปิดเสียงอยู่ ไม่ถือว่าเป็นความล้มเหลว
            else:
                self._speak_fail_count += 1

            self._tts_queue.task_done()

        if pythoncom:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass

    def set_enabled(self, value: bool):
        self.enabled = value
        if not value:
            self.stop_speech()  # ปิดเสียงแล้วต้องเงียบทันที ไม่ปล่อยให้คำที่ค้างอยู่อ่านต่อ

    def _apply_music_volume(self):
        if getattr(self, "bgm", None) is not None:
            self.bgm.set_volume(self.music_volume * 0.6 if self.enabled else 0.0)

    def set_music_volume(self, value: float):
        """ตั้งความดังเสียงพื้นหลัง (0.0 - 1.0) ไม่กระทบเสียงเอฟเฟกต์/เสียงพูด"""
        self.music_volume = max(0.0, min(1.0, value))
        self._apply_music_volume()

    def start_music(self):
        """เริ่มเล่นเพลงพื้นหลังวนลูป (เรียกครั้งเดียวตอนเปิดเกม)"""
        if getattr(self, "bgm", None) is None or self._music_playing:
            return
        try:
            self._apply_music_volume()
            self.bgm.play(loops=-1)
            self._music_playing = True
        except Exception:
            pass

    def set_volume(self, value: float):
        """ตั้งระดับความดังเสียงเอฟเฟกต์ (0.0 - 1.0) มีผลเฉพาะเสียงเอฟเฟกต์ ไม่กระทบเสียงพูด (TTS) และเสียงพื้นหลัง"""
        self.volume = max(0.0, min(1.0, value))
        for snd in (self.hover, self.click, self.correct, self.wrong,
                    self.level_up, self.achievement, self.lesson_complete):
            snd.set_volume(self.volume)

    def set_speech_volume(self, value: float):
        """ตั้งความดังเสียงโจทย์/เสียงพูด TTS (0.0 - 1.0) ไม่กระทบเสียงเอฟเฟกต์และเสียงพื้นหลัง"""
        self.speech_volume = max(0.0, min(1.0, value))  # เอนจินจะอ่านค่านี้ไปตั้งเองก่อนพูดคำถัดไป (ดู _tts_worker_loop)

    @staticmethod
    def _sapi_rate_from_multiplier(multiplier: float) -> int:
        """แปลงตัวคูณความเร็ว (เช่น 0.5x, 1.5x) เป็นค่า Rate ของ SAPI5 (จำนวนเต็ม -10 ถึง 10)
        SAPI นิยามว่าทุก +10 = เร็วขึ้น 2 เท่า จึงใช้สูตร rate = 10 * log2(multiplier)"""
        value = 10 * math.log2(max(0.1, multiplier))
        return max(-10, min(10, round(value)))

    def set_speech_rate(self, multiplier: float):
        """ตั้งความเร็วเสียงพูด (ตัวคูณจากความเร็วปกติ เช่น 0.5, 0.75, 1.0, 1.25, 1.5)
        มีผลทันทีกับเอนจินที่ใช้งานอยู่ (ทั้ง SAPI5 และ pyttsx3) คำถัดไปที่พูดจะใช้ความเร็วใหม่นี้"""
        self.speech_rate = max(0.4, min(2.0, multiplier))  # เอนจินจะอ่านค่านี้ไปตั้งเองก่อนพูดคำถัดไป

    def stop_speech(self):
        """หยุดเสียงพูดปัจจุบันทันที (ไม่บล็อกหน้าจอเกม: ไม่เรียกเอนจินเสียงตรง ๆ จากเธรดนี้)"""
        while not self._tts_queue.empty():
            try:
                self._tts_queue.get_nowait()
                self._tts_queue.task_done()
            except queue.Empty:
                break
        if self._engine_type == "sapi" and self._sapi_voice:
            self._tts_queue.put((None, "stop"))   # ให้เธรดเสียงเป็นคนสั่งหยุดเอง
        else:
            self._interrupt_current_speech()

    def _interrupt_current_speech(self):
        """ตัดเสียงที่กำลังอ่านค้างอยู่แบบไม่รอ (SAPI: เธรดเสียงเลิกรอและคำใหม่ purge เองอยู่แล้ว ไม่ต้องทำอะไร;
        pyttsx3: สั่ง stop ในเธรดแยกเพราะ runAndWait บล็อกอยู่ ไม่ให้หน้าจอเกมต้องรอ)"""
        engine = self._pyttsx3_engine
        if self._engine_type == "pyttsx3" and engine is not None and self._speaking:
            def _stop():
                try:
                    engine.stop()
                except Exception:
                    pass
            threading.Thread(target=_stop, daemon=True).start()

    def _play(self, sound: pygame.mixer.Sound):
        if self.enabled:
            sound.play()

    def play_hover(self):
        self._play(self.hover)

    def play_click(self):
        self._play(self.click)

    def play_correct(self):
        self._play(self.correct)

    def play_wrong(self):
        self._play(self.wrong)

    def play_level_up(self):
        self._play(self.level_up)

    def play_achievement(self):
        self._play(self.achievement)

    def play_lesson_complete(self):
        self._play(self.lesson_complete)

    @property
    def tts_available(self) -> bool:
        if not self._tts_ready and not self._tts_ready_event.is_set():
            self._tts_ready_event.wait(timeout=1.0)
        return self._tts_ready

    @property
    def is_speaking(self) -> bool:
        return self._speaking

    @property
    def last_error(self):
        """ข้อความ error ล่าสุดจากระบบเสียงพูด (None ถ้ายังไม่เจอปัญหาอะไร) ใช้ debug ตอนเสียงไม่ออก"""
        return self._last_error

    @property
    def engine_type(self):
        """ชื่อเอนจินเสียงพูดที่ใช้งานอยู่จริง: 'sapi' | 'pyttsx3' | None (ยังไม่พร้อม/หาไม่เจอ)"""
        return self._engine_type

    @property
    def speak_stats(self):
        """จำนวนครั้งที่พูดสำเร็จ/ล้มเหลว สะสมตั้งแต่เปิดเกม ใช้ตรวจสอบว่าเสียงพูดทำงานจริงหรือไม่"""
        return {"success": self._speak_success_count, "fail": self._speak_fail_count}

    @property
    def thai_voice_available(self) -> bool:
        """มีเสียงพูดภาษาไทยติดตั้งในเครื่องนี้ไหม (เสียงพูดของ Windows ที่ติดมาส่วนใหญ่เป็นภาษาอังกฤษ
        เท่านั้น ถ้าไม่มีเสียงไทย การพูดประโยคภาษาไทยจะไม่มีเสียงออกมาเลยแม้ speak() จะไม่ error ก็ตาม)"""
        if self._engine_type == "sapi":
            return self._sapi_voice_th is not None
        if self._engine_type == "pyttsx3":
            return self._pyttsx3_voice_th is not None
        return False

    def speak(self, text: str, lang: str = "en") -> bool:
        """พูดออกเสียงข้อความที่ระบุ ทำงานใน background thread ไม่ให้เกมกระตุก
        lang="en" (ค่าเริ่มต้น) ใช้เสียงพูดภาษาอังกฤษ, lang="th" ใช้เสียงพูดภาษาไทยถ้ามีติดตั้งในเครื่อง
        คืนค่า True ถ้าเริ่มพูดจริง, False ถ้าปิดเสียงอยู่/ไม่มีระบบเสียงพูด/ไม่มีเสียงพูดภาษานั้น ๆ"""
        if not self.enabled or not text:
            return False

        if not self._tts_ready:
            if not self._tts_ready_event.wait(timeout=1.5):
                return False
            if not self._tts_ready:
                return False

        # เสียงพูดที่ติดมากับ Windows ส่วนใหญ่มีแต่ภาษาอังกฤษ ถ้าขอเสียงไทยแต่ไม่มีเสียงไทยติดตั้งไว้
        # จะไม่มีทางฟังรู้เรื่อง (มักจะเงียบหรือออกเสียงเพี้ยน) จึงตัดสินใจไม่พูดไปเลยดีกว่า แล้วให้ผู้เรียก
        # แจ้งผู้เล่นแทน (ผ่าน thai_voice_available) ดีกว่าพูดออกมาเป็นเสียงที่ฟังไม่ออก
        if lang == "th" and not self.thai_voice_available:
            return False

        # ล้างคิวที่อาจค้างอยู่ เพื่อพูดคำล่าสุดทันที
        while not self._tts_queue.empty():
            try:
                self._tts_queue.get_nowait()
                self._tts_queue.task_done()
            except queue.Empty:
                break

        # ถ้ากำลังพูดคำก่อนหน้าอยู่ ให้ตัดทันทีเพื่อเริ่มคำใหม่ (แบบไม่รอ - ดู _interrupt_current_speech)
        if self._speaking:
            self._interrupt_current_speech()

        self._tts_queue.put((text, lang))
        return True
