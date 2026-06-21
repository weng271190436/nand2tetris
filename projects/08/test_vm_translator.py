"""Tests for the Project 8 VM translator.

TestParser exercises the parser only (no CodeWriter needed).
TestTranslation runs the full translator on each provided program and
sanity-checks the output. These will fail until the new write_* methods
(write_label, write_goto, write_if_goto, write_function, write_call,
write_return, write_init) are implemented.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from parser import (
    parse,
    Arithmetic,
    Push,
    Pop,
    Label,
    Goto,
    IfGoto,
    Function,
    Call,
    Return,
    Segment,
)
from vm_translator import translate


HERE = Path(__file__).resolve().parent

PROGRAM_FLOW_DIRS = [
    HERE / "ProgramFlow" / "BasicLoop",
    HERE / "ProgramFlow" / "FibonacciSeries",
]

FUNCTION_CALL_DIRS = [
    HERE / "FunctionCalls" / "SimpleFunction",
    HERE / "FunctionCalls" / "NestedCall",
    HERE / "FunctionCalls" / "FibonacciElement",
    HERE / "FunctionCalls" / "StaticsTest",
]

ALL_DIRS = PROGRAM_FLOW_DIRS + FUNCTION_CALL_DIRS


FIB_SERIES_VM = HERE / "ProgramFlow" / "FibonacciSeries" / "FibonacciSeries.vm"


class TestParser(unittest.TestCase):
    def test_fibonacci_series_first_commands(self) -> None:
        commands = list(parse(FIB_SERIES_VM))
        # First 4 commands of FibonacciSeries.vm.
        self.assertEqual(
            commands[:4],
            [
                Push(segment=Segment.ARGUMENT, index=1),
                Pop(segment=Segment.POINTER, index=1),
                Push(segment=Segment.CONSTANT, index=0),
                Pop(segment=Segment.THAT, index=0),
            ],
        )

    def test_parses_label_goto_if_goto(self) -> None:
        commands = list(parse(FIB_SERIES_VM))
        self.assertIn(Label(name="LOOP"), commands)
        self.assertIn(Goto(label="END"), commands)
        self.assertIn(IfGoto(label="COMPUTE_ELEMENT"), commands)


class TestTranslation(unittest.TestCase):
    """Smoke tests: translate each program; verify .asm output exists."""

    def tearDown(self) -> None:
        for d in ALL_DIRS:
            asm = d / f"{d.name}.asm"
            if asm.exists():
                asm.unlink()

    def _check(self, program_dir: Path) -> None:
        asm_path = translate(program_dir)
        self.assertTrue(asm_path.exists(), f"{asm_path} was not created")
        content = asm_path.read_text()
        self.assertGreater(len(content), 0, f"{asm_path} is empty")
        self.assertIn("@SP", content)

    def test_basic_loop(self) -> None:
        self._check(PROGRAM_FLOW_DIRS[0])

    def test_fibonacci_series(self) -> None:
        self._check(PROGRAM_FLOW_DIRS[1])

    def test_simple_function(self) -> None:
        self._check(FUNCTION_CALL_DIRS[0])

    def test_nested_call(self) -> None:
        self._check(FUNCTION_CALL_DIRS[1])

    def test_fibonacci_element(self) -> None:
        self._check(FUNCTION_CALL_DIRS[2])

    def test_statics_test(self) -> None:
        self._check(FUNCTION_CALL_DIRS[3])


if __name__ == "__main__":
    unittest.main()
