"""CodeWriter: emits Hack assembly for parsed VM commands.

write_push and write_pop are stubs to be implemented.
"""

from __future__ import annotations

from pathlib import Path
from typing import TextIO

from parser import Segment


# Binary ALU ops: the rhs goes into M (= top-of-stack minus one) after
# `D=y; A=SP-1`. Each entry says "what to put on the right of M=".
_BINARY_OPS = {
    "add": "M+D",
    "sub": "M-D",
    "and": "M&D",
    "or":  "M|D",
}

# Unary ops: rewrite the value at the top of the stack in place.
_UNARY_OPS = {
    "neg": "-M",
    "not": "!M",
}

# Comparison ops: subtract, then jump on the sign of the result.
_COMPARISON_JUMPS = {
    "eq": "JEQ",
    "gt": "JGT",
    "lt": "JLT",
}


# Pointer-based segments map to their base-pointer symbol in RAM.
_BASE_POINTER = {
    Segment.LOCAL:    "LCL",
    Segment.ARGUMENT: "ARG",
    Segment.THIS:     "THIS",
    Segment.THAT:     "THAT",
}


class CodeWriter:
    def __init__(self, out_path: Path, vm_filename: str) -> None:
        self._out: TextIO = out_path.open("w")
        self._filename = vm_filename     # used for static segment naming
        self._label_counter = 0          # used for eq/gt/lt unique labels

    def write_arithmetic(self, op: str) -> None:
        """Emit asm for add/sub/neg/eq/gt/lt/and/or/not."""
        if op in _BINARY_OPS:
            self._emit(
                "@SP",
                "AM=M-1",                # SP--, A = new SP (points to y)
                "D=M",                   # D = y
                "A=A-1",                 # A = SP-1 (points to x)
                f"M={_BINARY_OPS[op]}",  # x = x op y
            )
        elif op in _UNARY_OPS:
            self._emit(
                "@SP",
                "A=M-1",                 # top of stack
                f"M={_UNARY_OPS[op]}",
            )
        elif op in _COMPARISON_JUMPS:
            true_label = f"TRUE_{self._label_counter}"
            end_label = f"END_{self._label_counter}"
            self._label_counter += 1
            jump = _COMPARISON_JUMPS[op]
            self._emit(
                "@SP",
                "AM=M-1",
                "D=M",                   # D = y
                "A=A-1",                 # A = SP-1 (x)
                "D=M-D",                 # D = x - y
                f"@{true_label}",
                f"D;{jump}",
                "@SP",
                "A=M-1",
                "M=0",                   # false
                f"@{end_label}",
                "0;JMP",
                f"({true_label})",
                "@SP",
                "A=M-1",
                "M=-1",                  # true
                f"({end_label})",
            )
        else:
            raise ValueError(f"Unknown arithmetic op: {op}")

    def write_push(self, segment: Segment, index: int) -> None:
        """Emit asm to push the value from segment[index] onto the stack."""
        # 1. Load the value to push into D.
        match segment:
            case Segment.CONSTANT:
                self._emit(f"@{index}", "D=A")
            case Segment.LOCAL | Segment.ARGUMENT | Segment.THIS | Segment.THAT:
                base = _BASE_POINTER[segment]
                self._emit(
                    f"@{index}",
                    "D=A",
                    f"@{base}",
                    "A=D+M",             # A = base + index
                    "D=M",               # D = RAM[base + index]
                )
            case Segment.TEMP:
                self._emit(f"@{5 + index}", "D=M")
            case Segment.POINTER:
                self._emit(f"@{3 + index}", "D=M")
            case Segment.STATIC:
                self._emit(f"@{self._filename}.{index}", "D=M")
            case _:
                raise ValueError(f"Unknown segment: {segment}")

        # 2. Push D onto the stack: RAM[SP] = D; SP++.
        self._emit(
            "@SP",
            "A=M",                   # A = SP (next free slot)
            "M=D",                   # RAM[SP] = D
            "@SP",
            "M=M+1",                 # SP++
        )


    def write_pop(self, segment: Segment, index: int) -> None:
        """Emit asm to pop the top of stack into segment[index]."""
        match segment:
            case Segment.CONSTANT:
                raise ValueError("Cannot pop into constant segment")
            case Segment.LOCAL | Segment.ARGUMENT | Segment.THIS | Segment.THAT:
                # Target address depends on a base pointer; stash it in R13
                # so it survives the stack pop that follows.
                base = _BASE_POINTER[segment]
                self._emit(
                    f"@{index}",
                    "D=A",
                    f"@{base}",
                    "D=D+M",                 # D = base + index
                    "@R13",
                    "M=D",                   # R13 = target address
                    "@SP",
                    "AM=M-1",                # SP--, A = top
                    "D=M",                   # D = popped value
                    "@R13",
                    "A=M",                   # A = saved target address
                    "M=D",                   # RAM[target] = D
                )
            case Segment.TEMP:
                self._pop_into_fixed_address(5 + index)
            case Segment.POINTER:
                self._pop_into_fixed_address(3 + index)
            case Segment.STATIC:
                self._pop_into_fixed_address(f"{self._filename}.{index}")
            case _:
                raise ValueError(f"Unknown segment: {segment}")

    def _pop_into_fixed_address(self, target: int | str) -> None:
        """Pop the top of stack into RAM[@target], where target is a constant."""
        self._emit(
            "@SP",
            "AM=M-1",                # SP--, A = top
            "D=M",                   # D = popped value
            f"@{target}",
            "M=D",                   # RAM[target] = D
        )

    def close(self) -> None:
        self._out.close()

    def _emit(self, *lines: str) -> None:
        """Write one or more asm lines."""
        for line in lines:
            self._out.write(line + "\n")
