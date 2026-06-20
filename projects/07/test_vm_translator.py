"""Tests for the VM translator.

- TestParser exercises only the parser (no CodeWriter needed).
- TestTranslation runs the full translator on every provided .vm file
  and sanity-checks the output. These tests will fail until CodeWriter
  is implemented.

Note: true correctness requires running the produced .asm in the
nand2tetris CPU emulator against the .tst / .cmp files. These tests
only verify that translation runs end-to-end and emits plausible asm.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from parser import parse, Arithmetic, Push, Pop
from vm_translator import translate


HERE = Path(__file__).resolve().parent

VM_FILES = [
    HERE / "StackArithmetic" / "SimpleAdd" / "SimpleAdd.vm",
    HERE / "StackArithmetic" / "StackTest" / "StackTest.vm",
    HERE / "MemoryAccess" / "BasicTest" / "BasicTest.vm",
    HERE / "MemoryAccess" / "PointerTest" / "PointerTest.vm",
    HERE / "MemoryAccess" / "StaticTest" / "StaticTest.vm",
]


class TestParser(unittest.TestCase):
    def test_simple_add(self) -> None:
        commands = list(parse(VM_FILES[0]))
        self.assertEqual(
            commands,
            [
                Push(segment="constant", index=7),
                Push(segment="constant", index=8),
                Arithmetic(op="add"),
            ],
        )


class TestTranslation(unittest.TestCase):
    """End-to-end smoke tests: translate, then sanity-check the .asm output."""

    def tearDown(self) -> None:
        for vm in VM_FILES:
            asm = vm.with_suffix(".asm")
            if asm.exists():
                asm.unlink()

    def _check_translation(self, vm_path: Path) -> str:
        asm_path = translate(vm_path)
        self.assertTrue(asm_path.exists(), f"{asm_path} was not created")
        content = asm_path.read_text()
        self.assertGreater(len(content), 0, f"{asm_path} is empty")
        # Every nontrivial VM translation manipulates the stack pointer.
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


if __name__ == "__main__":
    unittest.main()
