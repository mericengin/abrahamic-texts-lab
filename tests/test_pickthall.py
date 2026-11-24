"""Tests for the Pickthall reconciliation helpers and the verification helpers, on tiny hand-made strings."""
import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


pr = load("pickthall_reconcile")
pb = load("pickthall_build")
vf = load("verify")


class KeyTest(unittest.TestCase):
    def test_key_ignores_case_punctuation_spacing_and_accents(self):
        self.assertEqual(pr.key("A'ad, Thamud (the tribes)!"), pr.key("aad thamud the  tribes"))
        self.assertEqual(pr.key("Muāwiyah"), pr.key("muawiyah"))


class AlignmentTest(unittest.TestCase):
    def test_variants_find_a_changed_word_and_ignore_trailing_text(self):
        g = pr.key("We wronged them not but they did wrong themselves")
        scan = pr.key("We wronged them not but they did wrong themselves 58 THE COW")
        v, frac, lead, trail = pr.verse_variants(g, scan)
        self.assertEqual(v, [])
        self.assertGreater(frac, 0.95)
        g2 = pr.key("they wronged Us not but they did wrong themselves")
        v2, *_ = pr.verse_variants(g2, scan)
        self.assertTrue(v2)  # the different wording shows up as a variant

    def test_chain_links_unique_sequences_in_order(self):
        import random
        rnd = random.Random(1)
        base = "".join(rnd.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(400))
        scan = "xxxx" + base[:200] + "zz" + base[200:] + "yyyy"
        pairs = pr.chain(base, scan)
        self.assertGreater(len(pairs), 100)
        self.assertTrue(all(b1 < b2 and a1 < a2 for (a1, b1), (a2, b2) in zip(pairs, pairs[1:])))


class CleaningTest(unittest.TestCase):
    def test_running_headers_and_footnotes_are_removed_but_words_stay(self):
        raw = "Lo! evil is that which they do. VII THE HEIGHTS 159\n\n* i,e. a footnote that must not stay\nnot this line\n\n10. Next verse here.\n"
        out = pb.clean_raw(raw)
        self.assertNotIn("HEIGHTS", out)
        self.assertNotIn("footnote", out)
        self.assertIn("Lo! evil is that which they do.", out)
        self.assertIn("Next verse here.", out)

    def test_trim_tail_drops_text_after_the_verse_when_it_matches_to_the_end(self):
        text = "And We caused the white cloud to overshadow you. 58 the glorious koran sorah II"
        self.assertEqual(pb.trim_tail(text, "And We caused the white cloud to overshadow you."), "And We caused the white cloud to overshadow you.")


class AccuracyTest(unittest.TestCase):
    def test_wer_cer_counts_known_errors(self):
        we, nw, ce, nc = vf.wer_cer("Sprich: Siehe, ich sehe dich", "Sprich: Siebe, ih sehe dich")
        self.assertEqual((we, nw), (2, 5))
        self.assertEqual(nc, 22)
        self.assertEqual(ce, 2)

    def test_long_s_is_ignored(self):
        self.assertEqual(vf.wer_cer("Sonst wissen wir", "Sonſt wiſſen wir")[0], 0)


if __name__ == "__main__":
    unittest.main()
