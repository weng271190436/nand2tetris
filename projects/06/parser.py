"""Parser module: reads a Hack .asm file and exposes one command at a time."""

from __future__ import annotations

from enum import Enum, auto
from pathlib import Path


class CommandType(Enum):
    A_COMMAND = auto()  # @xxx
    C_COMMAND = auto()  # dest=comp;jump
    L_COMMAND = auto()  # (LABEL)


class Parser:
    def __init__(self, path: Path) -> None:
        self._lines = self._load(path)
        self._index = -1
        self._current: str | None = None

    @staticmethod
    def _load(path: Path) -> list[str]:
        cleaned: list[str] = []
        for raw in path.read_text().splitlines():
            line = raw.split("//", 1)[0].strip()
            if line:
                cleaned.append(line)
        return cleaned

    def has_more_commands(self) -> bool:
        return self._index + 1 < len(self._lines)

    def advance(self) -> None:
        self._index += 1
        self._current = self._lines[self._index]

    def command_type(self) -> CommandType:
        assert self._current is not None
        if self._current.startswith("@"):
            return CommandType.A_COMMAND
        if self._current.startswith("(") and self._current.endswith(")"):
            return CommandType.L_COMMAND
        return CommandType.C_COMMAND

    def symbol(self) -> str:
        """Symbol/value for A_COMMAND or label for L_COMMAND."""
        assert self._current is not None
        ctype = self.command_type()
        if ctype == CommandType.A_COMMAND:
            return self._current[1:]
        if ctype == CommandType.L_COMMAND:
            return self._current[1:-1]
        raise ValueError("symbol() not valid for C_COMMAND")

    def dest(self) -> str:
        assert self._current is not None
        if "=" in self._current:
            return self._current.split("=", 1)[0]
        return ""

    def comp(self) -> str:
        assert self._current is not None
        body = self._current
        if "=" in body:
            body = body.split("=", 1)[1]
        if ";" in body:
            body = body.split(";", 1)[0]
        return body

    def jump(self) -> str:
        assert self._current is not None
        if ";" in self._current:
            return self._current.split(";", 1)[1]
        return ""
