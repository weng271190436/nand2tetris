"""SymbolTable for the Hack assembler.

Pre-populated with the predefined symbols from the Hack platform.
"""

from __future__ import annotations


class SymbolTable:
    def __init__(self) -> None:
        self._table: dict[str, int] = {
            "SP":     0,
            "LCL":    1,
            "ARG":    2,
            "THIS":   3,
            "THAT":   4,
            "SCREEN": 16384,
            "KBD":    24576,
        }
        for i in range(16):
            self._table[f"R{i}"] = i
        self._next_var = 16

    def add_entry(self, symbol: str, address: int) -> None:
        self._table[symbol] = address

    def resolve(self, symbol: str) -> int:
        """Return address, allocating a new RAM slot if symbol is unknown."""
        if symbol not in self._table:
            self._table[symbol] = self._next_var
            self._next_var += 1
        return self._table[symbol]
