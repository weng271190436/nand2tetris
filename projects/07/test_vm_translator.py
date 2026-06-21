"""Tests for the VM translator.

- TestParser exercises only the parser (no CodeWriter needed).
- TestTranslation runs the full translator on every provided .vm file
  and sanity-checks the output.
- TestEndToEnd translates -> assembles (via Project 6) -> executes on a
  Python Hack CPU emulator, then checks final RAM state against the
  expected values declared in each .cmp file. Initial RAM and cycle
  count come from the matching .tst file.
"""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

from parser import parse, Arithmetic, Push, Pop, Segment
from vm_translator import translate
from hack_emulator import HackCPU, load_hack, to_signed


HERE = Path(__file__).resolve().parent
ASSEMBLER = HERE.parent / "06" / "assembler.py"

VM_FILES = [
    HERE / "StackArithmetic" / "SimpleAdd" / "SimpleAdd.vm",
    HERE / "StackArithmetic" / "StackTest" / "StackTest.vm",
    HERE / "MemoryAccess" / "BasicTest" / "BasicTest.vm",
    HERE / "MemoryAccess" / "PointerTest" / "PointerTest.vm",
    HERE / "MemoryAccess" / "StaticTest" / "StaticTest.vm",
]


_RAM_ADDR_RE = re.compile(r"RAM\[(\d+)")
_SET_RAM_RE = re.compile(r"set\s+RAM\[(\d+)\]\s+(-?\d+)")
_REPEAT_RE = re.compile(r"repeat\s+(\d+)")


def _parse_cmp(path: Path) -> dict[int, int]:
    """Parse a .cmp file into {address: expected_value}.

    The file alternates header rows (containing `RAM[N]` columns) with data
    rows (containing the same number of numeric cells, pipe-separated).
    """
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
    """Parse a .tst file into (initial RAM, cycle count)."""
    content = re.sub(r"//.*", "", path.read_text())
    ram_init = {int(addr): int(val) for addr, val in _SET_RAM_RE.findall(content)}
    match = _REPEAT_RE.search(content)
    cycles = int(match.group(1)) if match else 1000
    return ram_init, cycles


def _assemble(asm_path: Path) -> Path:
    """Run the Project 6 assembler as a subprocess (isolates module names)."""
    subprocess.run(
        ["python3", str(ASSEMBLER), str(asm_path)],
        check=True, capture_output=True,
    )
    return asm_path.with_suffix(".hack")


class TestParser(unittest.TestCase):
    def test_simple_add(self) -> None:
        commands = list(parse(VM_FILES[0]))
        self.assertEqual(
            commands,
            [
                Push(segment=Segment.CONSTANT, index=7),
                Push(segment=Segment.CONSTANT, index=8),
                Arithmetic(op="add"),
            ],
        )


class TestTranslation(unittest.TestCase):
    """End-to-end smoke tests: translate, then sanity-check the .asm output."""

    def tearDown(self) -> None:
        for vm in VM_FILES:
            for ext in (".asm", ".hack"):
                out = vm.with_suffix(ext)
                if out.exists():
                    out.unlink()

    def _check_translation(self, vm_path: Path) -> str:
        asm_path = translate(vm_path)
        self.assertTrue(asm_path.exists(), f"{asm_path} was not created")
        content = asm_path.read_text()
        self.assertGreater(len(content), 0, f"{asm_path} is empty")
        self.assertIn("@SP", content, f"{asm_path} never references @SP")
        return content

    def test_simple_add(self) -> None:
        self._check_translation(VM_FILES[0])

    def test_stack_test(self) -> None:
        self._check_translation(VM_FILES[1])

    def test_basic_test(self) -> None:
        self._check_translation(VM_FILES[2])

    def test_pointer_test(self) -> None:
        self._check_translation(VM_FILES[3])

    def test_static_test(self) -> None:
        self._check_translation(VM_FILES[4])


class TestEndToEnd(unittest.TestCase):
    """Translate -> assemble -> execute -> compare RAM state to .cmp file."""

    def tearDown(self) -> None:
        for vm in VM_FILES:
            for ext in (".asm", ".hack"):
                out = vm.with_suffix(ext)
                if out.exists():
                    out.unlink()

    def _run_against_cmp(self, vm_path: Path) -> None:
        ram_init, cycles = _parse_tst(vm_path.with_suffix(".tst"))
        expected = _parse_cmp(vm_path.with_suffix(".cmp"))

        asm_path = translate(vm_path)
        hack_path = _assemble(asm_path)
        cpu = HackCPU(load_hack(hack_path))
        for addr, value in ram_init.items():
            cpu.ram[addr] = value
        cpu.run(cycles)

        for addr, expected_value in expected.items():
            self.assertEqual(
                to_signed(cpu.ram[addr]),
                expected_value,
                f"RAM[{addr}] mismatch in {vm_path.name}",
            )

    def test_simple_add(self) -> None:
        self._run_against_cmp(VM_FILES[0])

    def test_stack_test(self) -> None:
        self._run_against_cmp(VM_FILES[1])

    def test_basic_test(self) -> None:
        self._run_against_cmp(VM_FILES[2])

    def test_pointer_test(self) -> None:
        self._run_against_cmp(VM_FILES[3])

    def test_static_test(self) -> None:
        self._run_against_cmp(VM_FILES[4])


if __name__ == "__main__":
    unittest.main()
