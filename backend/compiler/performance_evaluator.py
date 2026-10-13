"""
Performance Evaluator for Phase 4: Performance Evaluation, Cost Analysis, and Visualization.

Implements transparent analytical performance metrics comparing:
  - CPU_ONLY
  - DIRECT_PIM
  - TRANSFORMED_PIM (only when feasible)

Computes:
  - Estimated execution costs (Compute + Transfer + Layout + Synchronization)
  - Speedup relative to CPU_ONLY (with CPU_ONLY baseline speedup = 1.0)
  - Data-transfer savings (distinguishing footprint, accessed bytes, and modeled bus bytes)
  - Dynamic runtime execution statistics (from Phase 3 simulation traces)
  - Context-aware compiler decision explanation
  - Interactive sensitivity analysis with input validation
"""
from typing import Dict, Any, List, Optional
from .cost_model import CostParameters, WorkloadAnalyzer, PIMCostModel, WorkloadProfile, CandidateCost


class PerformanceEvaluator:
    """
    Evaluates performance across execution strategies and extracts runtime execution statistics.
    Source of truth for analytical cost calculations and sensitivity experiments.
    """

    def __init__(self, default_params: Optional[CostParameters] = None):
        self.default_params = default_params or CostParameters()
        self.analyzer = WorkloadAnalyzer()

    def evaluate(
        self,
        ir_instructions: List[Dict[str, Any]],
        ast: Optional[Any] = None,
        simulation_res: Optional[Dict[str, Any]] = None,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Runs comprehensive performance evaluation.
        Produces baseline comparison, dynamic stats, transfer metrics, decision explanation,
        and optional sensitivity analysis.
        """
        # 1. Profile workload statically
        profile = self.analyzer.analyze(ir_instructions, ast)

        # 2. Evaluate default baseline
        baseline_model = PIMCostModel(self.default_params)
        baseline_eval = baseline_model.evaluate_candidates(profile)

        # 3. Structure candidate strategy table
        strategies = self._format_strategies(baseline_eval, profile, self.default_params)

        # 4. Extract data-transfer comparison
        transfer_metrics = self._compute_transfer_metrics(profile, baseline_eval, self.default_params)

        # 5. Extract execution statistics (dynamic from Phase 3 simulation + static)
        execution_stats = self._extract_execution_stats(ir_instructions, simulation_res, profile)

        # 6. Generate detailed decision explanation
        selected_strategy = baseline_eval["selected_strategy"]
        explanation = self._generate_detailed_explanation(baseline_eval, strategies, profile, transfer_metrics)

        # 7. Optional sensitivity analysis if custom parameters provided
        sensitivity_result = None
        if custom_params:
            sensitivity_result = self.evaluate_sensitivity(profile, custom_params, baseline_eval)

        return {
            "selected_strategy": selected_strategy,
            "selected_cost": baseline_eval["selected_cost"],
            "baseline_cpu_cost": baseline_eval["baseline_cpu_cost"],
            "speedup_estimate": baseline_eval["speedup_estimate"],
            "offload_beneficial": baseline_eval["offload_beneficial"],
            "decision_explanation": explanation,
            "decision_rationale": baseline_eval["decision_rationale"],
            "strategies": strategies,
            "transfer_metrics": transfer_metrics,
            "execution_stats": execution_stats,
            "cost_breakdown": self._format_cost_breakdown(strategies),
            "parameters": self.default_params.to_dict(),
            "sensitivity": sensitivity_result,
            "workload_profile": profile.to_dict()
        }

    def _format_strategies(
        self,
        eval_res: Dict[str, Any],
        profile: WorkloadProfile,
        params: CostParameters
    ) -> List[Dict[str, Any]]:
        """
        Formats each strategy into a clean table row with speedup vs CPU_ONLY.
        Ensures CPU_ONLY speedup is exactly 1.0 and infeasible strategies have no misleading speedup.
        """
        candidates = eval_res.get("candidates", {})
        cpu_cand = candidates.get("CPU_ONLY", {})
        cpu_cost = cpu_cand.get("total_cost", 0.0) or 0.0

        rows = []
        for name in ["CPU_ONLY", "DIRECT_PIM", "TRANSFORMED_PIM"]:
            cand = candidates.get(name, {})
            is_valid = cand.get("is_valid", False)
            total = cand.get("total_cost")

            if name == "CPU_ONLY":
                speedup = 1.0
            elif is_valid and total and total > 0 and cpu_cost > 0:
                speedup = round(cpu_cost / total, 2)
            else:
                speedup = None

            rows.append({
                "strategy": name,
                "is_valid": is_valid,
                "is_selected": (name == eval_res.get("selected_strategy")),
                "rejection_reason": cand.get("rejection_reason"),
                "compute_cost": cand.get("compute_cost", 0.0) if is_valid else None,
                "transfer_cost": cand.get("transfer_cost", 0.0) if is_valid else None,
                "layout_cost": cand.get("layout_cost", 0.0) if is_valid else None,
                "synchronization_cost": cand.get("synchronization_cost", 0.0) if is_valid else None,
                "total_cost": total if is_valid else None,
                "speedup_vs_cpu": speedup,
                "notes": cand.get("notes", "")
            })

        return rows

    def _format_cost_breakdown(self, strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Produces clean stacked-bar data for valid strategies.
        Guarantees that compute + transfer + layout + sync == total.
        """
        items = []
        for s in strategies:
            if not s["is_valid"]:
                continue
            compute = s["compute_cost"] or 0.0
            transfer = s["transfer_cost"] or 0.0
            layout = s["layout_cost"] or 0.0
            sync = s["synchronization_cost"] or 0.0
            total = round(compute + transfer + layout + sync, 2)

            items.append({
                "strategy": s["strategy"],
                "is_selected": s["is_selected"],
                "compute": compute,
                "transfer": transfer,
                "layout": layout,
                "synchronization": sync,
                "total": total,
                "unit": "cycles"
            })
        return items

    def _compute_transfer_metrics(
        self,
        profile: WorkloadProfile,
        eval_res: Dict[str, Any],
        params: CostParameters
    ) -> Dict[str, Any]:
        """
        Calculates data movement metrics with clear separation between
        memory footprint, bytes accessed, and modeled bus bytes transferred.
        """
        selected_strategy = eval_res.get("selected_strategy", "CPU_ONLY")
        cpu_cand = eval_res["candidates"].get("CPU_ONLY", {})
        cpu_transfer_cost = cpu_cand.get("transfer_cost", 0.0)

        # 1. Declared memory footprint (bytes declared in program variables/arrays)
        declared_footprint_bytes = profile.declared_variable_bytes

        # 2. Dynamic bus bytes accessed by algorithm (reads + writes across iterations)
        dynamic_bus_bytes_accessed = profile.dynamic_bus_bytes

        # 3. Modeled bytes transferred across the host memory bus
        # CPU_ONLY must stream all dynamic bytes over the bus
        cpu_bytes_transferred = dynamic_bus_bytes_accessed

        # PIM: Array data resides in local DRAM row buffer.
        # Only an 8-byte kernel dispatch descriptor is transferred over the bus.
        if selected_strategy in ("DIRECT_PIM", "TRANSFORMED_PIM"):
            selected_bytes_transferred = int(params.pim_kernel_dispatch_bytes)
            selected_transfer_cost = eval_res["candidates"][selected_strategy].get("transfer_cost", 0.0)
            bytes_saved = max(0, cpu_bytes_transferred - selected_bytes_transferred)
            transfer_cost_savings = round(cpu_transfer_cost - selected_transfer_cost, 2)
        else:
            selected_bytes_transferred = cpu_bytes_transferred
            selected_transfer_cost = cpu_transfer_cost
            bytes_saved = 0
            transfer_cost_savings = 0.0

        bandwidth_reduction_pct = (
            round((bytes_saved / cpu_bytes_transferred) * 100, 1)
            if cpu_bytes_transferred > 0 and bytes_saved > 0 else 0.0
        )

        return {
            "declared_footprint_bytes": declared_footprint_bytes,
            "dynamic_bus_bytes_accessed": dynamic_bus_bytes_accessed,
            "cpu_bytes_transferred": cpu_bytes_transferred,
            "selected_bytes_transferred": selected_bytes_transferred,
            "bytes_saved": bytes_saved,
            "bandwidth_reduction_pct": bandwidth_reduction_pct,
            "cpu_transfer_cost_cycles": cpu_transfer_cost,
            "selected_transfer_cost_cycles": selected_transfer_cost,
            "transfer_cost_savings_cycles": transfer_cost_savings,
            "bus_bandwidth_bytes_per_cycle": params.bus_bandwidth_bytes_per_cycle,
            "units": {
                "footprint": "bytes",
                "traffic": "bytes",
                "transfer_cost": "cycles"
            }
        }

    def _extract_execution_stats(
        self,
        ir_instructions: List[Dict[str, Any]],
        simulation_res: Optional[Dict[str, Any]],
        profile: WorkloadProfile
    ) -> Dict[str, Any]:
        """
        Extracts execution statistics, clearly distinguishing static compile-time
        estimates from Phase 3 dynamic runtime execution traces.
        """
        # Static Estimates
        static_total_ir = len(ir_instructions)
        static_loop_iterations = profile.loop_iterations
        static_kernel_ops = profile.static_kernel_ops

        # Dynamic Metrics from Phase 3 Simulation Trace
        dynamic_available = False
        total_executed_instructions = None
        cpu_executed_instructions = None
        pim_executed_instructions = None
        cpu_fallback_operations = None
        runtime_loop_iterations = None
        array_accesses = None
        data_transfers = None

        if simulation_res and isinstance(simulation_res, dict):
            pim_sim = simulation_res.get("pim")
            if pim_sim and isinstance(pim_sim, dict) and "execution_trace" in pim_sim:
                trace = pim_sim.get("execution_trace", [])
                if trace:
                    dynamic_available = True
                    total_executed_instructions = len(trace)
                    pim_executed_instructions = sum(1 for t in trace if t.get("processor") == "PIM")
                    cpu_executed_instructions = sum(1 for t in trace if t.get("processor") == "CPU")
                    cpu_fallback_operations = sum(1 for t in trace if t.get("is_fallback"))

                    array_read_count = sum(1 for t in trace if t.get("read_array") is not None)
                    array_write_count = sum(1 for t in trace if t.get("updated_array") is not None)
                    array_accesses = array_read_count + array_write_count

                    data_transfers = sum(1 for t in trace if t.get("is_transfer"))

                    # Count loop iterations from backwards jumps
                    runtime_loop_iterations = sum(
                        1 for t in trace
                        if t.get("mapped_instruction") in ("CPU_JUMP", "JUMP") and "loop" in str(t.get("arg1", "")).lower()
                    )
                    if runtime_loop_iterations == 0 and static_loop_iterations is not None:
                        runtime_loop_iterations = static_loop_iterations

        return {
            "dynamic_available": dynamic_available,
            "dynamic": {
                "total_executed_instructions": total_executed_instructions,
                "cpu_executed_instructions": cpu_executed_instructions,
                "pim_executed_instructions": pim_executed_instructions,
                "cpu_fallback_operations": cpu_fallback_operations,
                "runtime_loop_iterations": runtime_loop_iterations,
                "array_accesses": array_accesses,
                "data_transfers": data_transfers
            },
            "static": {
                "total_ir_instructions": static_total_ir,
                "estimated_loop_iterations": static_loop_iterations,
                "static_computational_ops": static_kernel_ops,
                "access_pattern": profile.access_pattern,
                "has_unsupported_ops": profile.has_unsupported_ops,
                "unsupported_ops": profile.unsupported_op_list
            }
        }

    def _generate_detailed_explanation(
        self,
        baseline_eval: Dict[str, Any],
        strategies: List[Dict[str, Any]],
        profile: WorkloadProfile,
        transfer: Dict[str, Any]
    ) -> str:
        """
        Generates an understandable, student-friendly explanation of the compiler's decision.
        Explains why the selected strategy won and why others lost or were rejected.
        """
        selected = baseline_eval.get("selected_strategy", "CPU_ONLY")
        candidates = baseline_eval.get("candidates", {})
        cpu = candidates.get("CPU_ONLY", {})
        direct = candidates.get("DIRECT_PIM", {})
        trans = candidates.get("TRANSFORMED_PIM", {})

        if selected == "CPU_ONLY":
            if profile.has_unsupported_ops:
                return (
                    f"The compiler selected CPU_ONLY because the workload contains arithmetic operations "
                    f"({', '.join(profile.unsupported_op_list)}) not supported by the simulated near-memory PIM ALUs. "
                    "These operations must execute via CPU fallback on the host processor."
                )
            elif not profile.is_pim_hardware_eligible:
                return (
                    "The compiler selected CPU_ONLY because the program does not access any DRAM array memory buffers. "
                    "All variables reside on the host CPU stack frame, so offloading to memory would create unnecessary latency."
                )
            else:
                return (
                    f"The compiler selected CPU_ONLY because the data footprint is small ({profile.dynamic_bus_bytes} bytes). "
                    f"The PIM offload synchronization overhead ({self.default_params.pim_launch_sync_overhead_cycles:.0f} cycles) "
                    f"exceeds the estimated data transfer savings ({transfer['transfer_cost_savings_cycles']:.1f} cycles). "
                    f"Total CPU cost ({cpu.get('total_cost')} cycles) is lower than Direct PIM ({direct.get('total_cost')} cycles)."
                )

        elif selected == "DIRECT_PIM":
            speedup = baseline_eval.get("speedup_estimate", 1.0)
            return (
                f"The compiler selected DIRECT_PIM because in-memory execution saves "
                f"{transfer['transfer_cost_savings_cycles']:.1f} cycles of memory-bus data traffic ({transfer['bytes_saved']} bytes saved). "
                f"Even after adding {self.default_params.pim_launch_sync_overhead_cycles:.0f} cycles of PIM launch overhead, "
                f"the total cost ({direct.get('total_cost')} cycles) is lower than CPU_ONLY ({cpu.get('total_cost')} cycles), "
                f"yielding an estimated {speedup}x speedup. Layout transformation is not needed because the array access pattern is sequential."
            )

        elif selected == "TRANSFORMED_PIM":
            speedup = baseline_eval.get("speedup_estimate", 1.0)
            return (
                f"The compiler selected TRANSFORMED_PIM because the array access pattern is strided. "
                f"The layout reorganization cost ({trans.get('layout_cost')} cycles) is amortized across {profile.dynamic_executed_ops} operations, "
                f"enabling contiguous row-buffer streaming and achieving an estimated {speedup}x speedup over CPU_ONLY."
            )

        return baseline_eval.get("decision_rationale", "Optimal strategy selected based on minimum analytical cost.")

    def evaluate_sensitivity(
        self,
        profile: WorkloadProfile,
        custom_params: Dict[str, Any],
        baseline_eval: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Performs sensitivity analysis by applying user-supplied hypothetical parameters.
        Validates inputs and determines if the selected strategy changes.
        """
        errors = []

        # Extract and validate inputs
        def validate_pos_float(key: str, default_val: float, min_val: float = 0.01) -> float:
            if key not in custom_params:
                return default_val
            val = custom_params[key]
            try:
                f_val = float(val)
                if f_val < min_val:
                    errors.append(f"{key} must be at least {min_val}")
                    return default_val
                return f_val
            except (ValueError, TypeError):
                errors.append(f"{key} must be a valid positive number")
                return default_val

        hypo_launch_overhead = validate_pos_float(
            "pim_launch_sync_overhead_cycles",
            self.default_params.pim_launch_sync_overhead_cycles,
            min_val=0.0
        )
        hypo_cpu_cost = validate_pos_float(
            "cpu_cycles_per_arithmetic_op",
            self.default_params.cpu_cycles_per_arithmetic_op,
            min_val=0.1
        )
        hypo_pim_cost = validate_pos_float(
            "pim_cycles_per_arithmetic_op",
            self.default_params.pim_cycles_per_arithmetic_op,
            min_val=0.1
        )
        hypo_bandwidth = validate_pos_float(
            "bus_bandwidth_bytes_per_cycle",
            self.default_params.bus_bandwidth_bytes_per_cycle,
            min_val=0.1
        )
        hypo_layout_cost = validate_pos_float(
            "layout_transform_cycles_per_byte",
            self.default_params.layout_transform_cycles_per_byte,
            min_val=0.0
        )

        if errors:
            return {
                "valid": False,
                "errors": errors,
                "hypothetical_parameters": custom_params,
                "strategy_changed": False,
                "baseline_strategy": baseline_eval.get("selected_strategy"),
                "hypothetical_strategy": None
            }

        # Build hypothetical cost parameters without touching default
        hypo_params = CostParameters(
            cpu_cycles_per_arithmetic_op=hypo_cpu_cost,
            pim_cycles_per_arithmetic_op=hypo_pim_cost,
            bus_bandwidth_bytes_per_cycle=hypo_bandwidth,
            pim_launch_sync_overhead_cycles=hypo_launch_overhead,
            layout_transform_cycles_per_byte=hypo_layout_cost,
            word_size_bytes=self.default_params.word_size_bytes,
            pim_kernel_dispatch_bytes=self.default_params.pim_kernel_dispatch_bytes
        )

        hypo_model = PIMCostModel(hypo_params)
        hypo_eval = hypo_model.evaluate_candidates(profile)
        hypo_strategies = self._format_strategies(hypo_eval, profile, hypo_params)

        baseline_strategy = baseline_eval.get("selected_strategy")
        hypo_strategy = hypo_eval.get("selected_strategy")
        strategy_changed = (baseline_strategy != hypo_strategy)

        if strategy_changed:
            impact_summary = (
                f"Strategy changed from {baseline_strategy} to {hypo_strategy}! "
                f"Under these hypothetical assumptions, {hypo_strategy} achieves estimated "
                f"{hypo_eval.get('speedup_estimate')}x speedup (Cost: {hypo_eval.get('selected_cost')} cyc)."
            )
        else:
            impact_summary = (
                f"Selected strategy remains {baseline_strategy} (Cost: {hypo_eval.get('selected_cost')} cyc, "
                f"Speedup: {hypo_eval.get('speedup_estimate')}x)."
            )

        hypo_transfer = self._compute_transfer_metrics(profile, hypo_eval, hypo_params)
        hypo_explanation = self._generate_detailed_explanation(
            hypo_eval, hypo_strategies, profile, hypo_transfer
        )

        # Build compact comparison table
        base_cands = baseline_eval.get("candidates", {})
        hypo_cands = hypo_eval.get("candidates", {})

        comparison_table = [
            {
                "metric": "Selected Strategy",
                "default_value": baseline_strategy,
                "custom_value": hypo_strategy,
                "changed": strategy_changed
            },
            {
                "metric": "CPU_ONLY Cost",
                "default_value": f"{base_cands.get('CPU_ONLY', {}).get('total_cost', 0.0):.1f} cycles",
                "custom_value": f"{hypo_cands.get('CPU_ONLY', {}).get('total_cost', 0.0):.1f} cycles",
                "changed": base_cands.get('CPU_ONLY', {}).get('total_cost') != hypo_cands.get('CPU_ONLY', {}).get('total_cost')
            },
            {
                "metric": "DIRECT_PIM Cost",
                "default_value": f"{base_cands.get('DIRECT_PIM', {}).get('total_cost', 0.0):.1f} cycles" if base_cands.get('DIRECT_PIM', {}).get('is_valid') else "Infeasible",
                "custom_value": f"{hypo_cands.get('DIRECT_PIM', {}).get('total_cost', 0.0):.1f} cycles" if hypo_cands.get('DIRECT_PIM', {}).get('is_valid') else "Infeasible",
                "changed": base_cands.get('DIRECT_PIM', {}).get('total_cost') != hypo_cands.get('DIRECT_PIM', {}).get('total_cost')
            },
            {
                "metric": "Estimated Speedup",
                "default_value": f"{baseline_eval.get('speedup_estimate', 1.0):.2f}x",
                "custom_value": f"{hypo_eval.get('speedup_estimate', 1.0):.2f}x",
                "changed": baseline_eval.get('speedup_estimate') != hypo_eval.get('speedup_estimate')
            }
        ]
        if base_cands.get("TRANSFORMED_PIM", {}).get("is_valid") or hypo_cands.get("TRANSFORMED_PIM", {}).get("is_valid"):
            comparison_table.append({
                "metric": "TRANSFORMED_PIM Cost",
                "default_value": f"{base_cands.get('TRANSFORMED_PIM', {}).get('total_cost', 0.0):.1f} cycles" if base_cands.get('TRANSFORMED_PIM', {}).get('is_valid') else "Infeasible",
                "custom_value": f"{hypo_cands.get('TRANSFORMED_PIM', {}).get('total_cost', 0.0):.1f} cycles" if hypo_cands.get('TRANSFORMED_PIM', {}).get('is_valid') else "Infeasible",
                "changed": base_cands.get('TRANSFORMED_PIM', {}).get('total_cost') != hypo_cands.get('TRANSFORMED_PIM', {}).get('total_cost')
            })

        return {
            "valid": True,
            "errors": [],
            "baseline_strategy": baseline_strategy,
            "hypothetical_strategy": hypo_strategy,
            "strategy_changed": strategy_changed,
            "impact_summary": impact_summary,
            "decision_explanation": hypo_explanation,
            "hypothetical_cost": hypo_eval.get("selected_cost"),
            "hypothetical_speedup": hypo_eval.get("speedup_estimate"),
            "hypothetical_parameters": hypo_params.to_dict(),
            "strategies": hypo_strategies,
            "transfer_metrics": hypo_transfer,
            "offload_beneficial": hypo_eval.get("offload_beneficial", hypo_strategy != "CPU_ONLY"),
            "cost_breakdown": self._format_cost_breakdown(hypo_strategies),
            "comparison_table": comparison_table
        }
