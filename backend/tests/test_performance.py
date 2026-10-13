"""
Comprehensive Unit and Integration Tests for Phase 4:
Performance Evaluation, Cost Breakdown, Speedup Analysis, and Sensitivity.
"""
import pytest
from backend.compiler.compiler import Compiler
from backend.compiler.cost_model import CostParameters, WorkloadAnalyzer, PIMCostModel, WorkloadProfile, CandidateCost
from backend.compiler.performance_evaluator import PerformanceEvaluator
from backend.main import app
from fastapi.testclient import TestClient


client = TestClient(app)


# -------------------------------------------------------------
# 1. Cost Calculations & Component Sum Verification
# -------------------------------------------------------------

def test_cpu_only_cost_calculation():
    """Verify CPU_ONLY computes compute + transfer with 0 layout and 0 sync."""
    params = CostParameters(
        cpu_cycles_per_arithmetic_op=1.0,
        bus_bandwidth_bytes_per_cycle=2.0
    )
    profile = WorkloadProfile()
    profile.dynamic_executed_ops = 10
    profile.dynamic_bus_bytes = 40

    model = PIMCostModel(params)
    res = model.evaluate_candidates(profile)
    cpu_cand = res["candidates"]["CPU_ONLY"]

    expected_compute = 10 * 1.0  # 10.0
    expected_transfer = 40 / 2.0  # 20.0
    expected_total = expected_compute + expected_transfer  # 30.0

    assert cpu_cand["compute_cost"] == expected_compute
    assert cpu_cand["transfer_cost"] == expected_transfer
    assert cpu_cand["layout_cost"] == 0.0
    assert cpu_cand["synchronization_cost"] == 0.0
    assert cpu_cand["total_cost"] == expected_total


def test_direct_pim_cost_calculation():
    """Verify DIRECT_PIM calculates in-situ compute + 8B dispatch transfer + 60 sync."""
    params = CostParameters(
        pim_cycles_per_arithmetic_op=1.2,
        bus_bandwidth_bytes_per_cycle=2.0,
        pim_launch_sync_overhead_cycles=60.0,
        pim_kernel_dispatch_bytes=8.0
    )
    profile = WorkloadProfile()
    profile.dynamic_executed_ops = 10
    profile.dynamic_bus_bytes = 40
    profile.is_pim_hardware_eligible = True
    profile.has_unsupported_ops = False
    profile.access_pattern = "sequential"

    model = PIMCostModel(params)
    res = model.evaluate_candidates(profile)
    direct_cand = res["candidates"]["DIRECT_PIM"]

    expected_compute = round(10 * 1.2, 2)  # 12.0
    expected_transfer = round(8.0 / 2.0, 2)  # 4.0
    expected_sync = 60.0
    expected_total = expected_compute + expected_transfer + expected_sync  # 76.0

    assert direct_cand["is_valid"] is True
    assert direct_cand["compute_cost"] == expected_compute
    assert direct_cand["transfer_cost"] == expected_transfer
    assert direct_cand["synchronization_cost"] == expected_sync
    assert direct_cand["layout_cost"] == 0.0
    assert direct_cand["total_cost"] == expected_total


def test_transformed_pim_feasibility():
    """Verify TRANSFORMED_PIM is only feasible when access pattern is strided/reorganization needed."""
    model = PIMCostModel()

    # Sequential access -> Rejected
    p_seq = WorkloadProfile()
    p_seq.dynamic_executed_ops = 10
    p_seq.is_pim_hardware_eligible = True
    p_seq.requires_layout_transform = False
    p_seq.access_pattern = "sequential"
    res_seq = model.evaluate_candidates(p_seq)
    assert res_seq["candidates"]["TRANSFORMED_PIM"]["is_valid"] is False
    assert "sequential" in res_seq["candidates"]["TRANSFORMED_PIM"]["rejection_reason"].lower()

    # Strided access -> Valid
    p_strided = WorkloadProfile()
    p_strided.dynamic_executed_ops = 10
    p_strided.dynamic_bus_bytes = 40
    p_strided.is_pim_hardware_eligible = True
    p_strided.requires_layout_transform = True
    p_strided.access_pattern = "strided"
    res_strided = model.evaluate_candidates(p_strided)
    assert res_strided["candidates"]["TRANSFORMED_PIM"]["is_valid"] is True
    assert res_strided["candidates"]["TRANSFORMED_PIM"]["layout_cost"] > 0


