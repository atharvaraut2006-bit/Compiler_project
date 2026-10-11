"""
Unit tests for Semantic Analysis and Symbol Table management.
"""
from backend.compiler.lexer import Lexer
from backend.compiler.parser import Parser
from backend.compiler.semantic import SemanticAnalyzer


def analyze_code(code: str):
    tokens = Lexer(code).tokenize()
    ast = Parser(tokens).parse()
    analyzer = SemanticAnalyzer()
    return analyzer.analyze(ast)


def test_valid_program_semantic():
    code = """
    int main() {
        int arr[4] = {10, 20, 30, 40};
        int sum = 0;
        for (int i = 0; i < 4; i++) {
            sum += arr[i];
        }
        return 0;
    }
    """
    res = analyze_code(code)
    assert res["success"] is True
    assert res["error_count"] == 0
    assert "arr" in res["symbols"]
    assert res["symbols"]["arr"]["is_array"] is True
    assert res["symbols"]["arr"]["size"] == 4


def test_undeclared_variable_error():
    code = """
    int x = 10;
    total = x + 5;
    """
    res = analyze_code(code)
    assert res["success"] is False
    assert any("Undeclared variable 'total'" in d["message"] for d in res["diagnostics"])


def test_duplicate_declaration_error():
    code = """
    int x = 10;
    int x = 20;
    """
    res = analyze_code(code)
    assert res["success"] is False
    assert any("Redeclaration of variable 'x'" in d["message"] for d in res["diagnostics"])


def test_indexing_scalar_variable_error():
    code = """
    int scalar = 42;
    int val = scalar[0];
    """
    res = analyze_code(code)
    assert res["success"] is False
    assert any("Cannot index non-array" in d["message"] for d in res["diagnostics"])


def test_array_initializer_overflow_error():
    code = "int arr[3] = {1, 2, 3, 4, 5};"
    res = analyze_code(code)
    assert res["success"] is False
    assert any("exceeding declared size" in d["message"] for d in res["diagnostics"])


def test_static_array_bounds_check():
    code = """
    int arr[4] = {10, 20, 30, 40};
    int bad = arr[10];
    """
    res = analyze_code(code)
    assert res["success"] is False
    assert any("out of bounds" in d["message"] for d in res["diagnostics"])


def test_division_by_zero_constant_check():
    code = "int x = 100 / 0;"
    res = analyze_code(code)
    assert res["success"] is False
    assert any("Division by zero" in d["message"] for d in res["diagnostics"])
