import unittest

from game.sounds import _voice_supports_language


class VoiceLanguageDetectionTests(unittest.TestCase):
    def test_detects_thai_voice_from_sapi_language_tag(self):
        self.assertTrue(_voice_supports_language((), "Microsoft Thai Voice", "", "th"))

    def test_detects_thai_voice_from_pyttsx3_language_bytes(self):
        self.assertTrue(_voice_supports_language([b"\x05th-TH"], "Voice", "voice-id", "th"))

    def test_detects_english_voice_from_language_tag(self):
        self.assertTrue(_voice_supports_language([b"\x05en-US"], "Voice", "voice-id", "en"))

    def test_does_not_match_language_code_inside_unrelated_text(self):
        self.assertFalse(_voice_supports_language((), "Heather", "some-voice", "th"))


if __name__ == "__main__":
    unittest.main()
