"""
Analytical Four-Term Cost Model and Workload Optimization Pass.
Inspired by Near-Memory Computing optimization (NMC-Opt) research principles:
- Transparent four-term cost modeling:
    total_cost = compute_cost + transfer_cost + layout_cost + synchronization_cost
- Analytical candidate strategy evaluation: CPU_ONLY vs. DIRECT_PIM vs. TRANSFORMED_PIM
- Cost-aware offload selection with explicit simulation assumptions.

Note: These are research-informed simulation assumptions, not claims about specific physical hardware.
"""
from typing import Dict, Any, List, Optional
import math


class CostParameters:
    """
    Configurable parameters defining the architectural cost model assumptions.
    All parameters are simulation assumptions calibrated for comparative study.
    """
    def __init__(
        self,
        cpu_cycles_per_arithmetic_op: float = 1.0,
        cpu_cycles_per_compare_op: float = 1.0,
        pim_cycles_per_arithmetic_op: float = 1.2,
        pim_cycles_per_compare_op: float = 1.2,
        bus_bandwidth_bytes_per_cycle: float = 2.0,
        pim_internal_bandwidth_bytes_per_cycle: float = 32.0,
        pim_launch_sync_overhead_cycles: float = 60.0,
        layout_transform_cycles_per_byte: float = 0.25,
        word_size_bytes: int = 4
    ):
        # 1. Compute speed assumptions:
        # Host CPU has pipelined, high-frequency superscalar ALUs.
        # In-memory PIM ALUs operate within DRAM thermal constraints at slightly lower clock frequency.
        self.cpu_cycles_per_arithmetic_op = cpu_cycles_per_arithmetic_op
        self.cpu_cycles_per_compare_op = cpu_cycles_per_compare_op
        self.pim_cycles_per_arithmetic_op = pim_cycles_per_arithmetic_op
        self.pim_cycles_per_compare_op = pim_cycles_per_compare_op

        # 2. Data movement assumptions:
        # Host CPU must transfer data across the off-chip memory bus (e.g., DDR bus).
        # PIM units access in-situ DRAM row buffers directly via wide internal TSVs/busses.
        self.bus_bandwidth_bytes_per_cycle = bus_bandwidth_bytes_per_cycle
        self.pim_internal_bandwidth_bytes_per_cycle = pim_internal_bandwidth_bytes_per_cycle

        # 3. Coordination assumptions:
        # Offloading to PIM requires host dispatch, command register setup, and barrier completion sync.
        self.pim_launch_sync_overhead_cycles = pim_launch_sync_overhead_cycles

        # 4. Data Layout assumptions:
        # Converting non-contiguous or strided arrays into aligned PIM row-buffer chunks incurs reorganization cost.
        self.layout_transform_cycles_per_byte = layout_transform_cycles_per_byte
        self.word_size_bytes = word_size_bytes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpu_cycles_per_arithmetic_op": self.cpu_cycles_per_arithmetic_op,
            "pim_cycles_per_arithmetic_op": self.pim_cycles_per_arithmetic_op,
            "bus_bandwidth_bytes_per_cycle": self.bus_bandwidth_bytes_per_cycle,
            "pim_internal_bandwidth_bytes_per_cycle": self.pim_internal_bandwidth_bytes_per_cycle,
            "pim_launch_sync_overhead_cycles": self.pim_launch_sync_overhead_cycles,
            "layout_transform_cycles_per_byte": self.layout_transform_cycles_per_byte,
            "word_size_bytes": self.word_size_bytes,
            "note": "Configurable simulation parameters; representative values based on NMC-Opt literature."
        }


