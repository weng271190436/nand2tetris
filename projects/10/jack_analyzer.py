#!/usr/bin/env python3
"""Jack syntax analyzer (Project 10).

For each .jack file in the input (file or directory), produces:
- <file>T.xml — flat token stream
- <file>.xml  — parsed XML tree (requires CompilationEngine to be implemented)

Usage:
    python3 jack_analyzer.py <Prog.jack | ProgDir>
"""

from __future__ import annotations

import sys
from pathlib import Path

from tokenizer import tokenize, token_to_xml
from parser import CompilationEngine


def write_token_xml(jack_path: Path) -> Path:
    """Write the flat tokens of a .jack file to <name>T.xml."""
    out_path = jack_path.with_name(f"{jack_path.stem}T.xml")
    with out_path.open("w") as f:
        f.write("<tokens>\n")
        for token in tokenize(jack_path):
            f.write(token_to_xml(token) + "\n")
        f.write("</tokens>\n")
    return out_path


def write_parse_xml(jack_path: Path) -> Path:
    """Write the parse tree of a .jack file to <name>.xml."""
    out_path = jack_path.with_suffix(".xml")
    engine = CompilationEngine(jack_path, out_path)
    engine.compile()
    return out_path


def analyze(input_path: Path) -> list[Path]:
    """Run both passes on a .jack file or every .jack in a directory."""
    jack_files = (
        [input_path]
        if input_path.is_file() and input_path.suffix == ".jack"
        else sorted(input_path.glob("*.jack"))
    )
    if not jack_files:
        raise FileNotFoundError(f"No .jack files found in {input_path}")

    outputs: list[Path] = []
    for jack_path in jack_files:
        outputs.append(write_token_xml(jack_path))
        outputs.append(write_parse_xml(jack_path))
    return outputs


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python3 jack_analyzer.py <Prog.jack | ProgDir>", file=sys.stderr)
        return 1
    input_path = Path(argv[1])
    if not input_path.exists():
        print(f"Not found: {input_path}", file=sys.stderr)
        return 1
    for out in analyze(input_path):
        print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
