import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import henning_proofread as hp  # noqa: E402


class Candidates(unittest.TestCase):
    def test_lost_c_of_ch(self):
        self.assertIn("wahrlich", hp.candidates("wahrlih"))
        self.assertIn("schon", hp.candidates("shon"))

    def test_sharp_s_for_tz_and_ch(self):
        self.assertIn("setzen", hp.candidates("seßen"))
        self.assertIn("sprechen", hp.candidates("spreßen"))

    def test_b_read_for_h(self):
        self.assertIn("hinter", hp.candidates("binter"))

    def test_real_word_is_not_a_candidate_source_of_itself(self):
        self.assertNotIn("kein", hp.candidates("kein"))


if __name__ == "__main__":
    unittest.main()
