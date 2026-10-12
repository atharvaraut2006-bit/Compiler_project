"""
Unit tests for PIM Simulator.
Verifies near-memory instruction execution, row buffer reads/writes,
in-memory comparisons, CPU fallback handling, and step metrics.
"""
import pytest
from backend.compiler.compiler import Compiler
from backend.compiler.pim_simulator import PIMSimulator


def test_pim_simulator_array_sum():
    compiler = Compiler()
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
    res = compiler.compile(code)
    assert res["success"] is True

    sim = PIMSimulator()
    exec_res = sim.run(res["mapping"]["instructions"])

    assert exec_res["status"] == "SUCCESS"
    assert exec_res["return_value"] == 100
    assert exec_res["final_variables"]["sum"] == 100
    assert exec_res["final_variables"]["i"] == 4
    assert exec_res["final_arrays"]["arr"] == [10, 20, 30, 40]

    # Verify PIM and CPU step accounting
    assert exec_res["pim_steps"] > 0
    assert exec_res["cpu_steps"] > 0
    assert exec_res["total_steps"] == exec_res["pim_steps"] + exec_res["cpu_steps"]


def test_pim_simulator_branching_and_fallback():
    compiler = Compiler()
    code = """
    int x = 15;
    int y = 25;
    int total = (x + y) * 2;
    if (total > 50) {
        total = total - 10;
    } else {
        total = total + 10;
    }
    print(total);
    """
    res = compiler.compile(code)
    assert res["success"] is True

    sim = PIMSimulator()
    exec_res = sim.run(res["mapping"]["instructions"])

    assert exec_res["status"] == "SUCCESS"
    assert exec_res["final_variables"]["total"] == 70
    assert exec_res["output"] == ["70"]
    assert exec_res["cpu_steps"] > 0
    assert exec_res["pim_steps"] > 0


def test_pim_simulator_division_fallback_fault():
    compiler = Compiler()
    code = """
    int main() {
        int a = 100;
        int b = 0;
        int c = a / b;
        return c;
    }
    """
    res = compiler.compile(code)
    assert res["success"] is True

    sim = PIMSimulator()
    exec_res = sim.run(res["mapping"]["instructions"])

    assert exec_res["status"] == "ERROR"
    assert "by zero" in exec_res["error"]


def test_pim_simulator_array_write_and_read():
    compiler = Compiler()
    code = """
    int main() {
        int arr[3] = {1, 2, 3};
        arr[1] = 99;
        int x = arr[1];
        return x;
    }
    """
    res = compiler.compile(code)
    assert res["success"] is True

    sim = PIMSimulator()
    exec_res = sim.run(res["mapping"]["instructions"])

    assert exec_res["status"] == "SUCCESS"
    assert exec_res["return_value"] == 99
    assert exec_res["final_arrays"]["arr"] == [1, 99, 3]


def test_pim_simulator_trace_fields():
    """Verify enriched trace fields required for step-by-step interactive animation."""
    compiler = Compiler()
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
    res = compiler.compile(code)
    sim = PIMSimulator()
    exec_res = sim.run(res["mapping"]["instructions"])

    trace = exec_res["execution_trace"]
    assert len(trace) > 0

    # Check that each step contains all required animation metadata
    for step in trace:
        assert "step" in step
        assert "pc" in step
        assert "processor" in step
        assert step["processor"] in ("PIM", "CPU")
        assert "mapped_instruction" in step
        assert "formatted_instruction" in step
        assert "is_fallback" in step
        assert "status" in step
        assert step["status"] == "SUCCESS"
        assert "variables_snapshot" in step
        assert "arrays_snapshot" in step

    # Verify PIM row buffer read step has read_array and is_transfer
    pim_load_steps = [s for s in trace if s["mapped_instruction"] == "PIM_LOAD"]
    assert len(pim_load_steps) == 4
    for pls in pim_load_steps:
        assert pls["read_array"] is not None
        assert pls["read_array"]["name"] == "arr"
        assert pls["is_transfer"] is True

    # Verify PIM ALU addition steps (4 for array sum accumulation + 4 for loop counter increment)
    pim_add_steps = [s for s in trace if s["mapped_instruction"] == "PIM_ADD"]
    assert len(pim_add_steps) == 8
    for pas in pim_add_steps:
        assert pas["processor"] == "PIM"
        assert pas["arg1_val"] is not None
        assert pas["arg2_val"] is not None
        assert pas["result_value"] is not None

