"""
Unit tests for the Intermediate Representation (IR) Generator.
Tests 3AC generation, operator precedence, array indexing, and control flow.
"""
import pytest
from backend.compiler.lexer import Lexer
from backend.compiler.parser import Parser
from backend.compiler.ir_generator import IRGenerator


def _get_ir(code: str):
    tokens = Lexer(code).tokenize()
    ast = Parser(tokens).parse()
    gen = IRGenerator()
    return gen.generate(ast)


def test_simple_arithmetic_ir():
    code = """
    int main() {
        int a = 10;
        int b = 20;
        int sum = a + b;
        return 0;
    }
    """
    res = _get_ir(code)
    opcodes = [i["opcode"] for i in res["instructions"]]

    assert "DECLARE" in opcodes
    assert "CONST" in opcodes
    assert "LOAD" in opcodes
    assert "ADD" in opcodes
    assert "STORE" in opcodes
    assert "RETURN" in opcodes

    add_instr = next(i for i in res["instructions"] if i["opcode"] == "ADD")
    assert add_instr["dest"].startswith("t")


def test_operator_precedence_in_ir():
    code = """
    int main() {
        int a = 2;
        int b = 3;
        int c = 4;
        int result = a + b * c;
        return 0;
    }
    """
    res = _get_ir(code)
    opcodes = [i["opcode"] for i in res["instructions"]]

    mul_idx = opcodes.index("MUL")
    add_idx = opcodes.index("ADD")

    # Multiplication must precede addition in evaluation order
    assert mul_idx < add_idx


def test_array_access_and_indexed_load():
    code = """
    int main() {
        int arr[4] = {10, 20, 30, 40};
        int value = arr[2];
        return 0;
    }
    """
    res = _get_ir(code)
    opcodes = [i["opcode"] for i in res["instructions"]]

    assert "STORE_INDEXED" in opcodes
    assert "LOAD_INDEXED" in opcodes

    load_idx_instr = next(i for i in res["instructions"] if i["opcode"] == "LOAD_INDEXED")
    assert load_idx_instr["arg1"] == "arr"
    assert load_idx_instr["metadata"]["operation_type"] == "memory_load"


def test_array_indexed_store():
    code = """
    int main() {
        int arr[4] = {1, 2, 3, 4};
        arr[1] = 10;
        return 0;
    }
    """
    res = _get_ir(code)
    store_indexed = [i for i in res["instructions"] if i["opcode"] == "STORE_INDEXED"]
    assert len(store_indexed) >= 5  # 4 initializers + 1 update


def test_for_loop_control_flow():
    code = """
    int main() {
        int sum = 0;
        for (int i = 0; i < 4; i++) {
            sum = sum + i;
        }
        return 0;
    }
    """
    res = _get_ir(code)
    opcodes = [i["opcode"] for i in res["instructions"]]

    assert "LABEL" in opcodes
    assert "BRANCH" in opcodes
    assert "JUMP" in opcodes
    assert "COMPARE_LT" in opcodes


def test_deterministic_ir_output():
    code = """
    int main() {
        int a = 10;
        int b = 20;
        int c = a + b * 2;
        return c;
    }
    """
    res1 = _get_ir(code)
    res2 = _get_ir(code)

    assert res1["formatted"] == res2["formatted"]
    assert len(res1["instructions"]) == len(res2["instructions"])
    for i1, i2 in zip(res1["instructions"], res2["instructions"]):
        assert i1["dest"] == i2["dest"]
        assert i1["opcode"] == i2["opcode"]
        assert i1["arg1"] == i2["arg1"]
        assert i1["arg2"] == i2["arg2"]


def test_while_and_if_else_ir():
    code = """
    int x = 10;
    while (x > 0) {
        if (x == 5) {
            print(x);
        } else {
            x = x - 1;
        }
    }
    """
    res = _get_ir(code)
    opcodes = [i["opcode"] for i in res["instructions"]]

    assert "BRANCH" in opcodes
    assert "COMPARE_GT" in opcodes
    assert "COMPARE_EQ" in opcodes
    assert "PRINT" in opcodes
    assert "JUMP" in opcodes
