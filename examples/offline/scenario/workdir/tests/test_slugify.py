"""Unit tests for src/slugify.py.

They fail against the placeholder and pass once the spec in instruction.md
is implemented. From the working directory:

    python3 -m unittest discover -s tests
"""

import unittest

from src.slugify import slugify


class SlugifyTests(unittest.TestCase):
    def test_lowercases(self):
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_collapses_runs_to_one_dash(self):
        self.assertEqual(slugify("a  --  b"), "a-b")
        self.assertEqual(slugify("Hello? World!"), "hello-world")

    def test_strips_edges(self):
        self.assertEqual(slugify("  hello  "), "hello")
        self.assertEqual(slugify("--hello--"), "hello")

    def test_symbols_only_becomes_empty(self):
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify(""), "")

    def test_digits_survive(self):
        self.assertEqual(slugify("Shipyard v0.0.2!"), "shipyard-v0-0-2")


if __name__ == "__main__":
    unittest.main()
