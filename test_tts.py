# -*- coding: utf-8 -*-
"""
test_tts.py
-----------
สคริปต์ทดสอบระบบเสียงพูด (Text-to-Speech) แบบสแตนด์อโลน แยกจากตัวเกมโดยสิ้นเชิง
ไม่ต้องใช้ pygame เลย รันตรง ๆ เพื่อดูว่าเครื่องนี้พูดได้จริงหรือไม่ และถ้าไม่ได้ ทำไมถึงไม่ได้

วิธีรัน:
    python test_tts.py

สคริปต์นี้จะลองทีละขั้นตอน พิมพ์ผลลัพธ์ทุกขั้นตอนออกมาให้เห็นชัด ๆ
(ต่างจากในเกมที่ error บางอย่างอาจถูกซ่อนไว้) ถ้าขั้นไหนพัง จะเห็น error เต็ม ๆ ทันที
"""

import platform
import sys
import time
import traceback


def line():
    print("-" * 70)


def main():
    print("=" * 70)
    print("TTS DIAGNOSTIC TEST - DracoLearn")
    print("=" * 70)
    print(f"Python version : {sys.version}")
    print(f"Platform       : {platform.platform()}")
    print(f"Is Windows     : {sys.platform == 'win32'}")
    line()

    sapi_ok = False
    pyttsx3_ok = False

    # -----------------------------------------------------------------
    # STEP 1: ทดสอบ SAPI5 โดยตรงผ่าน pywin32 (เฉพาะ Windows เท่านั้น)
    # -----------------------------------------------------------------
    print("[STEP 1] Testing Windows SAPI5 (via pywin32)...")
    if sys.platform != "win32":
        print("  -> SKIPPED (not running on Windows)")
    else:
        try:
            import pythoncom
            print("  [OK] pythoncom imported")
            import win32com.client
            print("  [OK] win32com.client imported")

            pythoncom.CoInitialize()
            print("  [OK] CoInitialize() succeeded")

            voice = win32com.client.Dispatch("SAPI.SpVoice")
            print("  [OK] SAPI.SpVoice created")

            voices = voice.GetVoices()
            count = voices.Count
            print(f"  [OK] Found {count} installed voice(s):")
            if count == 0:
                print("       !! NO VOICES INSTALLED !! This is very likely why TTS fails.")
                print("       Fix: Windows Settings > Time & Language > Speech > Manage voices > Add voices")
            for i in range(count):
                desc = voices.Item(i).GetDescription()
                print(f"         [{i}] {desc}")

            voice.Rate = 0
            voice.Volume = 100

            print("  Attempting voice.Speak('Hello, this is a test.') ... (should hear it NOW)")
            voice.Speak("Hello, this is a test.", 0)  # 0 = synchronous, blocks until finished
            print("  [OK] Speak() call returned without raising an exception.")
            print("  >>> Did you actually HEAR audio just now? If not, see notes at the bottom. <<<")
            sapi_ok = True

        except Exception:
            print("  [FAIL] SAPI5 raised an exception:")
            traceback.print_exc()
            print()
            print("  Common causes:")
            print("   - pywin32 not installed correctly -> pip install pywin32")
            print("   - pywin32 post-install step not run -> run:")
            print("       python -m pywin32_postinstall -install")
            print("     (may need to run PowerShell/cmd as Administrator)")

    line()

    # -----------------------------------------------------------------
    # STEP 2: ทดสอบ pyttsx3 (ทำงานได้ทั้ง Windows / macOS / Linux)
    # -----------------------------------------------------------------
    print("[STEP 2] Testing pyttsx3...")
    try:
        import pyttsx3
        print("  [OK] pyttsx3 imported")

        engine = pyttsx3.init()
        print("  [OK] pyttsx3.init() succeeded")

        voices = engine.getProperty("voices") or []
        print(f"  [OK] Found {len(voices)} installed voice(s):")
        if not voices:
            print("       !! NO VOICES FOUND !! This is very likely why TTS fails.")
        for v in voices:
            print(f"         - {v.id}  (name={getattr(v, 'name', '?')})")

        engine.setProperty("rate", 160)
        engine.setProperty("volume", 1.0)

        print("  Attempting engine.say(...) + runAndWait() ... (should hear it NOW)")
        engine.say("Hello, this is a test.")
        engine.runAndWait()
        print("  [OK] runAndWait() completed without raising an exception.")
        print("  >>> Did you actually HEAR audio just now? If not, see notes at the bottom. <<<")
        pyttsx3_ok = True

    except ImportError:
        print("  [FAIL] pyttsx3 is not installed.")
        print("  Fix: pip install pyttsx3")
    except Exception:
        print("  [FAIL] pyttsx3 raised an exception:")
        traceback.print_exc()

    line()

    # -----------------------------------------------------------------
    # สรุปผล
    # -----------------------------------------------------------------
    print("SUMMARY")
    print(f"  SAPI5 (Windows)  : {'WORKS (no exceptions)' if sapi_ok else 'FAILED / SKIPPED'}")
    print(f"  pyttsx3          : {'WORKS (no exceptions)' if pyttsx3_ok else 'FAILED / SKIPPED'}")
    print()
    if not sapi_ok and not pyttsx3_ok:
        print("Neither engine worked. The game's TTS will not function until one of these")
        print("is fixed. Copy the FULL error output above (especially the traceback) and")
        print("send it back - that tells us exactly what to fix.")
    else:
        print("At least one engine ran without raising an exception.")
        print("IMPORTANT: if you did NOT actually hear any sound just now, the problem is")
        print("likely NOT the Python code - check these instead:")
        print("  1. Is your system volume muted, or the wrong output device selected?")
        print("  2. Windows Settings > Time & Language > Speech - is a voice installed")
        print("     and is the 'Speech Output' set to your active speakers/headphones?")
        print("  3. Try Windows Narrator (Win+Ctrl+Enter) - if Narrator is also silent,")
        print("     it's a Windows/audio-device issue, not this game.")
    line()
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
