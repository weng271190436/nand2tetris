"""JackTokenizer: stream of tokens from a .jack source file.

Per the Jack language spec, tokens are:
- keyword       (one of 21 reserved words)
- symbol        (one of 19 punctuation characters)
- identifier    (letter or underscore, then alphanumeric/underscore)
- integerConstant  (0 .. 32767)
- stringConstant   ("...", no quotes or newlines inside)

Comments (// ... and /* ... */, including /** ... */) and whitespace are skipped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterator


class TokenType(Enum):
    KEYWORD          = "keyword"
    SYMBOL           = "symbol"
    IDENTIFIER       = "identifier"
    INT_CONST        = "integerConstant"
    STRING_CONST     = "stringConstant"


KEYWORDS = frozenset({
    "class", "constructor", "function", "method", "field", "static",
    "var", "int", "char", "boolean", "void",
    "true", "false", "null", "this",
    "let", "do", "if", "else", "while", "return",
})

SYMBOLS = frozenset("{}()[].,;+-*/&|<>=~")


@dataclass(frozen=True)
class Token:
    kind: TokenType
    value: str


# Order matters: strings before identifiers (otherwise we'd consume the opening quote
# as part of nothing), integers before identifiers (so digits aren't read as names).
_TOKEN_RE = re.compile(
    r"""
    (?P<string>   " [^"\n]* "          ) |
    (?P<integer>  \d+                  ) |
    (?P<ident>    [A-Za-z_][A-Za-z0-9_]* ) |
    (?P<symbol>   [{}()\[\].,;+\-*/&|<>=~] )
    """,
    re.VERBOSE,
)

_COMMENT_LINE_RE = re.compile(r"//[^\n]*")
_COMMENT_BLOCK_RE = re.compile(r"/\*.*?\*/", re.DOTALL)


def _strip_comments(source: str) -> str:
    source = _COMMENT_BLOCK_RE.sub("", source)
    source = _COMMENT_LINE_RE.sub("", source)
    return source


def tokenize(source_or_path: str | Path) -> Iterator[Token]:
    """Yield tokens from a .jack source string or path."""
    if isinstance(source_or_path, Path):
        source = source_or_path.read_text()
    else:
        source = source_or_path
    source = _strip_comments(source)

    for m in _TOKEN_RE.finditer(source):
        if m.group("string") is not None:
            # Strip surrounding quotes.
            yield Token(TokenType.STRING_CONST, m.group("string")[1:-1])
        elif m.group("integer") is not None:
            yield Token(TokenType.INT_CONST, m.group("integer"))
        elif m.group("ident") is not None:
            ident = m.group("ident")
            if ident in KEYWORDS:
                yield Token(TokenType.KEYWORD, ident)
            else:
                yield Token(TokenType.IDENTIFIER, ident)
        elif m.group("symbol") is not None:
            yield Token(TokenType.SYMBOL, m.group("symbol"))


# XML escaping for the four characters that have special meaning.
_XML_ESCAPE = {"<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;"}


def token_to_xml(token: Token) -> str:
    """Render a single token in the Jack-analyzer XML format.

    Example: Token(SYMBOL, "<")  →  '<symbol> &lt; </symbol>'
    """
    tag = token.kind.value
    value = "".join(_XML_ESCAPE.get(c, c) for c in token.value)
    return f"<{tag}> {value} </{tag}>"
