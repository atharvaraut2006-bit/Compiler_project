"""
Unit tests for the Syntax Analyzer (Parser) and AST generation.
"""
import pytest
from backend.compiler.lexer import Lexer
from backend.compiler.parser import Parser, ParserError
from backend.compiler.ast_nodes import (
    Program, FunctionDef, VarDecl, ArrayDecl, ForLoop, WhileLoop,
    IfStatement, ReturnStatement, BinaryOp, ArrayAccess, Assignment
)


def parse_code(code: str) -> Program:
    tokens = Lexer(code).tokenize()
    return Parser(tokens).parse()


def test_variable_declaration():
    prog = parse_code("int a = 10; int b;")
    assert len(prog.declarations) == 2
    assert isinstance(prog.declarations[0], VarDecl)
    assert prog.declarations[0].name == "a"
    assert prog.declarations[0].initializer.value == 10
    assert isinstance(prog.declarations[1], VarDecl)
    assert prog.declarations[1].initializer is None


def test_array_declaration_with_initializer():
    prog = parse_code("int arr[4] = {10, 20, 30, 40};")
    assert len(prog.declarations) == 1
    decl = prog.declarations[0]
    assert isinstance(decl, ArrayDecl)
    assert decl.name == "arr"
    assert decl.size == 4
    assert len(decl.initializers) == 4
    assert [init.value for init in decl.initializers] == [10, 20, 30, 40]


def test_operator_precedence():
    # 2 + 3 * 4 should be 2 + (3 * 4)
    prog = parse_code("int x = 2 + 3 * 4;")
    decl = prog.declarations[0]
    expr = decl.initializer
    assert isinstance(expr, BinaryOp)
    assert expr.op == "+"
    assert expr.left.value == 2
    assert isinstance(expr.right, BinaryOp)
    assert expr.right.op == "*"
    assert expr.right.left.value == 3
    assert expr.right.right.value == 4


def test_parenthesized_expression():
    # (2 + 3) * 4
    prog = parse_code("int x = (2 + 3) * 4;")
    decl = prog.declarations[0]
    expr = decl.initializer
    assert isinstance(expr, BinaryOp)
    assert expr.op == "*"
    assert isinstance(expr.left, BinaryOp)
    assert expr.left.op == "+"


def test_for_loop_and_array_indexing():
    code = """
    for (int i = 0; i < 4; i++) {
        sum = sum + arr[i];
    }
    """
    prog = parse_code(code)
    assert len(prog.declarations) == 1
    loop = prog.declarations[0]
    assert isinstance(loop, ForLoop)
    assert isinstance(loop.init, VarDecl)
    assert loop.init.name == "i"
    assert isinstance(loop.condition, BinaryOp)
    assert loop.condition.op == "<"


def test_function_definition_main():
    code = """
    int main() {
        int x = 5;
        return x;
    }
    """
    prog = parse_code(code)
    assert len(prog.declarations) == 1
    func = prog.declarations[0]
    assert isinstance(func, FunctionDef)
    assert func.name == "main"
    assert func.return_type == "int"
    assert len(func.body.statements) == 2
    assert isinstance(func.body.statements[1], ReturnStatement)


def test_if_else_and_while_loop():
    code = """
    while (x > 0) {
        if (x == 1) {
            x = 0;
        } else {
            x = x - 1;
        }
    }
    """
    prog = parse_code(code)
    assert len(prog.declarations) == 1
    w_loop = prog.declarations[0]
    assert isinstance(w_loop, WhileLoop)
    assert isinstance(w_loop.body.statements[0], IfStatement)


def test_syntax_error_missing_semicolon():
    code = "int x = 10\nint y = 20;"
    with pytest.raises(ParserError) as exc_info:
        parse_code(code)
    assert "Expected ';'" in str(exc_info.value)


def test_syntax_error_unmatched_brace():
    code = "int main() { int x = 10;"
    with pytest.raises(ParserError) as exc_info:
        parse_code(code)
    assert "Expected '}'" in str(exc_info.value)
