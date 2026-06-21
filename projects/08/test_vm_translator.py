"""Tests for the Project 8 VM translator.

- TestParser exercises the parser only.
- TestEndToEnd translates -> assembles -> executes on a Python Hack CPU
  emulator, then checks final RAM state against the expected values from
  each .cmp file. Initial RAM and cycle count come from the matching
  .tst file.
"""

from __future__ import annotations

import re
import subprocess
import sys
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

# Reuse the Hack CPU emulator from Project 7.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "07"))
from hack_emulator import HackCPU, load_hack, to_signed  # noqa: E402


HERE = Path(__file__).resolve().parent
ASSEMBLER = HERE.parent / "06" / "assembler.py"

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


_RAM_ADDR_RE = re.compile(r"RAM\[(\d+)")
_SET_RAM_RE = re.compile(r"set\s+RAM\[(\d+)\]\s+(-?\d+)")
_REPEAT_RE = re.compile(r"repeat\s+(\d+)")


def _parse_cmp(path: Path) -> dict[int, int]:
    lines = [line for line in path.read_text().splitlines() if line.strip()]
    if len(lines) % 2 != 0:
        raise ValueError(f"Unexpected odd number of rows in {path}")

    result: dict[int, int] = {}
    for header, data in zip(lines[0::2], lines[1::2]):
        addresses = [int(m) for m in _RAM_ADDR_RE.findall(header)]
        values = [int(cell.strip()) for cell in data.strip("|").split("|") if cell.strip()]
        if len(addresses) != len(values):
            raise ValueError(f"Header/data column mismatch in {path}")
        for addr, val in zip(addresses, values):
            result[addr] = val
    return result


def _parse_tst(path: Path) -> tuple[dict[int, int], int]:
    content = re.sub(r"//.*", "", path.read_text())
    ram_init = {int(addr): int(val) for addr, val in _SET_RAM_RE.findall(content)}
    match = _REPEAT_RE.search(content)
    cycles = int(match.group(1)) if match else 1000
    return ram_init, cycles


def _assemble(asm_path: Path) -> Path:
    subprocess.run(
        ["python3", str(ASSEMBLER), str(asm_path)],
        check=True, capture_output=True,
    )
    return asm_path.with_suffix(".hack")


def _cleanup(program_dir: Path) -> None:
    for ext in (".asm", ".hack"):
        out = program_dir / f"{program_dir.name}{ext}"
        if out.exists():
            out.unlink()


class TestParser(unittest.TestCase):
    def test_fibonacci_series_first_commands(self) -> None:
        commands = list(parse(FIB_SERIES_VM))
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


class TestEndToEnd(unittest.TestCase):
    """Translate -> assemble -> execute -> compare RAM state to .cmp file."""

    def tearDown(self) -> None:
        for d in ALL_DIRS:
            _cleanup(d)

    def _run_against_cmp(self, program_dir: Path) -> None:
        name = program_dir.name
        ram_init, cycles = _parse_tst(program_dir / f"{name}.tst")
        expected = _parse_cmp(program_dir / f"{name}.cmp")

        asm_path = translate(program_dir)
        hack_path = _assemble(asm_path)
        cpu = HackCPU(load_hack(hack_path))
        for addr, value in ram_init.items():
            cpu.ram[addr] = value
        cpu.run(cycles)

        for addr, expected_value in expected.items():
            self.assertEqual(
                to_signed(cpu.ram[addr]),
                expected_value,
                f"RAM[{addr}] mismatch in {name}",
            )

    def test_basic_loop(self) -> None:
        self._run_against_cmp(PROGRAM_FLOW_DIRS[0])

    def test_fibonacci_series(self) -> None:
        self._run_against_cmp(PROGRAM_FLOW_DIRS[1])

    def test_simple_function(self) -> None:
        self._run_against_cmp(FUNCTION_CALL_DIRS[0])

    def test_nested_call(self) -> None:
        self._run_against_cmp(FUNCTION_CALL_DIRS[1])

    def test_fibonacci_element(self) -> None:
        self._run_against_cmp(FUNCTION_CALL_DIRS[2])

    def test_statics_test(self) -> None:
        self._run_against_cmp(FUNCTION_CALL_DIRS[3])


if __name__ == "__main__":
    unittest.main()