class WorkloadProfile:
    """
    Extracted static workload properties from AST and IR analysis.
    Explicitly represents unknown quantities as None instead of inventing values.
    """
    def __init__(self):
        self.arithmetic_op_count: int = 0
        self.comparison_op_count: int = 0
        self.arrays_read: List[str] = []
        self.arrays_written: List[str] = []
        self.bytes_read: int = 0
        self.bytes_written: int = 0
        self.total_memory_bytes: int = 0
        self.loop_iterations: Optional[int] = None
        self.access_pattern: str = "scalar_only"  # 'sequential', 'strided', 'scalar_only', 'unknown'
        self.has_unsupported_ops: bool = False
        self.unsupported_op_list: List[str] = []
        self.is_pim_hardware_eligible: bool = False
        self.requires_layout_transform: bool = False
        self.data_reuse_detected: bool = False
        self.raw_dependencies_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "arithmetic_op_count": self.arithmetic_op_count,
            "comparison_op_count": self.comparison_op_count,
            "total_computational_ops": self.arithmetic_op_count + self.comparison_op_count,
            "arrays_read": self.arrays_read,
            "arrays_written": self.arrays_written,
            "bytes_read": self.bytes_read,
            "bytes_written": self.bytes_written,
            "total_memory_bytes": self.total_memory_bytes,
            "loop_iterations": self.loop_iterations,
            "access_pattern": self.access_pattern,
            "has_unsupported_ops": self.has_unsupported_ops,
            "unsupported_op_list": self.unsupported_op_list,
            "is_pim_hardware_eligible": self.is_pim_hardware_eligible,
            "requires_layout_transform": self.requires_layout_transform,
            "data_reuse_detected": self.data_reuse_detected,
            "raw_dependencies_count": self.raw_dependencies_count
        }


class WorkloadAnalyzer:
    """
    Static analysis pass extracting workload characteristics from AST and IR instructions.
    """
    def analyze(self, ir_instructions: List[Dict[str, Any]], ast: Optional[Any] = None) -> WorkloadProfile:
        profile = WorkloadProfile()

        # 1. Statically determine loop iterations from AST if present
        if ast:
            profile.loop_iterations = self._extract_loop_iterations(ast)

        # 2. Analyze IR instructions
        arrays_read_set = set()
        arrays_written_set = set()
        bytes_read = 0
        bytes_written = 0
        unsupported = set()
        has_strided_access = False
        has_indexed_access = False

        # Variable definitions for dependency analysis and index tracking
        definitions = set()
        def_ops = {}
        raw_deps = 0

        for instr in ir_instructions:
            op = instr.get("opcode", "")
            dest = instr.get("dest")
            arg1 = instr.get("arg1")
            arg2 = instr.get("arg2")

            # Dependency check (Read-After-Write)
            if arg1 and arg1 in definitions:
                raw_deps += 1
            if arg2 and arg2 in definitions:
                raw_deps += 1
            if dest:
                definitions.add(dest)
                def_ops[dest] = op

            # Operation classification
            if op in ("ADD", "SUB", "MUL"):
                profile.arithmetic_op_count += 1
            elif op in ("DIV", "MOD"):
                profile.arithmetic_op_count += 1
                profile.has_unsupported_ops = True
                unsupported.add(op)
            elif op.startswith("COMPARE_"):
                profile.comparison_op_count += 1
            elif op == "LOAD_INDEXED":
                has_indexed_access = True
                if arg1:
                    arrays_read_set.add(arg1)
                bytes_read += 4
                # Check for strided pattern via direct text or operand definition (e.g. index generated by MUL)
                if arg2:
                    if ("*" in str(arg2) or "+" in str(arg2)) or (arg2 in def_ops and def_ops[arg2] in ("MUL", "DIV")):
                        has_strided_access = True
            elif op == "STORE_INDEXED":
                has_indexed_access = True
                if dest:
                    arrays_written_set.add(dest)
                bytes_written += 4
                if arg1:
                    if ("*" in str(arg1) or "+" in str(arg1)) or (arg1 in def_ops and def_ops[arg1] in ("MUL", "DIV")):
                        has_strided_access = True

        # Check AST for strided ArrayAccess if available
        if ast and not has_strided_access:
            try:
                from .ast_nodes import ArrayAccess, BinaryOp
                def check_stride(node):
                    if node is None:
                        return False
                    if isinstance(node, ArrayAccess) and isinstance(node.index, BinaryOp) and node.index.op in ("*", "/"):
                        return True
                    for field in ("declarations", "statements", "body", "then_branch", "else_branch", "expression", "target", "value", "init", "condition", "update", "left", "right"):
                        val = getattr(node, field, None)
                        if isinstance(val, list):
                            for item in val:
                                if check_stride(item):
                                    return True
                        elif val is not None:
                            if check_stride(val):
                                return True
                    return False
                if check_stride(ast):
                    has_strided_access = True
            except Exception:
                pass

        profile.arrays_read = sorted(list(arrays_read_set))
        profile.arrays_written = sorted(list(arrays_written_set))
        profile.unsupported_op_list = sorted(list(unsupported))
        profile.raw_dependencies_count = raw_deps

        # Scale by statically determinable loop iterations if available
        iter_multiplier = profile.loop_iterations if profile.loop_iterations and profile.loop_iterations > 0 else 1

        profile.bytes_read = bytes_read * (iter_multiplier if bytes_read > 0 and profile.loop_iterations else 1)
        profile.bytes_written = bytes_written * (iter_multiplier if bytes_written > 0 and profile.loop_iterations else 1)
        profile.total_memory_bytes = profile.bytes_read + profile.bytes_written

        # Access pattern classification
        if has_strided_access:
            profile.access_pattern = "strided"
            profile.requires_layout_transform = True
        elif has_indexed_access:
            profile.access_pattern = "sequential"
            profile.requires_layout_transform = False
        else:
            profile.access_pattern = "scalar_only"
            profile.requires_layout_transform = False

        # Hardware eligibility check
        # Must have no unsupported ops and must have array data in memory to justify in-memory offload
        if not profile.has_unsupported_ops and has_indexed_access:
            profile.is_pim_hardware_eligible = True
        else:
            profile.is_pim_hardware_eligible = False

        # Detect data reuse (e.g. read array and also write it or multiple reads)
        if len(arrays_read_set.intersection(arrays_written_set)) > 0 or bytes_read > 8:
            profile.data_reuse_detected = True

        return profile

    def _extract_loop_iterations(self, ast: Any) -> Optional[int]:
        """
        Attempts to statically calculate loop bounds from for-loops in AST.
        Returns integer count if constant bounds are found, otherwise returns None.
        """
        try:
            from .ast_nodes import Program, FunctionDef, Block, ForLoop, BinaryOp, IntLiteral, VarDecl, Assignment

            def search_loops(node):
                if isinstance(node, Program):
                    for d in node.declarations:
                        res = search_loops(d)
                        if res is not None:
                            return res
                elif isinstance(node, FunctionDef):
                    return search_loops(node.body)
                elif isinstance(node, Block):
                    for stmt in node.statements:
                        res = search_loops(stmt)
                        if res is not None:
                            return res
                elif isinstance(node, ForLoop):
                    # Inspect condition: e.g. i < 100 or i <= 99
                    start_val = 0
                    if isinstance(node.init, VarDecl) and isinstance(node.init.initializer, IntLiteral):
                        start_val = node.init.initializer.value
                    elif isinstance(node.init, Assignment) and isinstance(node.init.value, IntLiteral):
                        start_val = node.init.value.value

                    if isinstance(node.condition, BinaryOp):
                        op = node.condition.op
                        bound = None
                        if isinstance(node.condition.right, IntLiteral):
                            bound = node.condition.right.value

                        if bound is not None:
                            if op == "<":
                                return max(0, bound - start_val)
                            elif op == "<=":
                                return max(0, bound - start_val + 1)
                return None

            return search_loops(ast)
        except Exception:
            return None


