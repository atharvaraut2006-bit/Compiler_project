"""
Unit tests for CPU Simulator.
Verifies instruction execution, runtime variable tracking, memory buffers,
control flow, and safety boundaries.
"""
import pytest
from backend.compiler.compiler import Compiler
from backend.compiler.cpu_simulator import CPUSimulator, SimulationError


def test_cpu_simulator_simple_arithmetic():
    compiler = Compiler()
    code = """
    int main() {
        int a = 15;
        int b = 25;
        int c = (a + b) * 2 - 10;
        return c;
    }
    """
    res = compiler.compile(code)
    assert res["success"] is True

    sim = CPUSimulator()
    exec_res = sim.run(res["ir"]["instructions"])

    assert exec_res["status"] == "SUCCESS"
    assert exec_res["return_value"] == 70
    assert exec_res["final_variables"]["a"] == 15
    assert exec_res["final_variables"]["b"] == 25
    assert exec_res["final_variables"]["c"] == 70
    assert exec_res["total_steps"] > 0
    assert len(exec_res["execution_trace"]) > 0


def test_cpu_simulator_array_sum_loop():
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

    sim = CPUSimulator()
    exec_res = sim.run(res["ir"]["instructions"])

    assert exec_res["status"] == "SUCCESS"
    assert exec_res["return_value"] == 100
    assert exec_res["final_variables"]["sum"] == 100
    assert exec_res["final_variables"]["i"] == 4
    assert exec_res["final_arrays"]["arr"] == [10, 20, 30, 40]


def test_cpu_simulator_division_by_zero():
    compiler = Compiler()
    code = """
    int main() {
        int a = 42;
        int b = 0;
        int c = a / b;
        return c;
    }
    """
    res = compiler.compile(code)
    assert res["success"] is True

    sim = CPUSimulator()
    exec_res = sim.run(res["ir"]["instructions"])

    assert exec_res["status"] == "ERROR"
    assert "by zero" in exec_res["error"]


def test_cpu_simulator_out_of_bounds():
    compiler = Compiler()
    code = """
    int main() {
        int arr[3] = {1, 2, 3};
        int idx = 10;
        int x = arr[idx];
        return x;
    }
    """
    res = compiler.compile(code)
    assert res["success"] is True

    sim = CPUSimulator()
    exec_res = sim.run(res["ir"]["instructions"])

    assert exec_res["status"] == "ERROR"
    assert "out of bounds" in exec_res["error"]


def test_cpu_simulator_step_limit():
    sim = CPUSimulator(max_steps=50)
    # Construct an infinite jump loop
    loop_ir = [
        {"id": 1, "opcode": "LABEL", "arg1": "loop_start"},
        {"id": 2, "opcode": "JUMP", "arg1": "loop_start"}
    ]
    exec_res = sim.run(loop_ir)
    assert exec_res["status"] == "ERROR"
    assert "limit exceeded" in exec_res["error"]
