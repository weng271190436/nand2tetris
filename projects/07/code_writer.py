"""CodeWriter: emits Hack assembly for parsed VM commands.

write_push and write_pop are stubs to be implemented.
"""

from __future__ import annotations

from pathlib import Path
from typing import TextIO


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

    def write_push(self, segment: str, index: int) -> None:
        """Emit asm to push the value from segment[index] onto the stack."""
        raise NotImplementedError

    def write_pop(self, segment: str, index: int) -> None:
        """Emit asm to pop the top of stack into segment[index]."""
        raise NotImplementedError

    def close(self) -> None:
        self._out.close()

    def _emit(self, *lines: str) -> None:
        """Write one or more asm lines."""
        for line in lines:
            self._out.write(line + "\n")
