"""ทดสอบว่าเสียงอ่านคำ "ไม่บล็อกหน้าจอเกม" เวลากดคำรัว ๆ (รัน: python -m unittest test_speech_responsiveness -v)

จำลอง SAPI ด้วยวัตถุปลอมที่เลียนพฤติกรรม COM: เรียกข้ามเธรดขณะอีกเธรดกำลัง Speak แบบ sync จะต้องรอจนพูดจบ
(นี่คือสาเหตุเดิมที่เกมค้างตอนกดคำไว ๆ) ไม่ต้องมีเสียง/หน้าต่างจริง
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import queue
import threading
import time
import unittest

from game import sounds as sounds_module
from game.sounds import SoundManager

SPEAK_SECONDS = 0.4   # เวลาที่คำหนึ่งคำ "อ่านจบ" ในการจำลอง


class FakeSapiVoice:
    """เลียนแบบ SAPI.SpVoice แบบ apartment-threaded: ล็อกจะถูกถือไว้ตลอดช่วง Speak แบบ sync (flags ไม่มี async)
    ส่วน WaitUntilDone ปล่อยล็อกระหว่างรอ (เหมือน COM ที่ pump message) และ Speak async คืนค่าทันที"""

    def __init__(self):
        self.apartment = threading.RLock()
        self.calls = []          # (text, flags)
        self.spoken_until = 0.0
        self.current = None
        self.finished = []       # คำที่พูดจนจบจริง ๆ (ไม่ถูกตัด)
        self.Volume = 100
        self.Rate = 0
        self.Voice = None

    def Speak(self, text, flags=0):
        with self.apartment:
            self.calls.append((text, flags))
            if flags & 2:                      # purge: ตัดคำเก่า
                self.current, self.spoken_until = None, 0.0
            if not text:
                return 0
            if flags & 1:                      # async: คืนค่าทันที
                self.current = text
                self.spoken_until = time.time() + SPEAK_SECONDS
                return 0
            time.sleep(SPEAK_SECONDS)          # sync: บล็อกพร้อมถือล็อก
            self.finished.append(text)
            return 0

    def WaitUntilDone(self, ms):
        deadline = time.time() + ms / 1000.0
        while time.time() < deadline:
            with self.apartment:
                if self.current is None or time.time() >= self.spoken_until:
                    if self.current is not None:
                        self.finished.append(self.current)
                        self.current = None
                    return True
            time.sleep(0.002)
        return False


class TtsOnly(SoundManager):
    """SoundManager เฉพาะส่วนเสียงพูด (ไม่สร้างเสียงเอฟเฟกต์/เพลง) ต่อกับ SAPI ปลอม"""

    def __init__(self):
        self.enabled = True
        self.speech_volume = 1.0
        self.speech_rate = 1.0
        self._pyttsx3_base_wpm = 160
        self._tts_queue = queue.Queue()
        self._tts_ready_event = threading.Event()
        self._tts_ready = False
        self._speaking = False
        self._engine_type = None
        self._sapi_voice = None
        self._sapi_voice_en = None
        self._sapi_voice_th = None
        self._sapi_active_voice = None
        self._pyttsx3_engine = None
        self._pyttsx3_voice_en = None
        self._pyttsx3_voice_th = None
        self._last_error = None
        self._speak_success_count = 0
        self._speak_fail_count = 0
        threading.Thread(target=self._tts_worker_loop, daemon=True).start()
        self._tts_ready_event.wait(2)

    def _init_sapi(self):
        self._sapi_voice = FakeSapiVoice()
        self._engine_type = "sapi"
        return True


class SpeechResponsivenessTests(unittest.TestCase):
    def setUp(self):
        self.sm = TtsOnly()
        self.voice = self.sm._sapi_voice

    def _timed(self, fn, *args):
        start = time.perf_counter()
        fn(*args)
        return time.perf_counter() - start

    def test_speak_returns_immediately_even_while_a_word_is_playing(self):
        self.sm.speak("apple")
        time.sleep(0.05)  # ให้เริ่มพูดแล้ว
        for word in ("banana", "orange", "grape", "mango"):
            self.assertLess(self._timed(self.sm.speak, word), 0.05, word)

    def test_rapid_taps_only_the_last_word_is_finished(self):
        for word in ("one", "two", "three", "four", "five"):
            self.sm.speak(word)
            time.sleep(0.01)   # กดรัว ๆ ห่างกันแค่ 10 มิลลิวินาที
        time.sleep(SPEAK_SECONDS + 0.4)
        self.assertEqual(self.voice.finished[-1:], ["five"])
        self.assertNotIn("one", self.voice.finished)
        self.assertNotIn("two", self.voice.finished)

    def test_every_speak_call_is_async_and_purges(self):
        self.sm.speak("hello")
        time.sleep(0.1)
        self.assertTrue(self.voice.calls)
        for text, flags in self.voice.calls:
            self.assertEqual(flags & 3, 3, f"{text!r} ไม่ใช่ async+purge")

    def test_stop_speech_does_not_block_the_caller(self):
        self.sm.speak("long")
        time.sleep(0.05)
        self.assertLess(self._timed(self.sm.stop_speech), 0.05)
        time.sleep(0.2)
        self.assertIsNone(self.voice.current)   # เสียงถูกตัดจริง

    def test_turning_sound_off_silences_immediately_without_blocking(self):
        self.sm.speak("hello")
        time.sleep(0.05)
        self.assertLess(self._timed(self.sm.set_enabled, False), 0.05)
        time.sleep(0.2)
        self.assertIsNone(self.voice.current)

    def test_volume_and_rate_changes_never_touch_the_engine_from_caller_thread(self):
        self.sm.speak("hi")
        time.sleep(0.05)
        calls_before = len(self.voice.calls)
        self.assertLess(self._timed(self.sm.set_speech_volume, 0.5), 0.05)
        self.assertLess(self._timed(self.sm.set_speech_rate, 1.5), 0.05)
        self.sm.speak("next")
        time.sleep(0.1)
        self.assertEqual(self.voice.Volume, 50)       # ถูกนำไปตั้งก่อนพูดคำถัดไป
        self.assertEqual(self.voice.Rate, self.sm._sapi_rate_from_multiplier(1.5))
        self.assertGreater(len(self.voice.calls), calls_before)

    def test_disabled_sound_does_not_speak(self):
        self.sm.enabled = False
        self.assertFalse(self.sm.speak("hello"))

    def test_speaks_again_normally_after_stop(self):
        self.sm.speak("first")
        time.sleep(0.05)
        self.sm.stop_speech()
        time.sleep(0.1)
        self.sm.speak("second")
        time.sleep(SPEAK_SECONDS + 0.3)
        self.assertEqual(self.voice.finished[-1:], ["second"])


if __name__ == "__main__":
    unittest.main()