def test_total_cost_equals_sum_of_components():
    """Verify that for every valid candidate, total_cost == compute + transfer + layout + sync."""
    code = """int main() {
        int arr[4] = {10, 20, 30, 40};
        int sum = 0;
        for (int i = 0; i < 4; i++) {
            sum = sum + arr[i];
        }
        return 0;
    }"""
    compiler = Compiler()
    res = compiler.compile(code)
    perf = res["performance"]

    for strat in perf["strategies"]:
        if strat["is_valid"]:
            c = strat["compute_cost"] or 0.0
            t = strat["transfer_cost"] or 0.0
            l = strat["layout_cost"] or 0.0
            s = strat["synchronization_cost"] or 0.0
            total = strat["total_cost"]
            assert round(c + t + l + s, 2) == total


# -------------------------------------------------------------
# 2. Speedup & Baseline Verification
# -------------------------------------------------------------

def test_speedup_calculation_and_cpu_baseline():
    """Verify CPU_ONLY has speedup exactly 1.0 and valid strategies have proper speedup ratios."""
    code = """int main() {
        int arr[4] = {10, 20, 30, 40};
        int sum = 0;
        for (int i = 0; i < 4; i++) {
            sum = sum + arr[i];
        }
        return 0;
    }"""
    compiler = Compiler()
    res = compiler.compile(code)
    perf = res["performance"]

    cpu_strat = next(s for s in perf["strategies"] if s["strategy"] == "CPU_ONLY")
    assert cpu_strat["speedup_vs_cpu"] == 1.0

    # Infeasible strategies must have speedup = None
    trans_strat = next(s for s in perf["strategies"] if s["strategy"] == "TRANSFORMED_PIM")
    if not trans_strat["is_valid"]:
        assert trans_strat["speedup_vs_cpu"] is None


def test_zero_or_invalid_denominator_handling():
    """Verify division by zero or invalid cost handles gracefully without crashing."""
    evaluator = PerformanceEvaluator()
    # Mock candidate with total_cost = 0.0
    eval_res = {
        "selected_strategy": "DIRECT_PIM",
        "candidates": {
            "CPU_ONLY": {"is_valid": True, "total_cost": 0.0, "compute_cost": 0.0, "transfer_cost": 0.0, "layout_cost": 0.0, "synchronization_cost": 0.0},
            "DIRECT_PIM": {"is_valid": True, "total_cost": 0.0, "compute_cost": 0.0, "transfer_cost": 0.0, "layout_cost": 0.0, "synchronization_cost": 0.0},
            "TRANSFORMED_PIM": {"is_valid": False, "rejection_reason": "Not applicable"}
        }
    }
    profile = WorkloadProfile()
    rows = evaluator._format_strategies(eval_res, profile, CostParameters())
    assert rows[0]["speedup_vs_cpu"] == 1.0
    assert rows[1]["speedup_vs_cpu"] is None  # handles 0.0 gracefully without ZeroDivisionError


# -------------------------------------------------------------
# 3. Workload Sizing & Selection Tests
# -------------------------------------------------------------

def test_small_workload_selects_cpu_only():
    """For small arrays (e.g. 4 elements), launch overhead (60 cyc) exceeds bus savings, so CPU_ONLY wins."""
    code = """int main() {
        int arr[4] = {10, 20, 30, 40};
        int sum = 0;
        for (int i = 0; i < 4; i++) {
            sum = sum + arr[i];
        }
        return 0;
    }"""
    compiler = Compiler()
    res = compiler.compile(code)
    perf = res["performance"]

    assert perf["selected_strategy"] == "CPU_ONLY"
    assert perf["speedup_estimate"] == 1.0
    assert "overhead" in perf["decision_explanation"].lower() or "small" in perf["decision_explanation"].lower()


def test_large_workload_selects_pim():
    """For larger arrays (32 elements), 128 bytes of bus traffic makes DIRECT_PIM faster than CPU_ONLY."""
    code = """int main() {
        int data[32] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32};
        int total = 0;
        for (int i = 0; i < 32; i++) {
            total = total + data[i];
        }
        return 0;
    }"""
    compiler = Compiler()
    res = compiler.compile(code)
    perf = res["performance"]

    assert perf["selected_strategy"] == "DIRECT_PIM"
    assert perf["speedup_estimate"] > 1.0
    assert perf["offload_beneficial"] is True
    assert perf["transfer_metrics"]["bytes_saved"] > 0


def test_unsupported_operations_trigger_cpu_fallback():
    """Kernels containing unsupported division/modulo operations reject PIM and select CPU_ONLY."""
    code = """int main() {
        int arr[4] = {100, 200, 300, 400};
        int result = 0;
        for (int i = 0; i < 4; i++) {
            int val = arr[i] / 10;
            result = result + val;
        }
        return 0;
    }"""
    compiler = Compiler()
    res = compiler.compile(code)
    perf = res["performance"]

    assert perf["selected_strategy"] == "CPU_ONLY"
    direct = next(s for s in perf["strategies"] if s["strategy"] == "DIRECT_PIM")
    assert direct["is_valid"] is False
    assert "unsupported" in direct["rejection_reason"].lower()


