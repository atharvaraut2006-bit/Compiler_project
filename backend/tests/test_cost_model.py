"""
Unit tests for the Research-Informed Analytical Cost Model and Workload Optimization Pass.
Verifies:
1. Small workloads select CPU execution due to synchronization overhead.
2. Large array memory-bound workloads select PIM offload due to transfer savings.
3. Unsupported operations correctly fall back to CPU.
4. Exact mathematical correctness of the 4-term cost formula.
5. Access pattern analysis (sequential vs strided) and layout transformation evaluation.
6. Explicit representation of unknown quantities (None instead of invented numbers).
7. Integration with the Compiler orchestrator and PIMMapper.
"""
import pytest
from backend.compiler.lexer import Lexer
from backend.compiler.parser import Parser
from backend.compiler.ir_generator import IRGenerator
from backend.compiler.pim_mapper import PIMMapper
from backend.compiler.cost_model import WorkloadAnalyzer, PIMCostModel, CostParameters
from backend.compiler.compiler import Compiler


def _compile_code(code: str):
    tokens = Lexer(code).tokenize()
    ast = Parser(tokens).parse()
    ir_res = IRGenerator().generate(ast)
    return ast, ir_res


def test_small_scalar_workload_selects_cpu():
    """
    Small workload: single scalar addition.
    PIM launch synchronization overhead (60 cycles) exceeds compute benefit,
    so cost-aware optimization must select CPU_ONLY.
    """
    code = """
    int main() {
        int a = 10;
        int b = 20;
        int c = a + b;
        return 0;
    }
    """
    ast, ir_res = _compile_code(code)
    mapper = PIMMapper()
    mapping = mapper.map_instructions(ir_res["instructions"], ast=ast)

    opt = mapping["optimization"]
    assert opt["selected_strategy"] == "CPU_ONLY"
    assert opt["offload_beneficial"] is False
    assert "CPU execution selected" in opt["decision_rationale"]

    # In default mode, structural capability remains PIM_ADD, but optimal_target is CPU
    add_instr = next(i for i in mapping["instructions"] if i["ir_opcode"] == "ADD")
    assert add_instr["target"] == "PIM"  # Structural capability
    assert add_instr["optimal_target"] == "CPU"  # Cost-aware assignment
    assert "overhead" in add_instr["cost_justification"].lower() or "cpu" in add_instr["cost_justification"].lower()


def test_large_array_workload_selects_pim():
    """
    Large memory-bound workload: 100-element array sum in a loop.
    400 bytes of memory bus data movement are eliminated by in-situ PIM execution.
    Cost model must select DIRECT_PIM with estimated speedup > 1.0x.
    """
    code = """
    int main() {
        int arr[100];
        int sum = 0;
        for (int i = 0; i < 100; i = i + 1) {
            sum += arr[i];
        }
        return sum;
    }
    """
    ast, ir_res = _compile_code(code)
    mapper = PIMMapper()
    mapping = mapper.map_instructions(ir_res["instructions"], ast=ast)

    opt = mapping["optimization"]
    assert opt["selected_strategy"] == "DIRECT_PIM"
    assert opt["offload_beneficial"] is True
    assert opt["speedup_estimate"] > 1.0
    assert "Direct PIM offload selected" in opt["decision_rationale"]

    # Verify candidate costs
    cpu_cand = opt["candidates"]["CPU_ONLY"]
    pim_cand = opt["candidates"]["DIRECT_PIM"]
    assert pim_cand["total_cost"] < cpu_cand["total_cost"]
    assert pim_cand["synchronization_cost"] == 60.0
    assert cpu_cand["transfer_cost"] > pim_cand["transfer_cost"]


def test_unsupported_operations_fallback_to_cpu():
    """
    Workload with division (DIV):
    PIM hardware model does not support division; PIM candidate is marked invalid,
    and system falls back to CPU_ONLY.
    """
    code = """
    int main() {
        int arr[50];
        int sum = 0;
        for (int i = 0; i < 50; i = i + 1) {
            sum = sum + arr[i] / 2;
        }
        return sum;
    }
    """
    ast, ir_res = _compile_code(code)
    mapper = PIMMapper()
    mapping = mapper.map_instructions(ir_res["instructions"], ast=ast)

    opt = mapping["optimization"]
    assert opt["selected_strategy"] == "CPU_ONLY"
    assert opt["candidates"]["DIRECT_PIM"]["is_valid"] is False
    assert "unsupported" in opt["candidates"]["DIRECT_PIM"]["rejection_reason"].lower()
    assert "DIV" in opt["candidates"]["DIRECT_PIM"]["rejection_reason"]


