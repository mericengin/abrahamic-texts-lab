import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import henning_align as ha  # noqa: E402


class HenningNumbers(unittest.TestCase):
    def test_split_shifts_later_verses(self):
        # sura 8: standard verse 36 is two Henning verses; 37 becomes 38
        self.assertEqual(ha.henning_numbers(8, 35, 75), [35])
        self.assertEqual(ha.henning_numbers(8, 36, 75), [36, 37])
        self.assertEqual(ha.henning_numbers(8, 37, 75), [38])

    def test_merge_joins_two_verses(self):
        # sura 45: standard verses 1 and 2 are one Henning verse
        self.assertEqual(ha.henning_numbers(45, 1, 37), [1])
        self.assertEqual(ha.henning_numbers(45, 2, 37), [1])
        self.assertEqual(ha.henning_numbers(45, 3, 37), [2])

    def test_two_merges(self):
        # sura 101: (6,7) and (8,9) are each one verse
        self.assertEqual([ha.henning_numbers(101, v, 11) for v in (5, 6, 7, 8, 9, 10)], [[5], [6], [6], [7], [7], [8]])

    def test_unverified_tail_is_not_mapped(self):
        self.assertEqual(ha.henning_numbers(27, 64, 93), [65])
        self.assertIsNone(ha.henning_numbers(27, 65, 93))

    def test_unresolved_sura_is_not_mapped(self):
        self.assertIsNone(ha.henning_numbers(71, 5, 28))


if __name__ == "__main__":
    unittest.main()
