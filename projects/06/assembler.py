#!/usr/bin/env python3
"""Entry point for the Hack assembler.

Usage:
    python3 assembler.py <Prog.asm>

Writes <Prog.hack> next to the input file.
"""

from __future__ import annotations

import sys
from pathlib import Path

from parser import parse, AInstruction, CInstruction, LInstruction
from code_module import Code
from symbol_table import SymbolTable


def assemble(asm_path: Path) -> Path:
    """Translate a .asm file into a .hack file. Returns the output path."""
    commands = list(parse(asm_path))
    symbols = SymbolTable()

    # First pass: bind labels to ROM addresses.
    rom_address = 0
    for cmd in commands:
        if isinstance(cmd, LInstruction):
            symbols.add_entry(cmd.label, rom_address)
        else:
            rom_address += 1

    # Second pass: emit binary.
    next_variable_address = 16
    out_lines: list[str] = []

    for cmd in commands:
        match cmd:
            case AInstruction(symbol=sym):
                if sym.isdigit():
                    value = int(sym)
                else:
                    if not symbols.contains(sym):
                        symbols.add_entry(sym, next_variable_address)
                        next_variable_address += 1
                    value = symbols.get_address(sym)
                out_lines.append(f"0{value:015b}")

            case CInstruction(dest=d, comp=c, jump=j):
                out_lines.append(f"111{Code.comp(c)}{Code.dest(d)}{Code.jump(j)}")

            case LInstruction():
                pass  # already handled in pass 1

    out_path = asm_path.with_suffix(".hack")
    out_path.write_text("\n".join(out_lines) + "\n")
    return out_path


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python3 assembler.py <Prog.asm>", file=sys.stderr)
        return 1
    asm_path = Path(argv[1])
    if not asm_path.is_file():
        print(f"File not found: {asm_path}", file=sys.stderr)
        return 1
    print(f"Wrote {assemble(asm_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