def test_four_term_cost_formula_exact_sum():
    """
    Verify that total_cost = compute_cost + transfer_cost + layout_cost + synchronization_cost
    for all valid candidates.
    """
    params = CostParameters(
        cpu_cycles_per_arithmetic_op=1.5,
        pim_cycles_per_arithmetic_op=2.0,
        bus_bandwidth_bytes_per_cycle=4.0,
        pim_launch_sync_overhead_cycles=50.0,
        layout_transform_cycles_per_byte=0.5
    )
    code = """
    int main() {
        int data[20];
        int acc = 0;
        for (int i = 0; i < 20; i = i + 1) {
            acc = acc + data[i];
        }
        return acc;
    }
    """
    ast, ir_res = _compile_code(code)
    mapper = PIMMapper(cost_params=params)
    mapping = mapper.map_instructions(ir_res["instructions"], ast=ast)

    candidates = mapping["optimization"]["candidates"]
    for name, cand in candidates.items():
        if cand["is_valid"]:
            expected_total = round(
                cand["compute_cost"] + cand["transfer_cost"] + cand["layout_cost"] + cand["synchronization_cost"],
                2
            )
            assert cand["total_cost"] == expected_total


def test_strided_access_detection_and_layout_transform():
    """
    Detects strided access pattern (e.g. arr[i * 2]) and evaluates TRANSFORMED_PIM.
    """
    code = """
    int main() {
        int arr[100];
        int sum = 0;
        for (int i = 0; i < 50; i = i + 1) {
            sum += arr[i * 2];
        }
        return sum;
    }
    """
    ast, ir_res = _compile_code(code)
    mapper = PIMMapper()
    mapping = mapper.map_instructions(ir_res["instructions"], ast=ast)

    profile = mapping["optimization"]["workload_profile"]
    assert profile["access_pattern"] == "strided"
    assert profile["requires_layout_transform"] is True

    cand = mapping["optimization"]["candidates"]["TRANSFORMED_PIM"]
    assert cand["is_valid"] is True
    assert cand["layout_cost"] > 0


def test_unknown_quantities_explicitly_represented():
    """
    When loop condition does not have a static integer constant bound (e.g. while condition),
    loop_iterations must be explicitly None, not an invented number.
    """
    code = """
    int main() {
        int a = 10;
        while (a > 0) {
            a = a - 1;
        }
        return a;
    }
    """
    ast, ir_res = _compile_code(code)
    mapper = PIMMapper()
    mapping = mapper.map_instructions(ir_res["instructions"], ast=ast)

    profile = mapping["optimization"]["workload_profile"]
    assert profile["loop_iterations"] is None


def test_enforce_cost_mapping_updates_target():
    """
    When enforce_cost=True is provided, instructions that are structurally PIM-capable
    are assigned target='CPU' if the cost model selects CPU_ONLY.
    """
    code = """
    int main() {
        int x = 5;
        int y = 15;
        int z = x + y;
        return z;
    }
    """
    ast, ir_res = _compile_code(code)
    mapper = PIMMapper()

    # With enforce_cost=True
    mapping = mapper.map_instructions(ir_res["instructions"], ast=ast, enforce_cost=True)
    add_instr = next(i for i in mapping["instructions"] if i["ir_opcode"] == "ADD")
    assert add_instr["target"] == "CPU"
    assert add_instr["is_pim"] is False


def test_compiler_full_pipeline_includes_optimization():
    """
    Verify Compiler.compile() includes the full optimization payload.
    """
    code = """
    int main() {
        int arr[64];
        int sum = 0;
        for (int i = 0; i < 64; i = i + 1) {
            sum += arr[i];
        }
        return sum;
    }
    """
    compiler = Compiler()
    res = compiler.compile(code)

    assert res["success"] is True
    assert "optimization" in res
    assert "selected_strategy" in res["optimization"]
    assert "candidates" in res["optimization"]
    assert "parameters" in res["optimization"]
    assert "CPU_ONLY" in res["optimization"]["candidates"]
    assert "DIRECT_PIM" in res["optimization"]["candidates"]
    assert "TRANSFORMED_PIM" in res["optimization"]["candidates"]
