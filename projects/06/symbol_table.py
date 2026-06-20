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

    def add_entry(self, symbol: str, address: int) -> None:
        self._table[symbol] = address

    def contains(self, symbol: str) -> bool:
        return symbol in self._table

    def get_address(self, symbol: str) -> int:
        return self._table[symbol]
