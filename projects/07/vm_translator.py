#!/usr/bin/env python3
"""VM Translator entry point.

Usage:
    python3 vm_translator.py <Prog.vm>

Writes <Prog.asm> next to the input file.
"""

from __future__ import annotations

import sys
from pathlib import Path

from parser import parse, Arithmetic, Push, Pop
from code_writer import CodeWriter


def translate(vm_path: Path) -> Path:
    """Translate a single .vm file into a .asm file. Returns the output path."""
    asm_path = vm_path.with_suffix(".asm")
    writer = CodeWriter(asm_path, vm_filename=vm_path.stem)
    try:
        for cmd in parse(vm_path):
            match cmd:
                case Arithmetic(op):
                    writer.write_arithmetic(op)
                case Push(segment, index):
                    writer.write_push(segment, index)
                case Pop(segment, index):
                    writer.write_pop(segment, index)
    finally:
        writer.close()
    return asm_path


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python3 vm_translator.py <Prog.vm>", file=sys.stderr)
        return 1
    vm_path = Path(argv[1])
    if not vm_path.is_file():
        print(f"File not found: {vm_path}", file=sys.stderr)
        return 1
    print(f"Wrote {translate(vm_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
