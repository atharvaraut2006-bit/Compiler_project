"""
Unit and integration tests for extended C constructs:
- Preprocessor directives (#include <stdio.h>, #define, #pragma, import)
- Custom modular function definitions and calls
- Standard library functions (printf, malloc, free)
- Pointers and address-of arithmetic (*p, &x)
- Floating point types (float, double)
- Structs and member access
- Multi-tier PIM acceleration vs CPU fallback
"""
import pytest
from backend.compiler.lexer import Lexer
from backend.compiler.parser import Parser
from backend.compiler.semantic import SemanticAnalyzer
from backend.compiler.ir_generator import IRGenerator
from backend.compiler.pim_mapper import PIMMapper
from backend.compiler.compiler import Compiler


def test_preprocessor_includes_and_defines():
    code = """#include <stdio.h>
#include <stdlib.h>
#define SIZE 4
#pragma once

int main() {
    int arr[SIZE] = {1, 2, 3, 4};
    int sum = 0;
    for (int i = 0; i < SIZE; i++) {
        sum += arr[i];
    }
    printf("Sum: %d\\n", sum);
    return 0;
}
"""
    compiler = Compiler()
    res = compiler.compile(code)
    assert res["success"] is True, f"Compilation failed: {res.get('error')}"
    assert len(res["ir"]["instructions"]) > 0
    # Array load should be in PIM
    pim_ops = [i["mapped_instruction"] for i in res["mapping"]["instructions"] if i["target"] == "PIM"]
    assert "PIM_LOAD" in pim_ops
    # printf call should be CPU fallback
    cpu_ops = [i["mapped_instruction"] for i in res["mapping"]["instructions"] if i["target"] == "CPU"]
    assert "CPU_CALL" in cpu_ops


def test_custom_function_definition_and_call():
    code = """#include <stdio.h>

int multiply_by_two(int val) {
    return val * 2;
}

int main() {
    int arr[3] = {10, 20, 30};
    int res = multiply_by_two(arr[0]);
    return 0;
}
"""
    compiler = Compiler()
    res = compiler.compile(code)
    assert res["success"] is True
    # Verify FUNC_multiply_by_two label in IR
    labels = [i["arg1"] for i in res["ir"]["instructions"] if i["opcode"] == "LABEL"]
    assert "FUNC_multiply_by_two" in labels
    # Verify CALL in IR
    calls = [i for i in res["ir"]["instructions"] if i["opcode"] == "CALL"]
    assert len(calls) == 1
    assert calls[0]["arg1"] == "multiply_by_two"


def test_pointers_and_address_of():
    code = """
int main() {
    int x = 42;
    int *p = &x;
    int y = *p;
    *p = 100;
    return 0;
}
"""
    compiler = Compiler()
    res = compiler.compile(code)
    assert res["success"] is True
    opcodes = [i["opcode"] for i in res["ir"]["instructions"]]
    assert "ADDRESS_OF" in opcodes
    assert "LOAD_PTR" in opcodes
    assert "STORE_PTR" in opcodes

    # All pointer ops should map to CPU fallback
    for instr in res["mapping"]["instructions"]:
        if instr["ir_opcode"] in ("ADDRESS_OF", "LOAD_PTR", "STORE_PTR"):
            assert instr["target"] == "CPU"
            assert instr["memory_metadata"]["memory_region"] == "host_cache"


def test_floating_point_numbers():
    code = """
int main() {
    float pi = 3.14;
    float radius = 2.5;
    float area = pi * radius;
    return 0;
}
"""
    compiler = Compiler()
    res = compiler.compile(code)
    assert res["success"] is True
    consts = [i for i in res["ir"]["instructions"] if i["opcode"] == "CONST"]
    assert any(c["metadata"].get("data_type") == "float" for c in consts)


def test_struct_definition_and_access():
    code = """
struct Point {
    int x;
    int y;
};

int main() {
    struct Point p;
    p.x = 10;
    int val = p.x;
    return 0;
}
"""
    compiler = Compiler()
    res = compiler.compile(code)
    assert res["success"] is True
    opcodes = [i["opcode"] for i in res["ir"]["instructions"]]
    assert "STRUCT_DEF" in opcodes
    assert "STORE_FIELD" in opcodes
    assert "LOAD_FIELD" in opcodes
