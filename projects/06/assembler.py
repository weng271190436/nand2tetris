#!/usr/bin/env python3
"""Entry point for the Hack assembler.

Usage:
    python3 assembler.py <Prog.asm>

Writes <Prog.hack> next to the input file.
"""

from __future__ import annotations

import sys
from pathlib import Path

from parser import Parser, CommandType
from code_module import Code
from symbol_table import SymbolTable


def assemble(asm_path: Path) -> Path:
    """Translate a .asm file into a .hack file. Returns the output path."""
    symbols = SymbolTable()

    # First pass: record label addresses.
    first = Parser(asm_path)
    rom_address = 0
    while first.has_more_commands():
        first.advance()
        ctype = first.command_type()
        if ctype == CommandType.L_COMMAND:
            symbols.add_entry(first.symbol(), rom_address)
        else:
            rom_address += 1

    # Second pass: emit binary.
    second = Parser(asm_path)
    next_variable_address = 16
    out_lines: list[str] = []

    while second.has_more_commands():
        second.advance()
        ctype = second.command_type()

        if ctype == CommandType.A_COMMAND:
            sym = second.symbol()
            if sym.isdigit():
                value = int(sym)
            else:
                if not symbols.contains(sym):
                    symbols.add_entry(sym, next_variable_address)
                    next_variable_address += 1
                value = symbols.get_address(sym)
            out_lines.append(f"0{value:015b}")

        elif ctype == CommandType.C_COMMAND:
            dest = Code.dest(second.dest())
            comp = Code.comp(second.comp())
            jump = Code.jump(second.jump())
            out_lines.append(f"111{comp}{dest}{jump}")

        # L_COMMAND: no output.

    out_path = asm_path.with_suffix(".hack")
    out_path.write_text("\n".join(out_lines) + "\n")
    return out_path


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python assembler.py <Prog.asm>", file=sys.stderr)
        return 1
    asm_path = Path(argv[1])
    if not asm_path.is_file():
        print(f"File not found: {asm_path}", file=sys.stderr)
        return 1
    out = assemble(asm_path)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
