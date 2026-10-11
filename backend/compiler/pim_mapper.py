"""
Centralized PIM Instruction Eligibility Policy and Mapping Module.
Defines explicit eligibility rules for simulated in-memory operations,
routes unsupported or control operations to CPU fallback, and produces
educational mapping rationales and memory movement metadata.

Extended with Research-Informed Analytical Cost Modeling (NMC-Opt inspired):
- Static workload analysis pass (op counts, arrays read/written, loop bounds, access patterns)
- Candidate strategy evaluation (CPU_ONLY, DIRECT_PIM, TRANSFORMED_PIM)
- 4-term analytical cost breakdown:
    total_cost = compute_cost + transfer_cost + layout_cost + synchronization_cost
- Cost-aware offloading decision with explainable rationales.
"""
from typing import List, Dict, Any, Optional
from .cost_model import WorkloadAnalyzer, PIMCostModel, CostParameters, WorkloadProfile


class PIMPolicy:
    """
    Centralized architectural specification for the simulated PIM model.
    Note: These are project simulation rules, not claims about all real PIM hardware.
    """
    # 1. PIM-Eligible Operations
    PIM_ARITHMETIC = {
        "ADD": "PIM_ADD",
        "SUB": "PIM_SUB",
        "MUL": "PIM_MUL"
    }

    PIM_COMPARISONS = {
        "COMPARE_LT": "PIM_COMPARE",
        "COMPARE_LE": "PIM_COMPARE",
        "COMPARE_GT": "PIM_COMPARE",
        "COMPARE_GE": "PIM_COMPARE",
        "COMPARE_EQ": "PIM_COMPARE",
        "COMPARE_NE": "PIM_COMPARE"
    }

    PIM_MEMORY = {
        "LOAD_INDEXED": "PIM_LOAD",
        "STORE_INDEXED": "PIM_STORE"
    }

    # 2. CPU-Fallback Operations
    CPU_FALLBACK = {
        "DIV": "CPU_DIV",
        "MOD": "CPU_MOD",
        "RETURN": "CPU_RETURN",
        "BRANCH": "CPU_BRANCH",
        "JUMP": "CPU_JUMP",
        "LABEL": "LABEL",
        "DECLARE": "DECLARE",
        "CONST": "CPU_CONST",
        "LOAD": "CPU_LOAD",
        "STORE": "CPU_STORE",
        "PRINT": "CPU_PRINT"
    }

    # 3. Explicit Memory Access Eligibility Rules:
    # - In-situ array access (LOAD_INDEXED, STORE_INDEXED): Allocated to DRAM bank row buffers -> PIM
    # - Scalar variable access (LOAD, STORE): Resides in host CPU stack frame -> CPU Fallback
    # - Immediate constant access (CONST): Encoded in host CPU instruction stream -> CPU Fallback


