"""
Unit tests for the PIM Eligibility Analyzer & Instruction Mapper.
Tests PIM mappings, CPU fallbacks, explanations, and metrics consistency.
"""
import pytest
from backend.compiler.lexer import Lexer
from backend.compiler.parser import Parser
from backend.compiler.ir_generator import IRGenerator
from backend.compiler.pim_mapper import PIMMapper


def _get_mapping(code: str):
    tokens = Lexer(code).tokenize()
    ast = Parser(tokens).parse()
    ir_res = IRGenerator().generate(ast)
    mapper = PIMMapper()
    return mapper.map_instructions(ir_res["instructions"])


def test_arithmetic_mapping_to_pim():
    code = """
    int main() {
        int a = 10;
        int b = 20;
        int c = a + b;
        int d = a * b;
        int e = a - b;
        return 0;
    }
    """
    mapping = _get_mapping(code)
    pim_ops = [i["mapped_instruction"] for i in mapping["instructions"] if i["target"] == "PIM"]

    assert "PIM_ADD" in pim_ops
    assert "PIM_MUL" in pim_ops
    assert "PIM_SUB" in pim_ops


def test_division_and_modulo_cpu_fallback():
    code = """
    int main() {
        int a = 100;
        int b = 5;
        int c = a / b;
        int d = a % b;
        return 0;
    }
    """
    mapping = _get_mapping(code)

    div_instr = next(i for i in mapping["instructions"] if i["ir_opcode"] == "DIV")
    mod_instr = next(i for i in mapping["instructions"] if i["ir_opcode"] == "MOD")

    assert div_instr["target"] == "CPU"
    assert div_instr["mapped_instruction"] == "CPU_DIV"
    assert "divider hardware" in div_instr["reason"]

    assert mod_instr["target"] == "CPU"
    assert mod_instr["mapped_instruction"] == "CPU_MOD"


def test_array_operations_pim_mapping():
    code = """
    int main() {
        int arr[4] = {10, 20, 30, 40};
        int val = arr[2];
        arr[0] = 99;
        return 0;
    }
    """
    mapping = _get_mapping(code)
    pim_ops = [i["mapped_instruction"] for i in mapping["instructions"] if i["target"] == "PIM"]

    assert "PIM_LOAD" in pim_ops
    assert "PIM_STORE" in pim_ops


def test_comparisons_mapped_to_pim():
    code = """
    int a = 5;
    int b = 10;
    if (a < b) {
        a = a + 1;
    }
    """
    mapping = _get_mapping(code)
    cmp_instr = next(i for i in mapping["instructions"] if i["ir_opcode"] == "COMPARE_LT")

    assert cmp_instr["target"] == "PIM"
    assert cmp_instr["mapped_instruction"] == "PIM_COMPARE"


def test_control_flow_cpu_fallback():
    code = """
    int sum = 0;
    for (int i = 0; i < 4; i++) {
        sum = sum + i;
    }
    """
    mapping = _get_mapping(code)
    branch_instrs = [i for i in mapping["instructions"] if i["ir_opcode"] in ("BRANCH", "JUMP")]

    for b in branch_instrs:
        assert b["target"] == "CPU"
        assert "control unit" in b["reason"].lower()


def test_every_instruction_has_reason():
    code = """
    int main() {
        int arr[4] = {10, 20, 30, 40};
        int sum = 0;
        for (int i = 0; i < 4; i++) {
            sum += arr[i];
        }
        return sum;
    }
    """
    mapping = _get_mapping(code)
    for instr in mapping["instructions"]:
        assert "reason" in instr
        assert len(instr["reason"].strip()) > 0
        assert instr["target"] in ("PIM", "CPU")


def test_mapping_summary_metrics():
    code = """
    int x = 10;
    int y = 20;
    int z = x + y;
    """
    mapping = _get_mapping(code)
    total = mapping["total_instructions"]
    pim = mapping["pim_count"]
    cpu = mapping["cpu_count"]

    assert total == pim + cpu
    assert mapping["unsupported_count"] == 0
