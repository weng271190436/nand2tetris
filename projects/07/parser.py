"""Parser: streams parsed VM commands from a .vm file."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class Arithmetic:
    op: str  # add, sub, neg, eq, gt, lt, and, or, not


@dataclass(frozen=True)
class Push:
    segment: str
    index: int


@dataclass(frozen=True)
class Pop:
    segment: str
    index: int


Command = Arithmetic | Push | Pop


ARITHMETIC_OPS = {"add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"}


def parse(path: Path) -> Iterator[Command]:
    for raw in path.read_text().splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line:
            continue

        tokens = line.split()
        head = tokens[0]

        if head in ARITHMETIC_OPS:
            yield Arithmetic(op=head)
        elif head == "push":
            yield Push(segment=tokens[1], index=int(tokens[2]))
        elif head == "pop":
            yield Pop(segment=tokens[1], index=int(tokens[2]))
        else:
            raise ValueError(f"Unknown VM command: {line!r}")
