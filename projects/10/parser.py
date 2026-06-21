"""CompilationEngine: parse a stream of Jack tokens into a parse tree (XML).

Implements the Jack grammar. Each compile_* method consumes tokens belonging
to one grammar non-terminal and writes the corresponding XML to the output.

All compile_* methods are stubs to be implemented.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, TextIO

from tokenizer import Token, TokenType, tokenize, token_to_xml


class CompilationEngine:
    def __init__(self, source: Path, out_path: Path) -> None:
        self._tokens: list[Token] = list(tokenize(source))
        self._index = 0
        self._out: TextIO = out_path.open("w")
        self._indent = 0

    # ---- public entry point ----

    def compile(self) -> None:
        """Compile the whole source — a single top-level `class`."""
        self.compile_class()
        self._out.close()

    # ---- Jack grammar non-terminals ----

    def compile_class(self) -> None:
        """class: 'class' className '{' classVarDec* subroutineDec* '}'"""
        raise NotImplementedError

    def compile_class_var_dec(self) -> None:
        """classVarDec: ('static' | 'field') type varName (',' varName)* ';'"""
        raise NotImplementedError

    def compile_subroutine_dec(self) -> None:
        """subroutineDec: ('constructor' | 'function' | 'method')
                          ('void' | type) subroutineName
                          '(' parameterList ')' subroutineBody"""
        raise NotImplementedError

    def compile_parameter_list(self) -> None:
        """parameterList: ((type varName) (',' type varName)*)?"""
        raise NotImplementedError

    def compile_subroutine_body(self) -> None:
        """subroutineBody: '{' varDec* statements '}'"""
        raise NotImplementedError

    def compile_var_dec(self) -> None:
        """varDec: 'var' type varName (',' varName)* ';'"""
        raise NotImplementedError

    def compile_statements(self) -> None:
        """statements: statement*"""
        raise NotImplementedError

    def compile_let(self) -> None:
        """letStatement: 'let' varName ('[' expression ']')? '=' expression ';'"""
        raise NotImplementedError

    def compile_if(self) -> None:
        """ifStatement: 'if' '(' expression ')' '{' statements '}'
                       ('else' '{' statements '}')?"""
        raise NotImplementedError

    def compile_while(self) -> None:
        """whileStatement: 'while' '(' expression ')' '{' statements '}'"""
        raise NotImplementedError

    def compile_do(self) -> None:
        """doStatement: 'do' subroutineCall ';'"""
        raise NotImplementedError

    def compile_return(self) -> None:
        """returnStatement: 'return' expression? ';'"""
        raise NotImplementedError

    def compile_expression(self) -> None:
        """expression: term (op term)*"""
        raise NotImplementedError

    def compile_term(self) -> None:
        """term: integerConstant | stringConstant | keywordConstant |
                 varName | varName '[' expression ']' |
                 subroutineCall | '(' expression ')' | unaryOp term"""
        raise NotImplementedError

    def compile_expression_list(self) -> None:
        """expressionList: (expression (',' expression)*)?"""
        raise NotImplementedError

    # ---- helpers (to be used inside compile_* methods) ----

    def _peek(self) -> Token:
        return self._tokens[self._index]

    def _advance(self) -> Token:
        tok = self._tokens[self._index]
        self._index += 1
        return tok

    def _has_more(self) -> bool:
        return self._index < len(self._tokens)

    def _write_open(self, name: str) -> None:
        self._out.write("  " * self._indent + f"<{name}>\n")
        self._indent += 1

    def _write_close(self, name: str) -> None:
        self._indent -= 1
        self._out.write("  " * self._indent + f"</{name}>\n")

    def _write_token(self, token: Token) -> None:
        self._out.write("  " * self._indent + token_to_xml(token) + "\n")