class CandidateCost:
    """
    Evaluated 4-term analytical cost for an execution strategy.
    total_cost = compute_cost + transfer_cost + layout_cost + synchronization_cost
    """
    def __init__(
        self,
        strategy_name: str,
        is_valid: bool,
        rejection_reason: Optional[str] = None,
        compute_cost: float = 0.0,
        transfer_cost: float = 0.0,
        layout_cost: float = 0.0,
        synchronization_cost: float = 0.0,
        notes: str = ""
    ):
        self.strategy_name = strategy_name
        self.is_valid = is_valid
        self.rejection_reason = rejection_reason
        self.compute_cost = round(compute_cost, 2)
        self.transfer_cost = round(transfer_cost, 2)
        self.layout_cost = round(layout_cost, 2)
        self.synchronization_cost = round(synchronization_cost, 2)
        self.total_cost = round(compute_cost + transfer_cost + layout_cost + synchronization_cost, 2) if is_valid else float("inf")
        self.notes = notes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy_name,
            "is_valid": self.is_valid,
            "rejection_reason": self.rejection_reason,
            "compute_cost": self.compute_cost,
            "transfer_cost": self.transfer_cost,
            "layout_cost": self.layout_cost,
            "synchronization_cost": self.synchronization_cost,
            "total_cost": self.total_cost if self.is_valid else None,
            "notes": self.notes
        }


