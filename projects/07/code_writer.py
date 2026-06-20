"""CodeWriter: emits Hack assembly for parsed VM commands.

All write_* methods are stubs to be implemented.
"""

from __future__ import annotations

from pathlib import Path
from typing import TextIO


class CodeWriter:
    def __init__(self, out_path: Path, vm_filename: str) -> None:
        self._out: TextIO = out_path.open("w")
        self._filename = vm_filename     # used for static segment naming
        self._label_counter = 0          # used for eq/gt/lt unique labels

    def write_arithmetic(self, op: str) -> None:
        """Emit asm for add/sub/neg/eq/gt/lt/and/or/not."""
        raise NotImplementedError

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
