"""Tests for scripts/canon.py on tiny hand-made fixtures. Run: python3 -m unittest discover -s tests"""
import importlib.util
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("canon", Path(__file__).resolve().parent.parent / "scripts" / "canon.py")
canon = importlib.util.module_from_spec(spec)
sys.modules["canon"] = canon  # dataclasses needs the module registered
spec.loader.exec_module(canon)

OSIS_BOOK = """<?xml version="1.0" encoding="utf-8"?>
<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace"><osisText osisIDWork="WLC"><div type="book" osisID="Gen">
<chapter osisID="Gen.1">
<verse osisID="Gen.1.1"><w lemma="b/7225" morph="HR/Ncfsa" id="a">בְּ/רֵאשִׁ֖ית</w><w lemma="1254" id="b">בָּרָ֣א</w><seg type="x-sof-pasuq">׃</seg></verse>
<verse osisID="Gen.1.2"><w id="c">כָּל</w><seg type="x-maqqef">־</seg><w id="d">הָאָ֖רֶץ</w><w type="x-ketiv" id="e">הוצא</w><note type="variant"><catchWord>הוצא</catchWord><rdg type="x-qere"><w id="f">הַיְצֵ֣א</w></rdg></note><seg type="x-pe">פ</seg></verse>
</chapter></div></osisText></osis>"""

USFX = """<?xml version="1.0"?><usfx><book id="GEN"><h>Genesis</h>
<c id="1" /><p><v id="1" bcv="GEN.1.1" />In the <w s="H7225">beginning</w> God<f>a footnote that must not appear</f> created.<ve />
<v id="2" bcv="GEN.1.2" />The earth was <add>formless</add>.<ve /></p></book>
<book id="TOB"><h>Tobit</h><c id="1" /><p><v id="1" />A Deuterocanon verse.<ve /></p></book></usfx>"""

TANZIL_TXT = "1|1|بِسْمِ\n1|2|الْحَمْدُ\n2|1|الم\n\n#  Tanzil Quran Text\n#  License: Creative Commons Attribution 3.0\n"


class HebrewTest(unittest.TestCase):
    def test_slashes_removed_maqqef_joined_qere_added(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "wlc").mkdir()
            for code in canon.HB_ORDER:
                (Path(d) / "wlc" / f"{code}.xml").write_text(OSIS_BOOK if code == "Gen" else OSIS_BOOK.replace("Gen.", code + "."), encoding="utf-8")
            ver = canon.parse_hebrew(Path(d))
        rows = ver.books[0].rows
        self.assertEqual(rows[0], ("1", "1", "בְּרֵאשִׁ֖ית בָּרָ֣א׃"))
        self.assertEqual(rows[1][2], "כָּל־הָאָ֖רֶץ הוצא [הַיְצֵ֣א] {פ}")
        self.assertEqual(ver.stats["qere_added"], 39)  # one per fixture book


class UsfxTest(unittest.TestCase):
    def test_footnotes_and_strongs_removed_words_kept_deutero_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            z = Path(d) / "t.zip"
            with zipfile.ZipFile(z, "w") as zf:
                zf.writestr("t_usfx.xml", USFX)
            ver = canon.parse_usfx(z, "t_usfx.xml", "k", "Test", "English")
        gen, tob = ver.books
        self.assertEqual(gen.rows[0], ("1", "1", "In the beginning God created."))
        self.assertEqual(gen.rows[1][2], "The earth was formless.")
        self.assertTrue(tob.extra["deuterocanon"])
        self.assertFalse(gen.extra["deuterocanon"])


class TanzilTest(unittest.TestCase):
    def test_text_is_verbatim_and_notice_kept(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "q.txt"
            p.write_text(TANZIL_TXT, encoding="utf-8")
            ver = canon.parse_tanzil_txt(p, "q", "Test")
            self.assertEqual(ver.stats, {"suras": 2, "ayas": 3})
            self.assertEqual(ver.books[0].rows[1], ("1", "2", "الْحَمْدُ"))
            self.assertIn("Creative Commons Attribution 3.0", ver.notice)
            out = Path(d) / "md"
            canon.write_md(ver, out, {"source_id": "x"})
            self.assertIn("Tanzil notice", (out / "001.md").read_text(encoding="utf-8"))
            self.assertTrue(canon.roundtrip(ver, out)["ok"])


class RoundtripTest(unittest.TestCase):
    def test_roundtrip_detects_a_changed_verse(self):
        ver = canon.Version("k", "N", "English", "ltr", [canon.Book("01-A", "A", [("1", "1", "one"), ("1", "2", "two"), ("2", "1", "three")])])
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            canon.write_md(ver, out, {"source_id": "x"})
            self.assertTrue(canon.roundtrip(ver, out)["ok"])
            f = out / "01-A.md"
            f.write_text(f.read_text(encoding="utf-8").replace("**2** two", "**2** TWO"), encoding="utf-8")
            self.assertEqual(canon.roundtrip(ver, out)["books_with_differences"], ["01-A"])


if __name__ == "__main__":
    unittest.main()
