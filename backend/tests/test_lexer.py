"""
Unit tests for the Lexical Analyzer (Lexer).
"""
import pytest
from backend.compiler.lexer import Lexer, TokenType, LexerError


def test_keywords_and_identifiers():
    code = "int main return for while if else print my_var _temp var2"
    tokens = Lexer(code).tokenize()
    types = [t.type for t in tokens[:-1]]  # exclude EOF
    assert types == [
        TokenType.INT,
        TokenType.IDENTIFIER,
        TokenType.RETURN,
        TokenType.FOR,
        TokenType.WHILE,
        TokenType.IF,
        TokenType.ELSE,
        TokenType.PRINT,
        TokenType.IDENTIFIER,
        TokenType.IDENTIFIER,
        TokenType.IDENTIFIER,
    ]
    assert tokens[1].value == "main"
    assert tokens[8].value == "my_var"


def test_integer_literals():
    code = "0 42 1000 9999"
    tokens = Lexer(code).tokenize()
    vals = [t.value for t in tokens if t.type == TokenType.INT_LITERAL]
    assert vals == [0, 42, 1000, 9999]


def test_operators():
    code = "+ - * / % ++ -- = += -= *= /= == != < <= > >= && || !"
    tokens = Lexer(code).tokenize()
    types = [t.type for t in tokens[:-1]]
    assert types == [
        TokenType.PLUS,
        TokenType.MINUS,
        TokenType.STAR,
        TokenType.SLASH,
        TokenType.PERCENT,
        TokenType.INCREMENT,
        TokenType.DECREMENT,
        TokenType.ASSIGN,
        TokenType.PLUS_ASSIGN,
        TokenType.MINUS_ASSIGN,
        TokenType.STAR_ASSIGN,
        TokenType.SLASH_ASSIGN,
        TokenType.EQ,
        TokenType.NE,
        TokenType.LT,
        TokenType.LE,
        TokenType.GT,
        TokenType.GE,
        TokenType.LOGICAL_AND,
        TokenType.LOGICAL_OR,
        TokenType.LOGICAL_NOT,
    ]


def test_delimiters():
    code = "( ) { } [ ] ; ,"
    tokens = Lexer(code).tokenize()
    types = [t.type for t in tokens[:-1]]
    assert types == [
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.LBRACE,
        TokenType.RBRACE,
        TokenType.LBRACKET,
        TokenType.RBRACKET,
        TokenType.SEMICOLON,
        TokenType.COMMA,
    ]


def test_comments():
    code = """
    // Single line comment
    int x = 10; /* Multi-line
    block comment */ int y = 20;
    // Another comment
    """
    tokens = Lexer(code).tokenize()
    types = [t.type for t in tokens[:-1]]
    assert types == [
        TokenType.INT,
        TokenType.IDENTIFIER,
        TokenType.ASSIGN,
        TokenType.INT_LITERAL,
        TokenType.SEMICOLON,
        TokenType.INT,
        TokenType.IDENTIFIER,
        TokenType.ASSIGN,
        TokenType.INT_LITERAL,
        TokenType.SEMICOLON,
    ]


def test_line_and_column_tracking():
    code = "int x;\n  int y = 5;"
    tokens = Lexer(code).tokenize()
    # int at line 1, col 1
    assert tokens[0].line == 1 and tokens[0].column == 1
    # x at line 1, col 5
    assert tokens[1].line == 1 and tokens[1].column == 5
    # int at line 2, col 3
    assert tokens[3].line == 2 and tokens[3].column == 3


def test_invalid_characters_error():
    code = "int x = 10 @ 5;"
    with pytest.raises(LexerError) as exc_info:
        Lexer(code).tokenize()
    assert "@" in str(exc_info.value)
    assert exc_info.value.line == 1
    assert exc_info.value.column == 12


def test_unterminated_multiline_comment():
    code = "int x = 10; /* unclosed comment"
    with pytest.raises(LexerError) as exc_info:
        Lexer(code).tokenize()
    assert "Unterminated" in str(exc_info.value)
