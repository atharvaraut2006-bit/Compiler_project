"""
Lexical Analyzer (Lexer) for C Compiler Front End with Extended C Support.
Produces ordered tokens with type, category, lexeme, line, and column.
Includes preprocessor handling for #include, #define, and imports.
"""
from enum import Enum
import re
from typing import List, Optional, Any, Dict, Tuple


class TokenType(str, Enum):
    # Keywords
    INT = "INT"
    RETURN = "RETURN"
    FOR = "FOR"
    WHILE = "WHILE"
    IF = "IF"
    ELSE = "ELSE"
    PRINT = "PRINT"
    FLOAT = "FLOAT"
    DOUBLE = "DOUBLE"
    VOID = "VOID"
    CHAR = "CHAR"
    STRUCT = "STRUCT"
    UNION = "UNION"
    CONST_KW = "CONST_KW"
    SIZEOF = "SIZEOF"
    AUTO = "AUTO"
    STATIC = "STATIC"

    # Identifiers & Literals
    IDENTIFIER = "IDENTIFIER"
    INT_LITERAL = "INT_LITERAL"
    FLOAT_LITERAL = "FLOAT_LITERAL"
    STRING_LITERAL = "STRING_LITERAL"
    CHAR_LITERAL = "CHAR_LITERAL"

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

    # Bitwise & Pointer Operators
    AMPERSAND = "AMPERSAND"     # & (address-of / bitwise AND)
    PIPE = "PIPE"               # | (bitwise OR)
    CARET = "CARET"             # ^ (bitwise XOR)
    TILDE = "TILDE"             # ~ (bitwise NOT)
    ARROW = "ARROW"             # -> (struct pointer member access)
    DOT = "DOT"                 # . (struct member access)

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
    "float": TokenType.FLOAT,
    "double": TokenType.DOUBLE,
    "void": TokenType.VOID,
    "char": TokenType.CHAR,
    "struct": TokenType.STRUCT,
    "union": TokenType.UNION,
    "const": TokenType.CONST_KW,
    "sizeof": TokenType.SIZEOF,
    "auto": TokenType.AUTO,
    "static": TokenType.STATIC,
}


class Token:
    """Represents a lexical token."""
    def __init__(self, type_: TokenType, value: Any, line: int, column: int):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    @property
    def category(self) -> str:
        """Explicit classification: keyword, identifier, operator, delimeter, numeric literal, string literal."""
        if self.type in (
            TokenType.INT, TokenType.RETURN, TokenType.FOR, TokenType.WHILE,
            TokenType.IF, TokenType.ELSE, TokenType.PRINT, TokenType.FLOAT,
            TokenType.DOUBLE, TokenType.VOID, TokenType.CHAR, TokenType.STRUCT,
            TokenType.UNION, TokenType.CONST_KW, TokenType.SIZEOF, TokenType.AUTO,
            TokenType.STATIC
        ):
            return "keyword"
        if self.type == TokenType.IDENTIFIER:
            return "identifier"
        if self.type in (TokenType.INT_LITERAL, TokenType.FLOAT_LITERAL):
            return "numeric literal"
        if self.type in (TokenType.STRING_LITERAL, TokenType.CHAR_LITERAL):
            return "string literal"
        if self.type in (
            TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH, TokenType.PERCENT,
            TokenType.INCREMENT, TokenType.DECREMENT,
            TokenType.ASSIGN, TokenType.PLUS_ASSIGN, TokenType.MINUS_ASSIGN,
            TokenType.STAR_ASSIGN, TokenType.SLASH_ASSIGN, TokenType.PERCENT_ASSIGN,
            TokenType.LT, TokenType.LE, TokenType.GT, TokenType.GE, TokenType.EQ, TokenType.NE,
            TokenType.LOGICAL_AND, TokenType.LOGICAL_OR, TokenType.LOGICAL_NOT,
            TokenType.AMPERSAND, TokenType.PIPE, TokenType.CARET, TokenType.TILDE,
            TokenType.ARROW, TokenType.DOT
        ):
            return "operator"
        if self.type in (
            TokenType.LPAREN, TokenType.RPAREN, TokenType.LBRACE, TokenType.RBRACE,
            TokenType.LBRACKET, TokenType.RBRACKET, TokenType.SEMICOLON, TokenType.COMMA, TokenType.EOF
        ):
            return "delimeter"
        return "delimeter"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "category": self.category,
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


def preprocess_c_source(source_code: str) -> Tuple[str, Dict[str, Any]]:
    """
    C Preprocessor pass:
    - Extracts and handles #include directives (e.g. #include <stdio.h>, #include "header.h")
    - Extracts and handles #define macros with identifier replacement
    - Handles import modules (e.g. import module;)
    - Preserves exact line numbers by replacing directive lines with empty spaces.
    """
    lines = source_code.splitlines(keepends=True)
    macros: Dict[str, str] = {}
    includes: List[str] = []
    processed_lines = []

    for line in lines:
        stripped = line.strip()
        # Preprocessor directive starting with #
        if stripped.startswith("#"):
            if stripped.startswith("#include"):
                # e.g., #include <stdio.h> or #include "mylib.h"
                m = re.search(r'#include\s*[<"]([^>"]+)[>"]', stripped)
                if m:
                    includes.append(m.group(1))
                # Preserve line count: blank line with newline
                processed_lines.append("\n" if line.endswith("\n") else "")
                continue

            elif stripped.startswith("#define"):
                # e.g., #define N 100 or #define PI 3.14
                parts = stripped.split(maxsplit=2)
                if len(parts) >= 3:
                    macro_name = parts[1]
                    macro_val = parts[2]
                    macros[macro_name] = macro_val
                processed_lines.append("\n" if line.endswith("\n") else "")
                continue

            elif any(stripped.startswith(d) for d in ("#pragma", "#ifdef", "#ifndef", "#endif", "#undef", "#else", "#elif")):
                # Conditional compilation and pragmas - blank line
                processed_lines.append("\n" if line.endswith("\n") else "")
                continue

        # Import modules (e.g., import math; or from os import path;)
        elif stripped.startswith("import ") or stripped.startswith("from "):
            mod_name = stripped.split(";")[0].replace("import", "").replace("from", "").strip()
            includes.append(mod_name)
            processed_lines.append("\n" if line.endswith("\n") else "")
            continue

        # Normal line: apply macro substitutions if any defined
        curr_line = line
        for m_name, m_val in macros.items():
            curr_line = re.sub(r'\b' + re.escape(m_name) + r'\b', m_val, curr_line)
        processed_lines.append(curr_line)

    preprocessed_code = "".join(processed_lines)
    metadata = {
        "includes": includes,
        "macros": macros
    }
    return preprocessed_code, metadata


