# Project 6 — Hack Assembler (Python skeleton)

A minimal two-pass assembler for the Hack platform.

## Layout

- `assembler.py` — CLI entrypoint and two-pass driver.
- `parser.py` — Strips comments/whitespace, classifies and dissects commands.
- `code_module.py` — Translates `dest` / `comp` / `jump` mnemonics to bits.
- `symbol_table.py` — Predefined symbols + labels + variables.

## Usage

```sh
python projects/06/assembler.py path/to/Prog.asm
```

Produces `path/to/Prog.hack` next to the input.

## Status

Skeleton is functional end-to-end on well-formed input.
Next steps:
- Validate against the supplied Project 6 test files
  (`Add`, `Max`, `Rect`, `Pong`) under both `*L.asm` (no symbols) and
  symbolic variants.
- Add unit tests for `Parser` and `Code`.
