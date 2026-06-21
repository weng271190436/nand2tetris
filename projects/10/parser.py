"""CompilationEngine: parse a stream of Jack tokens into a parse tree (XML).

Implements the Jack grammar from the textbook (Chapter 10). Each compile_*
method consumes tokens belonging to one grammar non-terminal and writes the
corresponding nested XML to the output file.
"""

from __future__ import annotations

from pathlib import Path
from typing import TextIO

from tokenizer import Token, TokenType, tokenize, token_to_xml


_KEYWORD_CONSTANTS = frozenset({"true", "false", "null", "this"})
_OPS = frozenset("+-*/&|<>=")
_UNARY_OPS = frozenset("-~")
_TYPE_KEYWORDS = frozenset({"int", "char", "boolean"})


class CompilationEngine:
    def __init__(self, source: Path, out_path: Path) -> None:
        self._tokens: list[Token] = list(tokenize(source))
        self._index = 0
        self._out: TextIO = out_path.open("w")
        self._indent = 0

    # ---- public entry point ----

    def compile(self) -> None:
        self.compile_class()
        self._out.close()

    # ---- Jack grammar non-terminals ----

    def compile_class(self) -> None:
        """class: 'class' className '{' classVarDec* subroutineDec* '}'"""
        self._open("class")
        self._consume_and_write()             # 'class'
        self._consume_and_write()             # className
        self._consume_and_write()             # '{'
        while self._peek_value() in ("static", "field"):
            self.compile_class_var_dec()
        while self._peek_value() in ("constructor", "function", "method"):
            self.compile_subroutine_dec()
        self._consume_and_write()             # '}'
        self._close("class")

    def compile_class_var_dec(self) -> None:
        """classVarDec: ('static' | 'field') type varName (',' varName)* ';'"""
        self._open("classVarDec")
        self._consume_and_write()             # 'static' | 'field'
        self._consume_and_write()             # type
        self._consume_and_write()             # varName
        while self._peek_value() == ",":
            self._consume_and_write()         # ','
            self._consume_and_write()         # varName
        self._consume_and_write()             # ';'
        self._close("classVarDec")

    def compile_subroutine_dec(self) -> None:
        """subroutineDec: ('constructor'|'function'|'method')
                          ('void' | type) subroutineName
                          '(' parameterList ')' subroutineBody"""
        self._open("subroutineDec")
        self._consume_and_write()             # 'constructor' | 'function' | 'method'
        self._consume_and_write()             # 'void' | type
        self._consume_and_write()             # subroutineName
        self._consume_and_write()             # '('
        self.compile_parameter_list()
        self._consume_and_write()             # ')'
        self.compile_subroutine_body()
        self._close("subroutineDec")

    def compile_parameter_list(self) -> None:
        """parameterList: ((type varName) (',' type varName)*)?"""
        self._open("parameterList")
        if self._peek_value() != ")":
            self._consume_and_write()         # type
            self._consume_and_write()         # varName
            while self._peek_value() == ",":
                self._consume_and_write()     # ','
                self._consume_and_write()     # type
                self._consume_and_write()     # varName
        self._close("parameterList")

    def compile_subroutine_body(self) -> None:
        """subroutineBody: '{' varDec* statements '}'"""
        self._open("subroutineBody")
        self._consume_and_write()             # '{'
        while self._peek_value() == "var":
            self.compile_var_dec()
        self.compile_statements()
        self._consume_and_write()             # '}'
        self._close("subroutineBody")

    def compile_var_dec(self) -> None:
        """varDec: 'var' type varName (',' varName)* ';'"""
        self._open("varDec")
        self._consume_and_write()             # 'var'
        self._consume_and_write()             # type
        self._consume_and_write()             # varName
        while self._peek_value() == ",":
            self._consume_and_write()         # ','
            self._consume_and_write()         # varName
        self._consume_and_write()             # ';'
        self._close("varDec")

    def compile_statements(self) -> None:
        """statements: statement*"""
        self._open("statements")
        while self._peek_value() in ("let", "if", "while", "do", "return"):
            kw = self._peek_value()
            if kw == "let":
                self.compile_let()
            elif kw == "if":
                self.compile_if()
            elif kw == "while":
                self.compile_while()
            elif kw == "do":
                self.compile_do()
            else:
                self.compile_return()
        self._close("statements")

    def compile_let(self) -> None:
        """letStatement: 'let' varName ('[' expression ']')? '=' expression ';'"""
        self._open("letStatement")
        self._consume_and_write()             # 'let'
        self._consume_and_write()             # varName
        if self._peek_value() == "[":
            self._consume_and_write()         # '['
            self.compile_expression()
            self._consume_and_write()         # ']'
        self._consume_and_write()             # '='
        self.compile_expression()
        self._consume_and_write()             # ';'
        self._close("letStatement")

    def compile_if(self) -> None:
        """ifStatement: 'if' '(' expression ')' '{' statements '}'
                       ('else' '{' statements '}')?"""
        self._open("ifStatement")
        self._consume_and_write()             # 'if'
        self._consume_and_write()             # '('
        self.compile_expression()
        self._consume_and_write()             # ')'
        self._consume_and_write()             # '{'
        self.compile_statements()
        self._consume_and_write()             # '}'
        if self._peek_value() == "else":
            self._consume_and_write()         # 'else'
            self._consume_and_write()         # '{'
            self.compile_statements()
            self._consume_and_write()         # '}'
        self._close("ifStatement")

    def compile_while(self) -> None:
        """whileStatement: 'while' '(' expression ')' '{' statements '}'"""
        self._open("whileStatement")
        self._consume_and_write()             # 'while'
        self._consume_and_write()             # '('
        self.compile_expression()
        self._consume_and_write()             # ')'
        self._consume_and_write()             # '{'
        self.compile_statements()
        self._consume_and_write()             # '}'
        self._close("whileStatement")

    def compile_do(self) -> None:
        """doStatement: 'do' subroutineCall ';'"""
        self._open("doStatement")
        self._consume_and_write()             # 'do'
        self._subroutine_call()               # inlined, no wrapping tag
        self._consume_and_write()             # ';'
        self._close("doStatement")

    def compile_return(self) -> None:
        """returnStatement: 'return' expression? ';'"""
        self._open("returnStatement")
        self._consume_and_write()             # 'return'
        if self._peek_value() != ";":
            self.compile_expression()
        self._consume_and_write()             # ';'
        self._close("returnStatement")

    def compile_expression(self) -> None:
        """expression: term (op term)*"""
        self._open("expression")
        self.compile_term()
        while self._peek_value() in _OPS:
            self._consume_and_write()         # op
            self.compile_term()
        self._close("expression")

    def compile_term(self) -> None:
        """term: integerConstant | stringConstant | keywordConstant |
                 varName | varName '[' expression ']' |
                 subroutineCall | '(' expression ')' | unaryOp term"""
        self._open("term")
        tok = self._peek()

        if tok.kind in (TokenType.INT_CONST, TokenType.STRING_CONST):
            self._consume_and_write()
        elif tok.kind == TokenType.KEYWORD and tok.value in _KEYWORD_CONSTANTS:
            self._consume_and_write()
        elif tok.kind == TokenType.SYMBOL and tok.value in _UNARY_OPS:
            self._consume_and_write()         # unary op
            self.compile_term()
        elif tok.kind == TokenType.SYMBOL and tok.value == "(":
            self._consume_and_write()         # '('
            self.compile_expression()
            self._consume_and_write()         # ')'
        elif tok.kind == TokenType.IDENTIFIER:
            # Need 1-token lookahead to distinguish varName, array access, and call.
            next_value = self._peek_value(offset=1)
            if next_value == "[":
                self._consume_and_write()     # varName
                self._consume_and_write()     # '['
                self.compile_expression()
                self._consume_and_write()     # ']'
            elif next_value in ("(", "."):
                self._subroutine_call()
            else:
                self._consume_and_write()     # varName
        else:
            raise ValueError(f"Unexpected token in term: {tok}")

        self._close("term")

    def compile_expression_list(self) -> None:
        """expressionList: (expression (',' expression)*)?"""
        self._open("expressionList")
        if self._peek_value() != ")":
            self.compile_expression()
            while self._peek_value() == ",":
                self._consume_and_write()     # ','
                self.compile_expression()
        self._close("expressionList")

    # ---- private helpers ----

    def _subroutine_call(self) -> None:
        """subroutineCall: subroutineName '(' expressionList ')' |
                           (className|varName) '.' subroutineName '(' expressionList ')'

        No wrapping tag — inlined into the caller (doStatement or term).
        """
        self._consume_and_write()             # subroutineName or (className|varName)
        if self._peek_value() == ".":
            self._consume_and_write()         # '.'
            self._consume_and_write()         # subroutineName
        self._consume_and_write()             # '('
        self.compile_expression_list()
        self._consume_and_write()             # ')'

    def _peek(self, offset: int = 0) -> Token:
        return self._tokens[self._index + offset]

    def _peek_value(self, offset: int = 0) -> str | None:
        idx = self._index + offset
        return self._tokens[idx].value if idx < len(self._tokens) else None

    def _advance(self) -> Token:
        tok = self._tokens[self._index]
        self._index += 1
        return tok

    def _consume_and_write(self) -> None:
        """Consume the next token and emit it as XML at the current indent."""
        self._write_token(self._advance())

    def _open(self, name: str) -> None:
        self._out.write("  " * self._indent + f"<{name}>\n")
        self._indent += 1

    def _close(self, name: str) -> None:
        self._indent -= 1
        self._out.write("  " * self._indent + f"</{name}>\n")

    def _write_token(self, token: Token) -> None:
        self._out.write("  " * self._indent + token_to_xml(token) + "\n")