class Lexer:
    """
    Lexical analyzer for C code with extended language features.
    Tracks line and column information accurately.
    """
    def __init__(self, source_code: str):
        # Run preprocessor pass first, preserving exact line coordinates
        self.preprocessed_code, self.preprocessor_meta = preprocess_c_source(source_code)
        self.source = self.preprocessed_code
        self.pos = 0
        self.length = len(self.source)
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
                self._advance()  # /
                self._advance()  # /
                while self.pos < self.length and self._peek() != "\n":
                    self._advance()
                continue

            if ch == "/" and self._peek(1) == "*":
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

            # String Literals: "..."
            if ch == '"':
                self._advance()  # opening quote
                str_val = ""
                while self.pos < self.length and self._peek() != '"':
                    if self._peek() == "\n":
                        break
                    if self._peek() == "\\":
                        self._advance()
                        esc = self._advance()
                        if esc == "n":
                            str_val += "\n"
                        elif esc == "t":
                            str_val += "\t"
                        elif esc == "r":
                            str_val += "\r"
                        elif esc == '"':
                            str_val += '"'
                        elif esc == "\\":
                            str_val += "\\"
                        else:
                            str_val += esc
                    else:
                        str_val += self._advance()
                if self._peek() == '"':
                    self._advance()  # closing quote
                tokens.append(Token(TokenType.STRING_LITERAL, str_val, start_line, start_col))
                continue

            # Character Literals: '...'
            if ch == "'":
                self._advance()  # opening '
                char_val = ""
                if self.pos < self.length and self._peek() != "'":
                    if self._peek() == "\\":
                        self._advance()
                        esc = self._advance()
                        char_val = "\n" if esc == "n" else ("\t" if esc == "t" else esc)
                    else:
                        char_val = self._advance()
                if self._peek() == "'":
                    self._advance()  # closing '
                tokens.append(Token(TokenType.CHAR_LITERAL, char_val, start_line, start_col))
                continue

            # Number Literals: Integers or Floats (e.g. 42, 3.14, .5, 1e-3)
            if ch.isdigit() or (ch == "." and self._peek(1).isdigit()):
                num_str = ""
                is_float = False
                if ch == ".":
                    is_float = True
                    num_str += self._advance()
                while self.pos < self.length and self._peek().isdigit():
                    num_str += self._advance()
                if not is_float and self._peek() == "." and self._peek(1).isdigit():
                    is_float = True
                    num_str += self._advance()  # '.'
                    while self.pos < self.length and self._peek().isdigit():
                        num_str += self._advance()
                # Scientific notation exponent
                if self._peek() in ("e", "E"):
                    is_float = True
                    num_str += self._advance()
                    if self._peek() in ("+", "-"):
                        num_str += self._advance()
                    while self.pos < self.length and self._peek().isdigit():
                        num_str += self._advance()
                # Optional float suffix 'f' or 'F'
                if self._peek() in ("f", "F", "l", "L"):
                    self._advance()

                if is_float:
                    tokens.append(Token(TokenType.FLOAT_LITERAL, float(num_str), start_line, start_col))
                else:
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

            # Multi-character & Single-character Operators and Delimiters
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
                if self._match(">"):
                    tokens.append(Token(TokenType.ARROW, "->", start_line, start_col))
                elif self._match("-"):
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

            # Logical AND or Address-of / Bitwise AND: & / &&
            elif ch == "&":
                if self._match("&"):
                    tokens.append(Token(TokenType.LOGICAL_AND, "&&", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.AMPERSAND, "&", start_line, start_col))

            # Logical OR or Bitwise OR: | / ||
            elif ch == "|":
                if self._match("|"):
                    tokens.append(Token(TokenType.LOGICAL_OR, "||", start_line, start_col))
                else:
                    tokens.append(Token(TokenType.PIPE, "|", start_line, start_col))

            # Bitwise XOR: ^
            elif ch == "^":
                tokens.append(Token(TokenType.CARET, "^", start_line, start_col))

            # Bitwise NOT: ~
            elif ch == "~":
                tokens.append(Token(TokenType.TILDE, "~", start_line, start_col))

            # Dot for struct member access: .
            elif ch == ".":
                tokens.append(Token(TokenType.DOT, ".", start_line, start_col))

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

            # Stray # directive handling if not at beginning of line
            elif ch == "#":
                # Consume directive line safely
                while self.pos < self.length and self._peek() != "\n":
                    self._advance()
                continue

            else:
                raise LexerError(f"Unexpected character '{ch}'", start_line, start_col)

        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens
