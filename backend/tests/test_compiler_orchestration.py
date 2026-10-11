"""
Unit tests for Compiler Orchestration module.
"""
from backend.compiler.compiler import Compiler


def test_section_11_required_demo_program():
    compiler = Compiler()
    code = """int main() {
    int arr[4] = {10, 20, 30, 40};
    int sum = 0;

    for (int i = 0; i < 4; i++) {
        sum = sum + arr[i];
    }

    return 0;
}"""
    result = compiler.compile(code)

    assert result["success"] is True
    assert result["error"] is None

    # Check stage statuses
    assert result["stages"]["lexical"]["status"] == "success"
    assert result["stages"]["syntax"]["status"] == "success"
    assert result["stages"]["semantic"]["status"] == "success"
    assert result["stages"]["ir"]["status"] == "success"
    assert result["stages"]["pim_mapping"]["status"] == "success"

    # Check tokens produced
    assert len(result["tokens"]) > 30

    # Check AST structure
    ast = result["ast"]
    assert ast["node_type"] == "Program"
    assert len(ast["body"]) == 1
    func = ast["body"][0]
    assert func["node_type"] == "FunctionDef"
    assert func["name"] == "main"

    # Check symbol table
    syms = result["symbol_table"]
    assert "main" in syms
    assert "arr" in syms
    assert syms["arr"]["is_array"] is True
    assert syms["arr"]["size"] == 4
    assert "sum" in syms

    # Check IR & PIM mapping
    assert len(result["ir"]["instructions"]) > 0
    assert result["mapping"]["pim_count"] > 0
    assert result["mapping"]["cpu_count"] > 0


def test_empty_source_code():
    compiler = Compiler()
    res = compiler.compile("")
    assert res["success"] is False
    assert res["stages"]["lexical"]["status"] == "error"
    assert res["stages"]["syntax"]["status"] == "skipped"
    assert res["stages"]["semantic"]["status"] == "skipped"
    assert res["stages"]["ir"]["status"] == "skipped"
    assert res["stages"]["pim_mapping"]["status"] == "skipped"


def test_lexical_failure_cascade():
    compiler = Compiler()
    res = compiler.compile("int x = 10 @ 5;")
    assert res["success"] is False
    assert res["stages"]["lexical"]["status"] == "error"
    assert res["stages"]["syntax"]["status"] == "skipped"
    assert res["stages"]["semantic"]["status"] == "skipped"
    assert res["stages"]["ir"]["status"] == "skipped"
    assert res["stages"]["pim_mapping"]["status"] == "skipped"


def test_syntax_failure_cascade():
    compiler = Compiler()
    res = compiler.compile("int x = 10\nint y = 20;")
    assert res["success"] is False
    assert res["stages"]["lexical"]["status"] == "success"
    assert res["stages"]["syntax"]["status"] == "error"
    assert res["stages"]["semantic"]["status"] == "skipped"
    assert res["stages"]["ir"]["status"] == "skipped"
    assert res["stages"]["pim_mapping"]["status"] == "skipped"


def test_semantic_failure_cascade():
    compiler = Compiler()
    res = compiler.compile("int x = 10; y = x + 1;")
    assert res["success"] is False
    assert res["stages"]["lexical"]["status"] == "success"
    assert res["stages"]["syntax"]["status"] == "success"
    assert res["stages"]["semantic"]["status"] == "error"
    assert res["stages"]["ir"]["status"] == "skipped"
    assert res["stages"]["pim_mapping"]["status"] == "skipped"
