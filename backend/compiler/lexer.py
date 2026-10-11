"""
Lexical Analyzer (Lexer) for Phase 1 of C Compiler Front End.
Produces ordered tokens with type, lexeme, line, and column.
"""
from enum import Enum
from typing import List, Optional, Any, Dict


class TokenType(str, Enum):
    # Keywords
    INT = "INT"
    RETURN = "RETURN"
    FOR = "FOR"
    WHILE = "WHILE"
    IF = "IF"
    ELSE = "ELSE"
    PRINT = "PRINT"

    # Identifiers & Literals
    IDENTIFIER = "IDENTIFIER"
    INT_LITERAL = "INT_LITERAL"

    # Arithmetic Operators
    PLUS = "PLUS"               # +
    MINUS = "MINUS"             # -
    STAR = "STAR"               # *
    SLASH = "SLASH"             # /
    PERCENT = "PERCENT"         # %

    # Increment / Decrement
    INCREMENT = "INCREMENT"     # ++
    DECREMENT = "DECREMENT"     # --

    # Assignment Operators
    ASSIGN = "ASSIGN"                 # =
    PLUS_ASSIGN = "PLUS_ASSIGN"       # +=
    MINUS_ASSIGN = "MINUS_ASSIGN"     # -=
    STAR_ASSIGN = "STAR_ASSIGN"       # *=
    SLASH_ASSIGN = "SLASH_ASSIGN"     # /=
    PERCENT_ASSIGN = "PERCENT_ASSIGN" # %=

    # Relational & Equality Operators
    LT = "LT"                   # <
    LE = "LE"                   # <=
    GT = "GT"                   # >
    GE = "GE"                   # >=
    EQ = "EQ"                   # ==
    NE = "NE"                   # !=

    # Logical Operators
    LOGICAL_AND = "LOGICAL_AND" # &&
    LOGICAL_OR = "LOGICAL_OR"   # ||
    LOGICAL_NOT = "LOGICAL_NOT" # !

    # Delimiters & Punctuation
    LPAREN = "LPAREN"           # (
    RPAREN = "RPAREN"           # )
    LBRACE = "LBRACE"           # {
    RBRACE = "RBRACE"           # }
    LBRACKET = "LBRACKET"       # [
    RBRACKET = "RBRACKET"       # ]
    SEMICOLON = "SEMICOLON"     # ;
    COMMA = "COMMA"             # ,

    # End of File
    EOF = "EOF"


KEYWORDS: Dict[str, TokenType] = {
    "int": TokenType.INT,
    "return": TokenType.RETURN,
    "for": TokenType.FOR,
    "while": TokenType.WHILE,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "print": TokenType.PRINT,
}


class Token:
    """Represents a lexical token."""
    def __init__(self, type_: TokenType, value: Any, line: int, column: int):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "value": self.value,
            "line": self.line,
            "column": self.column
        }

    def __repr__(self) -> str:
        return f"Token({self.type.value}, {repr(self.value)}, L{self.line}:C{self.column})"


class LexerError(Exception):
    """Exception raised for invalid or malformed lexical input."""
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"Lexical error at line {line}, column {column}: {message}")
        self.message = message
        self.line = line
        self.column = column


