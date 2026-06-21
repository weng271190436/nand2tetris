#!/usr/bin/env python3
"""VM Translator entry point (Project 8).

Usage:
    python3 vm_translator.py <Prog.vm>      # single file → Prog.asm
    python3 vm_translator.py <ProgDir>      # directory   → ProgDir/ProgDir.asm

In directory mode, emits a bootstrap (SP=256; call Sys.init) before
translating every *.vm file in the directory.
"""

from __future__ import annotations

import sys
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
)
from code_writer import CodeWriter


def _dispatch(writer: CodeWriter, vm_path: Path) -> None:
    writer.set_filename(vm_path.stem)
    for cmd in parse(vm_path):
        match cmd:
            case Arithmetic(op):
                writer.write_arithmetic(op)
            case Push(segment, index):
                writer.write_push(segment, index)
            case Pop(segment, index):
                writer.write_pop(segment, index)
            case Label(name):
                writer.write_label(name)
            case Goto(label):
                writer.write_goto(label)
            case IfGoto(label):
                writer.write_if_goto(label)
            case Function(name, n_locals):
                writer.write_function(name, n_locals)
            case Call(name, n_args):
                writer.write_call(name, n_args)
            case Return():
                writer.write_return()


def translate(input_path: Path) -> Path:
    """Translate a .vm file or a directory of .vm files into a single .asm.

    File mode:  Prog.vm -> Prog.asm next to the input.
    Dir mode:   ProgDir/ -> ProgDir/ProgDir.asm; emits bootstrap; concatenates
                every Prog/*.vm.
    """
    if input_path.is_file():
        asm_path = input_path.with_suffix(".asm")
        writer = CodeWriter(asm_path)
        try:
            _dispatch(writer, input_path)
        finally:
            writer.close()
        return asm_path

    if input_path.is_dir():
        asm_path = input_path / f"{input_path.name}.asm"
        writer = CodeWriter(asm_path)
        try:
            writer.write_init()
            for vm_path in sorted(input_path.glob("*.vm")):
                _dispatch(writer, vm_path)
        finally:
            writer.close()
        return asm_path

    raise FileNotFoundError(f"Not a file or directory: {input_path}")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python3 vm_translator.py <Prog.vm | ProgDir>", file=sys.stderr)
        return 1
    input_path = Path(argv[1])
    if not input_path.exists():
        print(f"Not found: {input_path}", file=sys.stderr)
        return 1
    print(f"Wrote {translate(input_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
