"""Parser: streams parsed Hack commands from a .asm file."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class AInstruction:
    symbol: str  # numeric literal as str ("21") or a name ("LOOP")


@dataclass(frozen=True)
class CInstruction:
    dest: str   # "" if absent
    comp: str
    jump: str   # "" if absent


@dataclass(frozen=True)
class LInstruction:
    label: str


Command = AInstruction | CInstruction | LInstruction


def parse(path: Path) -> Iterator[Command]:
    for raw in path.read_text().splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line:
            continue

        if line.startswith("@"):
            yield AInstruction(symbol=line[1:])
        elif line.startswith("(") and line.endswith(")"):
            yield LInstruction(label=line[1:-1])
        else:
            body = line
            dest = ""
            jump = ""
            if "=" in body:
                dest, body = body.split("=", 1)
            if ";" in body:
                body, jump = body.split(";", 1)
            yield CInstruction(dest=dest, comp=body, jump=jump)