class Lexer:
    """
    Lexical analyzer for the supported C subset.
    Tracks line and column information accurately.
    """
    def __init__(self, source_code: str):
        self.source = source_code
        self.pos = 0
        self.length = len(source_code)
        self.line = 1
        self.column = 1

    def _peek(self, offset: int = 0) -> str:
        idx = self.pos + offset
        if idx < self.length:
            return self.source[idx]
        return ""

    def _advance(self) -> str:
        if self.pos >= self.length:
            return ""
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _match(self, expected: str) -> bool:
        if self._peek() == expected:
            self._advance()
            return True
        return False

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []

        while self.pos < self.length:
            ch = self._peek()

            # Skip Whitespace
            if ch in (" ", "\t", "\r", "\n"):
                self._advance()
                continue

            start_line = self.line
            start_col = self.column

            # Comments: // and /* ... */
            if ch == "/" and self._peek(1) == "/":
                # Single-line comment: skip until newline
                self._advance()  # /
                self._advance()  # /
                while self.pos < self.length and self._peek() != "\n":
                    self._advance()
                continue

            if ch == "/" and self._peek(1) == "*":
                # Multi-line comment: skip until */
                self._advance()  # /
                self._advance()  # *
                unterminated = True
                while self.pos < self.length:
                    if self._peek() == "*" and self._peek(1) == "/":
                        self._advance()  # *
                        self._advance()  # /
                        unterminated = False
                        break
                    self._advance()
                if unterminated:
                    raise LexerError("Unterminated multi-line comment '/*'", start_line, start_col)
                continue

            # Number literals (integer)
            if ch.isdigit():
                num_str = ""
                while self.pos < self.length and self._peek().isdigit():
                    num_str += self._advance()
                tokens.append(Token(TokenType.INT_LITERAL, int(num_str), start_line, start_col))
                continue

            # Identifiers and Keywords
            if ch.isalpha() or ch == "_":
                ident_str = ""
                while self.pos < self.length and (self._peek().isalnum() or self._peek() == "_"):
                    ident_str += self._advance()
                token_type = KEYWORDS.get(ident_str, TokenType.IDENTIFIER)
                tokens.append(Token(token_type, ident_str, start_line, start_col))
                continue

            # Multi-character Operators and Delimiters
            self._advance()

            # Operators starting with '+'
            if ch == "+":
                if self._match("+"):
                    tokens.append(Token(TokenType.INCREMENT, "++", start_line, start_col))
                elif self._match("="):
                    tokens.append(Token(TokenType.PLUS_ASSIGN, "+=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.PLUS, "+", start_line, start_col))

            # Operators starting with '-'
            elif ch == "-":
                if self._match("-"):
                    tokens.append(Token(TokenType.DECREMENT, "--", start_line, start_col))
                elif self._match("="):
                    tokens.append(Token(TokenType.MINUS_ASSIGN, "-=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.MINUS, "-", start_line, start_col))

            # Operators starting with '*'
            elif ch == "*":
                if self._match("="):
                    tokens.append(Token(TokenType.STAR_ASSIGN, "*=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.STAR, "*", start_line, start_col))

            # Operators starting with '/'
            elif ch == "/":
                if self._match("="):
                    tokens.append(Token(TokenType.SLASH_ASSIGN, "/=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.SLASH, "/", start_line, start_col))

            # Operators starting with '%'
            elif ch == "%":
                if self._match("="):
                    tokens.append(Token(TokenType.PERCENT_ASSIGN, "%=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.PERCENT, "%", start_line, start_col))

            # Operators starting with '='
            elif ch == "=":
                if self._match("="):
                    tokens.append(Token(TokenType.EQ, "==", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.ASSIGN, "=", start_line, start_col))

            # Operators starting with '!'
            elif ch == "!":
                if self._match("="):
                    tokens.append(Token(TokenType.NE, "!=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.LOGICAL_NOT, "!", start_line, start_col))

            # Operators starting with '<'
            elif ch == "<":
                if self._match("="):
                    tokens.append(Token(TokenType.LE, "<=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.LT, "<", start_line, start_col))

            # Operators starting with '>'
            elif ch == ">":
                if self._match("="):
                    tokens.append(Token(TokenType.GE, ">=", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.GT, ">", start_line, start_col))

            # Logical AND: &&
            elif ch == "&":
                if self._match("&"):
                    tokens.append(Token(TokenType.LOGICAL_AND, "&&", start_line, start_col))
                else:
                    raise LexerError(f"Unexpected character '&'. Did you mean '&&'?", start_line, start_col)

            # Logical OR: ||
            elif ch == "|":
                if self._match("|"):
                    tokens.append(Token(TokenType.LOGICAL_OR, "||", start_line, start_col))
                else:
                    raise LexerError(f"Unexpected character '|'. Did you mean '||'?", start_line, start_col)

            # Single-character delimiters
            elif ch == "(":
                tokens.append(Token(TokenType.LPAREN, "(", start_line, start_col))
            elif ch == ")":
                tokens.append(Token(TokenType.RPAREN, ")", start_line, start_col))
            elif ch == "{":
                tokens.append(Token(TokenType.LBRACE, "{", start_line, start_col))
            elif ch == "}":
                tokens.append(Token(TokenType.RBRACE, "}", start_line, start_col))
            elif ch == "[":
                tokens.append(Token(TokenType.LBRACKET, "[", start_line, start_col))
            elif ch == "]":
                tokens.append(Token(TokenType.RBRACKET, "]", start_line, start_col))
            elif ch == ";":
                tokens.append(Token(TokenType.SEMICOLON, ";", start_line, start_col))
            elif ch == ",":
                tokens.append(Token(TokenType.COMMA, ",", start_line, start_col))

            else:
                raise LexerError(f"Unexpected character '{ch}'", start_line, start_col)

        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens
