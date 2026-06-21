"""Tests for the Project 10 Jack analyzer.

- TestTokenizer compares our flat-token XML against the course-provided
  <Name>T.xml reference files. Whitespace is normalized to per-line tokens
  so we tolerate trailing newlines / minor formatting differences.
- TestParser is left as a placeholder until CompilationEngine is implemented.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from jack_analyzer import write_token_xml


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
    def tearDown(self) -> None:
        for jack in _all_jack_files():
            out = jack.with_name(f"{jack.stem}T.xml")
            # Only remove if it was created by our run (matches our name pattern)
            # and isn't one of the reference XML files we want to preserve.
            # Reference files are named exactly the same, so we restore from disk
            # by not deleting — comparisons are read-only against the reference
            # files in their original location. We don't write over them because
            # write_token_xml writes to a freshly-derived path. But that path
            # IS the same as the reference. So we DO overwrite during the test.
            # To avoid stomping reference files, we instead write to a temp dir.
            pass

    def _compare_tokens(self, jack_path: Path) -> None:
        # Reference file lives next to the .jack file with the T.xml suffix.
        reference = jack_path.with_name(f"{jack_path.stem}T.xml")
        self.assertTrue(reference.exists(), f"Missing reference: {reference}")

        # Generate our output to a temp location so we don't clobber the reference.
        tmp_out = jack_path.with_name(f"{jack_path.stem}T.actual.xml")
        # write_token_xml writes to <stem>T.xml; we'll re-route by writing manually.
        from tokenizer import tokenize, token_to_xml

        with tmp_out.open("w") as f:
            f.write("<tokens>\n")
            for tok in tokenize(jack_path):
                f.write(token_to_xml(tok) + "\n")
            f.write("</tokens>\n")

        try:
            actual = _read_lines(tmp_out)
            expected = _read_lines(reference)
            self.assertEqual(actual, expected, f"Mismatch for {jack_path.name}")
        finally:
            tmp_out.unlink()

    def test_array_test(self) -> None:
        for jack in sorted((HERE / "ArrayTest").glob("*.jack")):
            with self.subTest(jack=jack.name):
                self._compare_tokens(jack)

    def test_expressionless_square(self) -> None:
        for jack in sorted((HERE / "ExpressionLessSquare").glob("*.jack")):
            with self.subTest(jack=jack.name):
                self._compare_tokens(jack)

    def test_square(self) -> None:
        for jack in sorted((HERE / "Square").glob("*.jack")):
            with self.subTest(jack=jack.name):
                self._compare_tokens(jack)


class TestParser(unittest.TestCase):
    """Compare our parse-tree XML against the course-provided reference files."""

    def _compare_parse(self, jack_path: Path) -> None:
        reference = jack_path.with_suffix(".xml")
        self.assertTrue(reference.exists(), f"Missing reference: {reference}")

        # Write to a temp path so we don't clobber the reference file.
        tmp_out = jack_path.with_name(f"{jack_path.stem}.actual.xml")
        from parser import CompilationEngine

        engine = CompilationEngine(jack_path, tmp_out)
        engine.compile()

        try:
            actual = _read_lines(tmp_out)
            expected = _read_lines(reference)
            self.assertEqual(actual, expected, f"Mismatch for {jack_path.name}")
        finally:
            tmp_out.unlink()

    def test_array_test(self) -> None:
        for jack in sorted((HERE / "ArrayTest").glob("*.jack")):
            with self.subTest(jack=jack.name):
                self._compare_parse(jack)

    def test_expressionless_square(self) -> None:
        for jack in sorted((HERE / "ExpressionLessSquare").glob("*.jack")):
            with self.subTest(jack=jack.name):
                self._compare_parse(jack)

    def test_square(self) -> None:
        for jack in sorted((HERE / "Square").glob("*.jack")):
            with self.subTest(jack=jack.name):
                self._compare_parse(jack)


if __name__ == "__main__":
    unittest.main()
