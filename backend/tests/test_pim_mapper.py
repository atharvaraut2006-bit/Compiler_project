"""
Unit tests for the centralized PIM Instruction Eligibility Policy and Mapper.
Tests each supported operation, each fallback operation, array-access restrictions,
and mixed CPU/PIM execution in loops.
"""
import pytest
from backend.compiler.lexer import Lexer
from backend.compiler.parser import Parser
from backend.compiler.ir_generator import IRGenerator
from backend.compiler.pim_mapper import PIMMapper, PIMPolicy


def _get_mapping(code: str):
    tokens = Lexer(code).tokenize()
    ast = Parser(tokens).parse()
    ir_res = IRGenerator().generate(ast)
    mapper = PIMMapper()
    return mapper.map_instructions(ir_res["instructions"])


def test_each_supported_pim_arithmetic_operation():
    """Verify ADD -> PIM_ADD, SUB -> PIM_SUB, MUL -> PIM_MUL."""
    code = """
    int main() {
        int a = 10;
        int b = 20;
        int sum = a + b;
        int diff = a - b;
        int prod = a * b;
        return 0;
    }
    """
    mapping = _get_mapping(code)
    pim_ops = [i["mapped_instruction"] for i in mapping["instructions"] if i["target"] == "PIM"]

    assert "PIM_ADD" in pim_ops
    assert "PIM_SUB" in pim_ops
    assert "PIM_MUL" in pim_ops


def test_supported_pim_comparisons():
    """Verify comparisons map to PIM_COMPARE."""
    code = """
    int a = 5;
    int b = 10;
    if (a < b) {
        a = a + 1;
    }
    if (a >= b) {
        a = a - 1;
    }
    if (a == b) {
        a = 0;
    }
    """
    mapping = _get_mapping(code)
    cmps = [i for i in mapping["instructions"] if i["mapped_instruction"] == "PIM_COMPARE"]
    assert len(cmps) >= 3
    for c in cmps:
        assert c["target"] == "PIM"
        assert "comparator circuit" in c["reason"].lower()


def test_supported_pim_array_memory_operations():
    """Verify LOAD_INDEXED -> PIM_LOAD and STORE_INDEXED -> PIM_STORE."""
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

    load_item = next(i for i in mapping["instructions"] if i["mapped_instruction"] == "PIM_LOAD")
    assert load_item["memory_metadata"]["memory_region"] == "array_buffer"
    assert "row buffer" in load_item["reason"]


def test_each_fallback_operation_div_and_mod():
    """Verify DIV -> CPU_DIV and MOD -> CPU_MOD with divider hardware rationales."""
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
    assert "divider hardware" in mod_instr["reason"]


def test_fallback_control_flow_and_returns():
    """Verify loop conditions, branches, jumps, labels, and returns route to CPU."""
    code = """
    int main() {
        int sum = 0;
        for (int i = 0; i < 4; i++) {
            sum += i;
        }
        return sum;
    }
    """
    mapping = _get_mapping(code)

    branch_instr = next(i for i in mapping["instructions"] if i["ir_opcode"] == "BRANCH")
    jump_instr = next(i for i in mapping["instructions"] if i["ir_opcode"] == "JUMP")
    ret_instr = next(i for i in mapping["instructions"] if i["ir_opcode"] == "RETURN")
    decl_instr = next(i for i in mapping["instructions"] if i["ir_opcode"] == "DECLARE")

    assert branch_instr["target"] == "CPU"
    assert jump_instr["target"] == "CPU"
    assert ret_instr["target"] == "CPU"
    assert decl_instr["target"] == "CPU"


def test_array_access_restrictions_vs_scalar_access():
    """
    Verify explicit memory-access eligibility:
    - Array indexed access (LOAD_INDEXED, STORE_INDEXED) -> PIM
    - Scalar variable access (LOAD, STORE) -> CPU Fallback
    """
    code = """
    int main() {
        int arr[2] = {5, 10};
        int x = arr[0];
        arr[1] = x;
        return x;
    }
    """
    mapping = _get_mapping(code)

    # Array access
    load_indexed = next(i for i in mapping["instructions"] if i["ir_opcode"] == "LOAD_INDEXED")
    store_indexed = next(i for i in mapping["instructions"] if i["ir_opcode"] == "STORE_INDEXED")
    assert load_indexed["target"] == "PIM"
    assert store_indexed["target"] == "PIM"

    # Scalar access
    scalar_load = next(i for i in mapping["instructions"] if i["ir_opcode"] == "LOAD" and i["arg1"] == "x")
    scalar_store = next(i for i in mapping["instructions"] if i["ir_opcode"] == "STORE" and i["dest"] == "x")
    assert scalar_load["target"] == "CPU"
    assert scalar_store["target"] == "CPU"
    assert "stack" in scalar_load["reason"].lower()


def test_mixed_cpu_pim_execution_in_loops():
    """
    Verify mixed-execution programs:
    - Loop execution / sequencing (BRANCH, JUMP, LABEL) is CPU-controlled.
    - Eligible arithmetic (ADD) and memory operations (LOAD_INDEXED) inside the loop are PIM-mapped.
    """
    code = """
    int main() {
        int arr[4] = {10, 20, 30, 40};
        int sum = 0;
        for (int i = 0; i < 4; i++) {
            sum = sum + arr[i];
        }
        return sum;
    }
    """
    mapping = _get_mapping(code)

    # CPU handles loop control
    cpu_ops = [i["mapped_instruction"] for i in mapping["instructions"] if i["target"] == "CPU"]
    assert "CPU_BRANCH" in cpu_ops
    assert "CPU_JUMP" in cpu_ops
    assert "LABEL" in cpu_ops

    # PIM handles computation inside loop body
    pim_ops = [i["mapped_instruction"] for i in mapping["instructions"] if i["target"] == "PIM"]
    assert "PIM_LOAD" in pim_ops
    assert "PIM_ADD" in pim_ops
    assert "PIM_STORE" in pim_ops


def test_unsupported_operation_fallback():
    """Verify any unsupported or unknown instruction defaults safely to CPU fallback."""
    mapper = PIMMapper()
    fake_instr = [{
        "id": "ir_999",
        "opcode": "UNKNOWN_OP",
        "dest": "t1",
        "arg1": "t2",
        "metadata": {}
    }]
    res = mapper.map_instructions(fake_instr)
    assert len(res["instructions"]) == 1
    item = res["instructions"][0]
    assert item["target"] == "CPU"
    assert item["mapped_instruction"] == "CPU_UNKNOWN_OP"
    assert "not explicitly supported" in item["reason"]
