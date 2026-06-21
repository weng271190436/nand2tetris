"""Tiny Hack CPU emulator.

Executes .hack-formatted instructions against a 32K RAM. Sufficient to
validate the Project 6 assembler and Project 7 VM translator end-to-end.

Usage:
    from hack_emulator import HackCPU, load_hack, to_signed

    cpu = HackCPU(load_hack(Path("Prog.hack")))
    cpu.ram[0] = 256          # initial state, mirrors a .tst `set RAM[...]`
    cpu.run(cycles=1000)      # ticktock N times
    assert cpu.ram[256] == 15
"""

from __future__ import annotations

from pathlib import Path


_MASK16 = 0xFFFF


class HackCPU:
    """A minimal Hack CPU. ROM is fixed at construction; RAM is mutable."""

    def __init__(self, instructions: list[str]) -> None:
        self._rom = instructions
        self.ram: list[int] = [0] * 32768
        self.a = 0
        self.d = 0
        self.pc = 0

    def run(self, cycles: int) -> None:
        for _ in range(cycles):
            if self.pc >= len(self._rom):
                break
            self._step()

    def _step(self) -> None:
        instr = self._rom[self.pc]
        if instr[0] == "0":
            # A-instruction: load the 15-bit literal into A.
            self.a = int(instr, 2)
            self.pc += 1
            return

        # C-instruction: 1 1 1 a c1 c2 c3 c4 c5 c6 d1 d2 d3 j1 j2 j3
        a_bit = instr[3] == "1"
        c_bits = instr[4:10]
        dest_bits = instr[10:13]
        jump_bits = instr[13:16]

        x = self.d
        y = self.ram[self.a] if a_bit else self.a
        out = _alu(x, y, c_bits)

        new_a = out if dest_bits[0] == "1" else self.a
        if dest_bits[1] == "1":
            self.d = out
        if dest_bits[2] == "1":
            self.ram[self.a] = out
        self.a = new_a

        if _should_jump(out, jump_bits):
            self.pc = self.a
        else:
            self.pc += 1


def _alu(x: int, y: int, c_bits: str) -> int:
    """Hack ALU: 6 control bits zx, nx, zy, ny, f, no operate on x and y."""
    zx, nx, zy, ny, f, no = (b == "1" for b in c_bits)
    if zx:
        x = 0
    if nx:
        x = ~x
    if zy:
        y = 0
    if ny:
        y = ~y
    out = (x + y) if f else (x & y)
    if no:
        out = ~out
    return out & _MASK16


def _should_jump(value: int, jump_bits: str) -> bool:
    """jump_bits = (j_lt, j_eq, j_gt) — jump if (value<0, ==0, >0) respectively."""
    signed = to_signed(value)
    j_lt, j_eq, j_gt = (b == "1" for b in jump_bits)
    return (j_lt and signed < 0) or (j_eq and signed == 0) or (j_gt and signed > 0)


def to_signed(value: int) -> int:
    """Interpret an unsigned 16-bit integer as signed two's complement."""
    return value - 0x10000 if value & 0x8000 else value


def load_hack(path: Path) -> list[str]:
    """Read a .hack file as a list of 16-char binary instruction strings."""
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]