class PIMMapper:
    """
    Centralized mapping module enforcing PIM eligibility policies and analytical cost optimization.
    Every mapping decision includes target assignment (PIM or CPU),
    mapped instruction mnemonic, memory metadata, and a detailed reason.
    """
    def __init__(self, policy: Optional[PIMPolicy] = None, cost_params: Optional[CostParameters] = None):
        self.policy = policy or PIMPolicy()
        self.analyzer = WorkloadAnalyzer()
        self.cost_model = PIMCostModel(cost_params)

    def map_instructions(
        self,
        ir_instructions: List[Dict[str, Any]],
        ast: Optional[Any] = None,
        enforce_cost: bool = False
    ) -> Dict[str, Any]:
        """
        Maps an ordered sequence of IR instructions into simulated PIM or CPU operations.
        Executes static workload analysis pass and evaluates 4-term analytical cost model.
        Returns mapped instructions, summary metrics, and policy/optimization details.
        """
        # 1. Static workload analysis pass
        profile = self.analyzer.analyze(ir_instructions, ast)

        # 2. Four-term analytical cost model evaluation
        optimization = self.cost_model.evaluate_candidates(profile)
        selected_strategy = optimization.get("selected_strategy", "CPU_ONLY")

        mapped_list = []
        pim_count = 0
        cpu_count = 0

        for instr in ir_instructions:
            mapped_item = self._evaluate_instruction(instr)

            # Determine cost-aware optimal target
            is_structurally_pim = mapped_item["is_pim"]
            if selected_strategy in ("DIRECT_PIM", "TRANSFORMED_PIM") and is_structurally_pim:
                optimal_target = "PIM"
                cost_justification = f"Cost model selected {selected_strategy}: in-memory execution saves bus transfer."
            else:
                optimal_target = "CPU"
                if is_structurally_pim:
                    cost_justification = (
                        f"Allocated to CPU by cost model: {optimization.get('decision_rationale', 'Overhead exceeds compute savings')}"
                    )
                else:
                    cost_justification = "Allocated to CPU: Operation requires CPU host control or ALU hardware."

            mapped_item["cost_strategy"] = selected_strategy
            mapped_item["optimal_target"] = optimal_target
            mapped_item["cost_justification"] = cost_justification

            if enforce_cost:
                mapped_item["target"] = optimal_target
                mapped_item["is_pim"] = (optimal_target == "PIM")

            mapped_list.append(mapped_item)
            if mapped_item["target"] == "PIM":
                pim_count += 1
            else:
                cpu_count += 1

        return {
            "instructions": mapped_list,
            "pim_count": pim_count,
            "cpu_count": cpu_count,
            "unsupported_count": 0,
            "total_instructions": len(ir_instructions),
            "summary": {
                "total": len(ir_instructions),
                "pim_allocated": pim_count,
                "cpu_fallback": cpu_count,
                "optimal_strategy": selected_strategy,
                "estimated_speedup": optimization.get("speedup_estimate", 1.0)
            },
            "optimization": optimization
        }

    def _evaluate_instruction(self, instr: Dict[str, Any]) -> Dict[str, Any]:
        opcode = instr.get("opcode", "")
        dest = instr.get("dest")
        arg1 = instr.get("arg1")
        arg2 = instr.get("arg2")
        metadata = instr.get("metadata", {})

        # Rule 1: Array-indexed Memory Loads (PIM_LOAD)
        if opcode == "LOAD_INDEXED":
            return {
                "ir_id": instr.get("id"),
                "ir_opcode": opcode,
                "target": "PIM",
                "mapped_instruction": "PIM_LOAD",
                "is_pim": True,
                "dest": dest,
                "arg1": arg1,
                "arg2": arg2,
                "reason": (
                    f"Array-indexed read '{arg1}[{arg2}]' accesses the local DRAM bank row buffer; "
                    "eligible for PIM in-situ load without traversing the memory bus."
                ),
                "memory_metadata": {
                    "operation_type": "memory_load",
                    "data_type": "int",
                    "memory_region": "array_buffer",
                    "bytes_transferred": metadata.get("bytes_transferred", 4),
                    "array_name": arg1
                },
                "formatted": f"PIM_LOAD {dest}, {arg1}[{arg2}]"
            }

        # Rule 2: Array-indexed Memory Stores (PIM_STORE)
        if opcode == "STORE_INDEXED":
            return {
                "ir_id": instr.get("id"),
                "ir_opcode": opcode,
                "target": "PIM",
                "mapped_instruction": "PIM_STORE",
                "is_pim": True,
                "dest": dest,
                "arg1": arg1,
                "arg2": arg2,
                "reason": (
                    f"Array-indexed write to '{dest}[{arg1}]' writes directly into the local DRAM row buffer; "
                    "eligible for PIM in-situ store without cache-flush or bus roundtrip."
                ),
                "memory_metadata": {
                    "operation_type": "memory_store",
                    "data_type": "int",
                    "memory_region": "array_buffer",
                    "bytes_transferred": metadata.get("bytes_transferred", 4),
                    "array_name": dest
                },
                "formatted": f"PIM_STORE {dest}[{arg1}], {arg2}"
            }

        # Rule 3: Scalar Memory Access (LOAD / STORE) -> CPU Fallback
        if opcode == "LOAD":
            return {
                "ir_id": instr.get("id"),
                "ir_opcode": opcode,
                "target": "CPU",
                "mapped_instruction": "CPU_LOAD",
                "is_pim": False,
                "dest": dest,
                "arg1": arg1,
                "arg2": None,
                "reason": (
                    f"Scalar variable '{arg1}' resides in the host CPU activation record / stack frame; "
                    "loaded via host CPU L1/L2 cache rather than in-memory PIM bank logic."
                ),
                "memory_metadata": {
                    "operation_type": "scalar_load",
                    "memory_region": "stack",
                    "bytes_transferred": 4
                },
                "formatted": f"CPU_LOAD {dest}, {arg1}"
            }

        if opcode == "STORE":
            return {
                "ir_id": instr.get("id"),
                "ir_opcode": opcode,
                "target": "CPU",
                "mapped_instruction": "CPU_STORE",
                "is_pim": False,
                "dest": dest,
                "arg1": arg1,
                "arg2": None,
                "reason": (
                    f"Scalar variable '{dest}' resides on the CPU stack frame; "
                    "stored by host CPU registers to preserve function call context."
                ),
                "memory_metadata": {
                    "operation_type": "scalar_store",
                    "memory_region": "stack",
                    "bytes_transferred": 4
                },
                "formatted": f"CPU_STORE {dest}, {arg1}"
            }

        # Rule 4: Immediate Constant Loading (CONST) -> CPU Fallback
        if opcode == "CONST":
            return {
                "ir_id": instr.get("id"),
                "ir_opcode": opcode,
                "target": "CPU",
                "mapped_instruction": "CPU_CONST",
                "is_pim": False,
                "dest": dest,
                "arg1": arg1,
                "arg2": None,
                "reason": (
                    f"Immediate literal value '{arg1}' is encoded directly in the CPU instruction stream "
                    "as an immediate operand, requiring no DRAM row-buffer allocation."
                ),
                "memory_metadata": {
                    "operation_type": "immediate_load",
                    "memory_region": "register",
                    "bytes_transferred": 0
                },
                "formatted": f"CPU_CONST {dest}, {arg1}"
            }

        # Rule 5: Supported Arithmetic Operations (ADD, SUB, MUL) -> PIM
        if opcode in self.policy.PIM_ARITHMETIC:
            pim_op = self.policy.PIM_ARITHMETIC[opcode]
            return {
                "ir_id": instr.get("id"),
                "ir_opcode": opcode,
                "target": "PIM",
                "mapped_instruction": pim_op,
                "is_pim": True,
                "dest": dest,
                "arg1": arg1,
                "arg2": arg2,
                "reason": (
                    f"Arithmetic '{opcode}' matches simulated PIM ALU capability; "
                    f"mapped to near-memory instruction '{pim_op}' for in-situ execution."
                ),
                "memory_metadata": {
                    "operation_type": "arithmetic",
                    "operator": opcode,
                    "memory_region": "pim_alu",
                    "bytes_transferred": 0
                },
                "formatted": f"{pim_op} {dest}, {arg1}, {arg2}"
            }

        # Rule 6: Unsupported Arithmetic Operations (DIV, MOD) -> CPU Fallback
        if opcode in ("DIV", "MOD"):
            cpu_op = f"CPU_{opcode}"
            return {
                "ir_id": instr.get("id"),
                "ir_opcode": opcode,
                "target": "CPU",
                "mapped_instruction": cpu_op,
                "is_pim": False,
                "dest": dest,
                "arg1": arg1,
                "arg2": arg2,
                "reason": (
                    f"Hardware division/modulo '{opcode}' is not supported by the lightweight in-memory PIM ALU "
                    "(area and power constraints); routed to host CPU divider hardware fallback."
                ),
                "memory_metadata": {
                    "operation_type": "fallback_arithmetic",
                    "operator": opcode,
                    "memory_region": "host_alu",
                    "bytes_transferred": 0
                },
                "formatted": f"{cpu_op} {dest}, {arg1}, {arg2}"
            }

        # Rule 7: Comparisons (COMPARE_LT, LE, GT, GE, EQ, NE) -> PIM
        if opcode in self.policy.PIM_COMPARISONS:
            return {
                "ir_id": instr.get("id"),
                "ir_opcode": opcode,
                "target": "PIM",
                "mapped_instruction": "PIM_COMPARE",
                "is_pim": True,
                "dest": dest,
                "arg1": arg1,
                "arg2": arg2,
                "reason": (
                    f"Relational condition '{opcode}' evaluates via in-memory PIM comparator circuit; "
                    "produces boolean condition flag locally within memory bank."
                ),
                "memory_metadata": {
                    "operation_type": "comparison",
                    "operator": opcode,
                    "memory_region": "pim_comparator",
                    "bytes_transferred": 0
                },
                "formatted": f"PIM_COMPARE {dest}, {arg1}, {arg2}"
            }

        # Rule 8: Control Flow Operations (JUMP, BRANCH, LABEL, RETURN) -> CPU Fallback
        if opcode in ("JUMP", "BRANCH", "LABEL", "RETURN"):
            return {
                "ir_id": instr.get("id"),
                "ir_opcode": opcode,
                "target": "CPU",
                "mapped_instruction": f"CPU_{opcode}" if opcode != "LABEL" else "LABEL",
                "is_pim": False,
                "dest": dest,
                "arg1": arg1,
                "arg2": arg2,
                "reason": (
                    "Control-flow instruction sequencing, branch evaluation, and program counter updates "
                    "are managed exclusively by the host CPU control unit."
                ),
                "memory_metadata": {
                    "operation_type": "control_flow",
                    "memory_region": "host_control_unit",
                    "bytes_transferred": 0
                },
                "formatted": instr.get("formatted", f"{opcode}")
            }

        # Rule 9: Declarations (DECLARE) -> CPU Fallback
        if opcode == "DECLARE":
            return {
                "ir_id": instr.get("id"),
                "ir_opcode": opcode,
                "target": "CPU",
                "mapped_instruction": "DECLARE",
                "is_pim": False,
                "dest": None,
                "arg1": arg1,
                "arg2": None,
                "reason": "Variable and array declaration is managed by the host runtime stack/heap layout.",
                "memory_metadata": {
                    "operation_type": "declaration",
                    "data_type": metadata.get("data_type", "int"),
                    "memory_region": "host_runtime",
                    "bytes_transferred": 0
                },
                "formatted": f"DECLARE {arg1} : {metadata.get('data_type', 'int')}"
            }

        # Rule 10: I/O Operations (PRINT) -> CPU Fallback
        if opcode == "PRINT":
            return {
                "ir_id": instr.get("id"),
                "ir_opcode": opcode,
                "target": "CPU",
                "mapped_instruction": "CPU_PRINT",
                "is_pim": False,
                "dest": None,
                "arg1": arg1,
                "arg2": None,
                "reason": "Standard output I/O is a host operating system system call executed by the CPU.",
                "memory_metadata": {
                    "operation_type": "io",
                    "memory_region": "host_os",
                    "bytes_transferred": 0
                },
                "formatted": f"CPU_PRINT {arg1}"
            }

        # Rule 11: General Fallback for Unsupported / Unrecognized Operations
        return {
            "ir_id": instr.get("id"),
            "ir_opcode": opcode,
            "target": "CPU",
            "mapped_instruction": f"CPU_{opcode}",
            "is_pim": False,
            "dest": dest,
            "arg1": arg1,
            "arg2": arg2,
            "reason": f"Operation '{opcode}' is not explicitly supported by the simulated PIM model; routed to CPU fallback.",
            "memory_metadata": {"operation_type": "fallback", "memory_region": "host_cpu"},
            "formatted": instr.get("formatted", f"{opcode}")
        }
