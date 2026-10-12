"""
Unit tests for Correctness Comparator and dual simulation orchestration.
Verifies semantic equivalence checking, discrepancy detection, and verdict generation.
"""
import pytest
from backend.compiler.compiler import Compiler
from backend.compiler.simulation_runner import SimulationRunner
from backend.compiler.correctness_comparator import CorrectnessComparator


def test_correctness_comparator_array_sum_pass():
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

    runner = SimulationRunner()
    dual_res = runner.run(res["ir"]["instructions"], res["mapping"]["instructions"])

    comp = dual_res["comparison"]
    assert comp["verdict"] == "PASS"
    assert comp["is_match"] is True
    assert comp["summary"]["return_value_match"] is True
    assert comp["summary"]["variables_match"] is True
    assert comp["summary"]["arrays_match"] is True
    assert len(comp["discrepancies"]) == 0


def test_correctness_comparator_sample_2_pass():
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

    runner = SimulationRunner()
    dual_res = runner.run(res["ir"]["instructions"], res["mapping"]["instructions"])

    comp = dual_res["comparison"]
    assert comp["verdict"] == "PASS"
    assert comp["is_match"] is True
    assert comp["summary"]["output_match"] is True


def test_correctness_comparator_detects_mismatch():
    comparator = CorrectnessComparator()

    cpu_res = {
        "status": "SUCCESS",
        "return_value": 100,
        "final_variables": {"a": 10, "b": 20},
        "final_arrays": {"arr": [1, 2, 3]},
        "output": ["100"],
        "total_steps": 10
    }

    # Simulate divergent PIM result
    pim_res = {
        "status": "SUCCESS",
        "return_value": 95,  # Mismatch!
        "final_variables": {"a": 10, "b": 15},  # Mismatch!
        "final_arrays": {"arr": [1, 2, 3]},
        "output": ["100"],
        "total_steps": 10,
        "pim_steps": 5,
        "cpu_steps": 5
    }

    comp = comparator.compare(cpu_res, pim_res)
    assert comp["verdict"] == "FAIL"
    assert comp["is_match"] is False
    assert comp["summary"]["return_value_match"] is False
    assert comp["summary"]["variables_match"] is False
    assert len(comp["discrepancies"]) >= 2


def test_correctness_comparator_error_divergence():
    comparator = CorrectnessComparator()

    cpu_res = {
        "status": "SUCCESS",
        "return_value": 0,
        "final_variables": {},
        "final_arrays": {},
        "output": [],
        "total_steps": 5
    }
    pim_res = {
        "status": "ERROR",
        "error": "Division by zero on CPU core",
        "return_value": None,
        "final_variables": {},
        "final_arrays": {},
        "output": [],
        "total_steps": 2,
        "pim_steps": 1,
        "cpu_steps": 1
    }

    comp = comparator.compare(cpu_res, pim_res)
    assert comp["verdict"] == "ERROR"
    assert comp["is_match"] is False
