"""Tests for scripts/to_markdown.py on tiny hand-made fixtures. Run: python3 -m unittest discover -s tests"""
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("to_markdown", Path(__file__).resolve().parent.parent / "scripts" / "to_markdown.py")
tm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tm)

# Mimics the Gutenberg #16955 layout, including a corrupted verse id (0.003) as in the real file.
FIXTURE = (
    "header\r\n\r\n Chapter 1:\r\n\r\n   AL-FATIHA (THE OPENING)\r\n Total Verses: 3 Revealed At: MAKKA\r\n\r\n"
    "-----\r\n\r\n001.001\r\nY: Yusuf one.\r\n\r\nP: Pickthall one.\r\n\r\nS: Shakir one.\r\n\r\n"
    "001.002\r\nY: Yusuf two.\r\n\r\nP: Pickthall two\r\nwraps here.\r\n\r\nS: Shakir two.\r\n\r\n"
    "0.003\r\nY: Yusuf three.\r\n\r\nP: Pickthall three.\r\n\r\nS: Shakir three.\r\n"
)


class QualityTest(unittest.TestCase):
    def test_normal_english_is_good(self):
        text = "And the angels said that they are those who were not with his people and they sought thee for the work " * 5
        self.assertEqual(tm.ocr_quality(text, "English")["flag"], "good")

    def test_fraktur_misread_is_unusable(self):
        junk = "3)er Koran übertragen unö ©erfel^en pon ZHaf fjenning Dcriag Hcciam Cctpjig " * 20
        self.assertEqual(tm.ocr_quality(junk, "German")["flag"], "unusable")


class ConversionTest(unittest.TestCase):
    def test_plain_text_is_lossless_and_crlf_normalized(self):
        body, _, checks = tm.convert_text("a  b\r\nc\r\n")
        self.assertEqual(body, "a  b\nc\n")
        self.assertTrue(checks["lossless"])

    def test_three_translations_adds_structure_without_changing_words(self):
        body, _, checks = tm.convert_three_translations(FIXTURE)
        self.assertIn("## Chapter 1:", body)
        self.assertIn("#### 001.001", body)
        self.assertIn("**P:** Pickthall one.", body)
        self.assertTrue(checks["lossless"])

    def test_pickthall_extraction_repairs_corrupted_id_and_joins_wrapped_lines(self):
        md, stats = tm.extract_pickthall(FIXTURE)
        self.assertIn("**1:2** Pickthall two wraps here.", md)
        self.assertIn("**1:3** Pickthall three.", md)  # id "0.003" repaired from the sequence
        self.assertNotIn("Yusuf", md)
        self.assertNotIn("Shakir", md)
        self.assertEqual(stats["verses_found"], 3)
        self.assertEqual(stats["verses_expected_from_headers"], 3)
        self.assertEqual(stats["repaired_corrupted_verse_ids"][0]["assigned"], "1:3")
        self.assertEqual(stats["suras_with_count_mismatch"], {})


if __name__ == "__main__":
    unittest.main()


class OcrHelpersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import sys
        s = importlib.util.spec_from_file_location("ocr_to_markdown", Path(__file__).resolve().parent.parent / "scripts" / "ocr_to_markdown.py")
        cls.om = importlib.util.module_from_spec(s)
        sys.modules["ocr_to_markdown"] = cls.om
        s.loader.exec_module(cls.om)

    def test_candidates_cover_fraktur_slips(self):
        c = self.om.candidates
        self.assertIn("nicht", c("niht"))    # ch read as h
        self.assertIn("nicht", c("nict"))    # ch read as c
        self.assertIn("nicht", c("uicht"))   # u/n swap
        self.assertIn("sich", c("sih"))      # ih -> ich

    def test_common_score_separates_german_from_junk(self):
        good = "Und die da glauben an das was auf dich herabgesandt ward und nicht ist sie von den Menschen " * 5
        junk = "3)er Koran übertragen unö ©erfel^en pon ZHaf fjenning Dcriag Hcciam Cctpjig " * 5
        self.assertGreater(self.om.common_score(good), 150)
        self.assertLess(self.om.common_score(junk), 80)
