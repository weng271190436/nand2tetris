"""Tests for the Project 10 Jack analyzer.

Each .jack file in the test directories generates ONE TestTokenizer test
(comparing against the corresponding *T.xml) and ONE TestParser test
(comparing against the corresponding *.xml).

Total: 14 tests (7 .jack files × 2 stages).
"""

from __future__ import annotations

import unittest
from pathlib import Path

from tokenizer import tokenize, token_to_xml
from parser import CompilationEngine


HERE = Path(__file__).resolve().parent

JACK_DIRS = [
    HERE / "ArrayTest",
    HERE / "ExpressionLessSquare",
    HERE / "Square",
]


def _read_lines(path: Path) -> list[str]:
    """Read a file's non-blank lines, stripped, for tolerant comparison."""
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def _all_jack_files() -> list[Path]:
    return [p for d in JACK_DIRS for p in sorted(d.glob("*.jack"))]


class TestTokenizer(unittest.TestCase):
    """Tokenizer comparison tests — methods are generated dynamically below."""


class TestParser(unittest.TestCase):
    """Parser comparison tests — methods are generated dynamically below."""


def _make_tokenizer_test(jack_path: Path):
    def test(self: unittest.TestCase) -> None:
        reference = jack_path.with_name(f"{jack_path.stem}T.xml")
        self.assertTrue(reference.exists(), f"Missing reference: {reference}")

        # Write to a temp path so we don't clobber the reference file.
        tmp_out = jack_path.with_name(f"{jack_path.stem}T.actual.xml")
        with tmp_out.open("w") as f:
            f.write("<tokens>\n")
            for tok in tokenize(jack_path):
                f.write(token_to_xml(tok) + "\n")
            f.write("</tokens>\n")

        try:
            self.assertEqual(_read_lines(tmp_out), _read_lines(reference))
        finally:
            tmp_out.unlink()

    return test


def _make_parser_test(jack_path: Path):
    def test(self: unittest.TestCase) -> None:
        reference = jack_path.with_suffix(".xml")
        self.assertTrue(reference.exists(), f"Missing reference: {reference}")

        tmp_out = jack_path.with_name(f"{jack_path.stem}.actual.xml")
        engine = CompilationEngine(jack_path, tmp_out)
        engine.compile()

        try:
            self.assertEqual(_read_lines(tmp_out), _read_lines(reference))
        finally:
            tmp_out.unlink()

    return test


# Generate one tokenizer test and one parser test per .jack file.
for _jack in _all_jack_files():
    _name = f"test_{_jack.parent.name}_{_jack.stem}"
    setattr(TestTokenizer, _name, _make_tokenizer_test(_jack))
    setattr(TestParser, _name, _make_parser_test(_jack))


if __name__ == "__main__":
    unittest.main()
