"""Unit tests for src/stats.py.

They fail against the shipped bugs and pass once the spec in instruction.md
is implemented. From the working directory:

    python3 -m unittest discover -s tests
"""

import unittest

from src.stats import mean, median, mode


class MeanTests(unittest.TestCase):
    def test_exact_mean(self):
        self.assertAlmostEqual(mean([1, 2, 4]), 7 / 3)

    def test_single_value(self):
        self.assertAlmostEqual(mean([5]), 5.0)


class MedianTests(unittest.TestCase):
    def test_odd_count(self):
        self.assertEqual(median([7, 1, 3]), 3)

    def test_even_count_averages_the_middle_two(self):
        self.assertEqual(median([1, 2, 3, 4]), 2.5)
        self.assertEqual(median([4, 3, 2, 1]), 2.5)


class ModeTests(unittest.TestCase):
    def test_clear_winner(self):
        self.assertEqual(mode([2, 2, 1]), 2)

    def test_tie_resolves_to_smallest(self):
        self.assertEqual(mode([3, 1, 3, 1]), 1)


if __name__ == "__main__":
    unittest.main()