class PIMCostModel:
    """
    Transparent 4-term analytical cost model.
    Evaluates:
      1. CPU_ONLY execution
      2. DIRECT_PIM execution
      3. TRANSFORMED_PIM execution (layout-aware)
    Selects the minimum-cost valid candidate and explains the decision.
    """
    def __init__(self, params: Optional[CostParameters] = None):
        self.params = params or CostParameters()

    def evaluate_candidates(self, profile: WorkloadProfile) -> Dict[str, Any]:
        total_ops = profile.arithmetic_op_count + profile.comparison_op_count
        iter_mult = profile.loop_iterations if profile.loop_iterations and profile.loop_iterations > 0 else 1
        effective_ops = total_ops * (iter_mult if profile.loop_iterations else 1)

        # -------------------------------------------------------------
        # Candidate 1: CPU_ONLY
        # -------------------------------------------------------------
        # Host CPU executes all operations. Must transfer all array data across memory bus.
        cpu_compute = effective_ops * self.params.cpu_cycles_per_arithmetic_op
        cpu_transfer = profile.total_memory_bytes / self.params.bus_bandwidth_bytes_per_cycle
        cpu_layout = 0.0  # Host cache accommodates arbitrary access patterns
        cpu_sync = 0.0    # No offload launch or device barrier required

        cpu_candidate = CandidateCost(
            strategy_name="CPU_ONLY",
            is_valid=True,
            compute_cost=cpu_compute,
            transfer_cost=cpu_transfer,
            layout_cost=cpu_layout,
            synchronization_cost=cpu_sync,
            notes="Executes entirely on host CPU; all memory lines traverse the off-chip memory bus."
        )

        # -------------------------------------------------------------
        # Candidate 2: DIRECT_PIM
        # -------------------------------------------------------------
        # In-memory execution without layout transformation.
        if profile.has_unsupported_ops:
            direct_pim = CandidateCost(
                strategy_name="DIRECT_PIM",
                is_valid=False,
                rejection_reason=f"Kernel contains unsupported operations: {', '.join(profile.unsupported_op_list)}",
                notes="Rejected: Simulated PIM architecture cannot execute unsupported operations."
            )
        elif not profile.is_pim_hardware_eligible:
            direct_pim = CandidateCost(
                strategy_name="DIRECT_PIM",
                is_valid=False,
                rejection_reason="No DRAM array memory accessed; scalar operations remain on CPU stack.",
                notes="Rejected: Pure scalar computations have no in-memory data affinity."
            )
        else:
            pim_compute = effective_ops * self.params.pim_cycles_per_arithmetic_op
            # Array data stays in DRAM bank row buffers; only small scalar operands traverse bus (e.g. 8 bytes)
            pim_transfer = 8.0 / self.params.bus_bandwidth_bytes_per_cycle
            pim_layout = 0.0
            pim_sync = self.params.pim_launch_sync_overhead_cycles

            # Strided penalty if access pattern is not sequential
            if profile.access_pattern == "strided":
                # Uncoalesced bank row buffer conflicts
                pim_compute *= 1.35
                notes = "Direct PIM offload. Suffers strided row-buffer miss penalty."
            else:
                notes = "Direct PIM offload. Array reads access local bank row buffers with zero bus traffic."

            direct_pim = CandidateCost(
                strategy_name="DIRECT_PIM",
                is_valid=True,
                compute_cost=pim_compute,
                transfer_cost=pim_transfer,
                layout_cost=pim_layout,
                synchronization_cost=pim_sync,
                notes=notes
            )

        # -------------------------------------------------------------
        # Candidate 3: TRANSFORMED_PIM
        # -------------------------------------------------------------
        # Layout-aware PIM execution. Reorganizes strided/scattered data into contiguous row buffer format.
        if profile.has_unsupported_ops or not profile.is_pim_hardware_eligible:
            transformed_pim = CandidateCost(
                strategy_name="TRANSFORMED_PIM",
                is_valid=False,
                rejection_reason=direct_pim.rejection_reason,
                notes="Rejected due to hardware eligibility constraints."
            )
        elif not profile.requires_layout_transform:
            transformed_pim = CandidateCost(
                strategy_name="TRANSFORMED_PIM",
                is_valid=False,
                rejection_reason="Access pattern is already sequential; layout transformation is unnecessary.",
                notes="Not applicable for contiguous streaming accesses."
            )
        else:
            # Transformation is evaluated
            trans_compute = effective_ops * self.params.pim_cycles_per_arithmetic_op
            trans_transfer = 8.0 / self.params.bus_bandwidth_bytes_per_cycle
            trans_layout = profile.total_memory_bytes * self.params.layout_transform_cycles_per_byte
            trans_sync = self.params.pim_launch_sync_overhead_cycles

            transformed_pim = CandidateCost(
                strategy_name="TRANSFORMED_PIM",
                is_valid=True,
                compute_cost=trans_compute,
                transfer_cost=trans_transfer,
                layout_cost=trans_layout,
                synchronization_cost=trans_sync,
                notes="Layout-transformed PIM offload. Data re-organized into coalesced DRAM row buffers."
            )

        candidates = {
            "CPU_ONLY": cpu_candidate,
            "DIRECT_PIM": direct_pim,
            "TRANSFORMED_PIM": transformed_pim
        }

        # -------------------------------------------------------------
        # Cost-Aware Decision Logic: Pick minimum-cost valid candidate
        # -------------------------------------------------------------
        valid_candidates = [c for c in candidates.values() if c.is_valid]
        selected = min(valid_candidates, key=lambda c: c.total_cost)

        # Speedup vs CPU
        cpu_cost = cpu_candidate.total_cost
        speedup = round(cpu_cost / selected.total_cost, 2) if selected.total_cost > 0 else 1.0
        offload_beneficial = (selected.strategy_name != "CPU_ONLY" and selected.total_cost < cpu_cost)

        # Explainable decision rationale
        rationale = self._generate_rationale(selected, cpu_candidate, direct_pim, transformed_pim, profile)

        transformation_status = "not_needed"
        transformation_note = "Standard layout preserved."
        if selected.strategy_name == "TRANSFORMED_PIM":
            transformation_status = "estimated"
            transformation_note = "In-memory layout packing estimated based on NMC-Opt analytical model (not applied to AST/IR)."

        return {
            "workload_profile": profile.to_dict(),
            "candidates": {k: v.to_dict() for k, v in candidates.items()},
            "selected_strategy": selected.strategy_name,
            "selected_cost": selected.total_cost,
            "baseline_cpu_cost": cpu_cost,
            "speedup_estimate": speedup,
            "offload_beneficial": offload_beneficial,
            "decision_rationale": rationale,
            "transformation_status": transformation_status,
            "transformation_note": transformation_note,
            "parameters": self.params.to_dict()
        }

    def _generate_rationale(
        self,
        selected: CandidateCost,
        cpu: CandidateCost,
        direct_pim: CandidateCost,
        transformed_pim: CandidateCost,
        profile: WorkloadProfile
    ) -> str:
        name = selected.strategy_name

        if name == "CPU_ONLY":
            if profile.has_unsupported_ops:
                return (
                    f"CPU fallback selected: Kernel contains operations ({', '.join(profile.unsupported_op_list)}) "
                    "unsupported by the simulated PIM instruction set architecture."
                )
            elif not profile.is_pim_hardware_eligible:
                return (
                    "CPU execution selected: Workload operates exclusively on host stack scalars. "
                    "No DRAM arrays are accessed to justify in-memory offloading."
                )
            else:
                return (
                    f"CPU execution selected: Workload computation is small ({profile.total_memory_bytes} bytes). "
                    f"The PIM offload launch synchronization overhead ({self.params.pim_launch_sync_overhead_cycles:.0f} cycles) "
                    f"exceeds the memory bus transfer savings (CPU: {cpu.total_cost} cycles vs PIM: {direct_pim.total_cost} cycles)."
                )

        elif name == "DIRECT_PIM":
            savings = round(cpu.transfer_cost - selected.transfer_cost, 1)
            return (
                f"Direct PIM offload selected: In-memory execution eliminates {savings} cycles of memory bus data movement. "
                f"Even with {selected.synchronization_cost:.0f} cycles launch overhead, total cost ({selected.total_cost} cycles) "
                f"yields an estimated {round(cpu.total_cost / selected.total_cost, 2)}x speedup over CPU."
            )

        elif name == "TRANSFORMED_PIM":
            return (
                f"Layout-transformed PIM offload selected: Access pattern '{profile.access_pattern}' benefits from in-memory "
                f"data reorganization. Layout cost ({selected.layout_cost} cycles) is recouped by high coalesced throughput, "
                f"achieving {round(cpu.total_cost / selected.total_cost, 2)}x speedup over host CPU."
            )

        return f"Selected {name} with estimated total cost of {selected.total_cost} cycles."
