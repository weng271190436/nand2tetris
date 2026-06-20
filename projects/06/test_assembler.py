"""Tests for the Hack assembler."""

from __future__ import annotations

import unittest
from pathlib import Path

from assembler import assemble


HERE = Path(__file__).resolve().parent
FILL_ASM = HERE.parent / "04" / "Fill.asm"
MULT_ASM = HERE.parent / "04" / "Mult.asm"


FILL_EXPECTED = [
    "0110000000000000",
    "1111110000010000",
    "0000000000000110",
    "1110001100000101",
    "0000000000000000",
    "1110101010000111",
    "0100000000000000",
    "1110110000010000",
    "0000000000010000",
    "1110001100001000",
    "0000000000010000",
    "1111110000010000",
    "0110000000000000",
    "1110010011010000",
    "0000000000010111",
    "1110001100000010",
    "0000000000010000",
    "1111110000100000",
    "1110111010001000",
    "0000000000010000",
    "1111110111001000",
    "0000000000001010",
    "1110101010000111",
    "0000000000010111",
    "1110101010000111",
]


MULT_EXPECTED = [
    "0000000000000010",
    "1110101010001000",
    "0000000000000001",
    "1111110000010000",
    "0000000000010000",
    "1110001100001000",
    "0000000000010000",
    "1111110000010000",
    "0000000000010010",
    "1110001100000010",
    "0000000000000000",
    "1111110000010000",
    "0000000000000010",
    "1111000010001000",
    "0000000000010000",
    "1111110010001000",
    "0000000000000110",
    "1110101010000111",
    "0000000000010010",
    "1110101010000111",
]


class TestAssembler(unittest.TestCase):
    def tearDown(self) -> None:
        for asm in (FILL_ASM, MULT_ASM):
            out = asm.with_suffix(".hack")
            if out.exists():
                out.unlink()

    def test_fill_asm(self) -> None:
        out_path = assemble(FILL_ASM)
        actual = out_path.read_text().splitlines()
        self.assertEqual(actual, FILL_EXPECTED)

    def test_mult_asm(self) -> None:
        out_path = assemble(MULT_ASM)
        actual = out_path.read_text().splitlines()
        self.assertEqual(actual, MULT_EXPECTED)


if __name__ == "__main__":
    unittest.main()
