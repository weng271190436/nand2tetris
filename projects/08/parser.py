"""Parser: streams parsed VM commands from a .vm file."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterator


class Segment(Enum):
    CONSTANT = "constant"
    LOCAL    = "local"
    ARGUMENT = "argument"
    THIS     = "this"
    THAT     = "that"
    TEMP     = "temp"
    POINTER  = "pointer"
    STATIC   = "static"


@dataclass(frozen=True)
class Arithmetic:
    op: str  # add, sub, neg, eq, gt, lt, and, or, not


@dataclass(frozen=True)
class Push:
    segment: Segment
    index: int


@dataclass(frozen=True)
class Pop:
    segment: Segment
    index: int


@dataclass(frozen=True)
class Label:
    name: str


@dataclass(frozen=True)
class Goto:
    label: str


@dataclass(frozen=True)
class IfGoto:
    label: str


@dataclass(frozen=True)
class Function:
    name: str
    n_locals: int


@dataclass(frozen=True)
class Call:
    name: str
    n_args: int


@dataclass(frozen=True)
class Return:
    pass


Command = Arithmetic | Push | Pop | Label | Goto | IfGoto | Function | Call | Return


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
            yield Push(segment=Segment(tokens[1]), index=int(tokens[2]))
        elif head == "pop":
            yield Pop(segment=Segment(tokens[1]), index=int(tokens[2]))
        elif head == "label":
            yield Label(name=tokens[1])
        elif head == "goto":
            yield Goto(label=tokens[1])
        elif head == "if-goto":
            yield IfGoto(label=tokens[1])
        elif head == "function":
            yield Function(name=tokens[1], n_locals=int(tokens[2]))
        elif head == "call":
            yield Call(name=tokens[1], n_args=int(tokens[2]))
        elif head == "return":
            yield Return()
        else:
            raise ValueError(f"Unknown VM command: {line!r}")
