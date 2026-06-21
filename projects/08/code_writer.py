"""CodeWriter: emits Hack assembly for parsed VM commands.

write_arithmetic, write_push, write_pop are implemented.
The branching and function methods are stubs to be implemented.
"""

from __future__ import annotations

from pathlib import Path
from typing import TextIO

from parser import Segment


# Binary ALU ops: the rhs goes into M (= top-of-stack minus one) after
# `D=y; A=SP-1`. Each entry says "what to put on the right of M=".
_BINARY_OPS = {
    "add": "D+M",
    "sub": "M-D",
    "and": "D&M",
    "or":  "D|M",
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
    def __init__(self, out_path: Path) -> None:
        self._out: TextIO = out_path.open("w")
        self._filename = ""              # set per .vm file via set_filename
        self._function = ""              # current function (for label scoping)
        self._label_counter = 0          # used for eq/gt/lt unique labels
        self._call_counter = 0           # used for unique return-address labels

    def set_filename(self, vm_filename: str) -> None:
        """Tell the writer which .vm file's commands are about to be emitted.

        Affects static segment naming and label scoping for files without
        explicit function declarations.
        """
        self._filename = vm_filename

    def write_init(self) -> None:
        """Emit the bootstrap: SP = 256, then call Sys.init."""
        self._filename = "Bootstrap"           # scope for the return label
        self._emit(
            "@256",
            "D=A",
            "@SP",
            "M=D",                              # SP = 256
        )
        self.write_call("Sys.init", 0)

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

        self._emit(
            "@SP",
            "A=M",
            "M=D",
            "@SP",
            "M=M+1",
        )

    def write_pop(self, segment: Segment, index: int) -> None:
        """Emit asm to pop the top of stack into segment[index]."""
        match segment:
            case Segment.CONSTANT:
                raise ValueError("Cannot pop into constant segment")
            case Segment.LOCAL | Segment.ARGUMENT | Segment.THIS | Segment.THAT:
                base = _BASE_POINTER[segment]
                self._emit(
                    f"@{index}",
                    "D=A",
                    f"@{base}",
                    "D=D+M",
                    "@R13",
                    "M=D",
                    "@SP",
                    "AM=M-1",
                    "D=M",
                    "@R13",
                    "A=M",
                    "M=D",
                )
            case Segment.TEMP:
                self._pop_into_fixed_address(5 + index)
            case Segment.POINTER:
                self._pop_into_fixed_address(3 + index)
            case Segment.STATIC:
                self._pop_into_fixed_address(f"{self._filename}.{index}")
            case _:
                raise ValueError(f"Unknown segment: {segment}")

    def write_label(self, name: str) -> None:
        """Emit asm for `label X` — declare a scoped label."""
        self._emit(f"({self._scoped(name)})")

    def write_goto(self, label: str) -> None:
        """Emit asm for `goto X` — unconditional jump."""
        self._emit(
            f"@{self._scoped(label)}",
            "0;JMP",
        )

    def write_if_goto(self, label: str) -> None:
        """Emit asm for `if-goto X` — pop top of stack; jump if nonzero."""
        self._emit(
            "@SP",
            "AM=M-1",
            "D=M",                       # D = popped value
            f"@{self._scoped(label)}",
            "D;JNE",                     # jump if D != 0 (i.e., true)
        )

    def write_function(self, name: str, n_locals: int) -> None:
        """Emit asm for `function f n` — declare function, zero-init n locals."""
        self._function = name
        self._emit(f"({name})")
        for _ in range(n_locals):
            self._emit(
                "@SP",
                "A=M",
                "M=0",                          # push 0 onto stack
                "@SP",
                "M=M+1",
            )

    def write_call(self, name: str, n_args: int) -> None:
        """Emit asm for `call f n` — save caller frame, set up callee, jump."""
        ret_label = self._scoped(f"ret.{self._call_counter}")
        self._call_counter += 1

        # 1. Push return address.
        self._emit(f"@{ret_label}", "D=A")
        self._push_d()

        # 2. Push the caller's frame pointers.
        for sym in ("LCL", "ARG", "THIS", "THAT"):
            self._push_var(sym)

        # 3. ARG = SP - 5 - n_args  (points to the first pushed arg)
        self._emit(
            "@SP",
            "D=M",
            f"@{5 + n_args}",
            "D=D-A",
            "@ARG",
            "M=D",
        )

        # 4. LCL = SP  (callee's locals start at the new top of stack)
        self._emit(
            "@SP",
            "D=M",
            "@LCL",
            "M=D",
        )

        # 5. Jump to the function, then declare the return-address label.
        self._emit(f"@{name}", "0;JMP", f"({ret_label})")

    def write_return(self) -> None:
        """Emit asm for `return` — restore caller frame, place return value."""
        self._emit(
            # FRAME (R13) = LCL  — temporary pointer to top of caller's saved frame.
            "@LCL",
            "D=M",
            "@R13",
            "M=D",
            # RET (R14) = *(FRAME - 5)  — stash the return address before we restore ARG.
            "@5",
            "A=D-A",
            "D=M",
            "@R14",
            "M=D",
            # *ARG = pop()  — place return value where argument 0 lived.
            "@SP",
            "AM=M-1",
            "D=M",
            "@ARG",
            "A=M",
            "M=D",
            # SP = ARG + 1  — caller's new top of stack.
            "@ARG",
            "D=M+1",
            "@SP",
            "M=D",
            # THAT = *(FRAME - 1)  — restore caller's THAT.
            "@R13",
            "AM=M-1",
            "D=M",
            "@THAT",
            "M=D",
            # THIS = *(FRAME - 2)
            "@R13",
            "AM=M-1",
            "D=M",
            "@THIS",
            "M=D",
            # ARG = *(FRAME - 3)
            "@R13",
            "AM=M-1",
            "D=M",
            "@ARG",
            "M=D",
            # LCL = *(FRAME - 4)
            "@R13",
            "AM=M-1",
            "D=M",
            "@LCL",
            "M=D",
            # goto RET
            "@R14",
            "A=M",
            "0;JMP",
        )

    def _pop_into_fixed_address(self, target: int | str) -> None:
        self._emit(
            "@SP",
            "AM=M-1",
            "D=M",
            f"@{target}",
            "M=D",
        )

    def _push_d(self) -> None:
        """Push the current value of D onto the stack."""
        self._emit(
            "@SP",
            "A=M",
            "M=D",
            "@SP",
            "M=M+1",
        )

    def _push_var(self, symbol: str) -> None:
        """Push the value of an asm variable (e.g. LCL, ARG, THIS, THAT)."""
        self._emit(f"@{symbol}", "D=M")
        self._push_d()

    def _scoped(self, label: str) -> str:
        """Qualify a VM label with its enclosing function (or file) to avoid collisions."""
        scope = self._function or self._filename
        assert scope, "Cannot scope a label before set_filename or write_function"
        return f"{scope}${label}"

    def close(self) -> None:
        self._out.close()

    def _emit(self, *lines: str) -> None:
        for line in lines:
            self._out.write(line + "\n")