# -------------------------------------------------------------
# 4. Sensitivity Analysis & API Endpoints
# -------------------------------------------------------------

def test_sensitivity_analysis_hypothetical_shift():
    """Verify that lowering launch overhead to 5 cycles makes PIM optimal even for small workloads."""
    evaluator = PerformanceEvaluator()
    profile = WorkloadProfile()
    profile.dynamic_executed_ops = 8
    profile.dynamic_bus_bytes = 32
    profile.is_pim_hardware_eligible = True
    profile.access_pattern = "sequential"

    baseline_eval = PIMCostModel().evaluate_candidates(profile)
    assert baseline_eval["selected_strategy"] == "CPU_ONLY"

    # Hypothetical low overhead: 2.0 cycles
    sensitivity = evaluator.evaluate_sensitivity(
        profile,
        {"pim_launch_sync_overhead_cycles": 2.0},
        baseline_eval
    )

    assert sensitivity["valid"] is True
    assert sensitivity["strategy_changed"] is True
    assert sensitivity["hypothetical_strategy"] == "DIRECT_PIM"
    assert sensitivity["hypothetical_speedup"] > 1.0


def test_sensitivity_invalid_inputs():
    """Verify sensitivity analysis validates and flags negative or invalid inputs."""
    evaluator = PerformanceEvaluator()
    profile = WorkloadProfile()
    baseline_eval = PIMCostModel().evaluate_candidates(profile)

    res = evaluator.evaluate_sensitivity(
        profile,
        {"bus_bandwidth_bytes_per_cycle": -5.0, "cpu_cycles_per_arithmetic_op": "invalid"},
        baseline_eval
    )

    assert res["valid"] is False
    assert len(res["errors"]) >= 1


def test_api_evaluate_endpoint():
    """Verify POST /api/evaluate returns full performance metrics."""
    payload = {
        "source_code": """int main() {
            int arr[4] = {10, 20, 30, 40};
            int sum = 0;
            for (int i = 0; i < 4; i++) {
                sum = sum + arr[i];
            }
            return 0;
        }"""
    }
    response = client.post("/api/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "selected_strategy" in data
    assert "strategies" in data
    assert len(data["strategies"]) == 3
    assert "transfer_metrics" in data
    assert "execution_stats" in data
    assert "cost_breakdown" in data
    assert "decision_explanation" in data


def test_api_evaluate_with_custom_params():
    """Verify POST /api/evaluate with custom_params returns sensitivity analysis."""
    payload = {
        "source_code": """int main() {
            int arr[4] = {10, 20, 30, 40};
            int sum = 0;
            for (int i = 0; i < 4; i++) {
                sum = sum + arr[i];
            }
            return 0;
        }""",
        "custom_params": {
            "pim_launch_sync_overhead_cycles": 4.0
        }
    }
    response = client.post("/api/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "sensitivity" in data
    assert data["sensitivity"]["valid"] is True
    assert data["sensitivity"]["hypothetical_strategy"] == "DIRECT_PIM"
    assert "comparison_table" in data["sensitivity"]
    assert len(data["sensitivity"]["comparison_table"]) >= 4
    metrics = [r["metric"] for r in data["sensitivity"]["comparison_table"]]
    assert "Selected Strategy" in metrics
    assert "CPU_ONLY Cost" in metrics
    assert "DIRECT_PIM Cost" in metrics
    assert "Estimated Speedup" in metrics


def test_mapping_decisions_preserve_when_cost_assumptions_change():
    """Verify instruction-level mapping decisions remain unchanged when only cost assumptions change."""
    code = """int main() {
        int arr[4] = {10, 20, 30, 40};
        int sum = 0;
        for (int i = 0; i < 4; i++) {
            sum = sum + arr[i];
        }
        return 0;
    }"""
    compiler = Compiler()
    res = compiler.compile(code)
    mapping_instrs = res["mapping"]["instructions"]

    # Instruction mapping targets remain identical
    assert len(mapping_instrs) == len(res["ir"]["instructions"])
    pim_ops = [i for i in mapping_instrs if i["target"] == "PIM"]
    assert len(pim_ops) > 0

    # Custom evaluation only affects candidate cost ranking, not hardware instruction mapping rules
    evaluator = PerformanceEvaluator()
    custom_eval = evaluator.evaluate(
        ir_instructions=res["ir"]["instructions"],
        custom_params={"pim_launch_sync_overhead_cycles": 2.0}
    )
    assert custom_eval["sensitivity"]["strategy_changed"] is True

