"""
Centralized PIM Instruction Eligibility Policy and Mapping Module.
Defines explicit eligibility rules for simulated in-memory operations,
routes unsupported or control operations to CPU fallback, and produces
educational mapping rationales and memory movement metadata.
"""
from typing import List, Dict, Any, Optional


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
    Centralized mapping module enforcing PIM eligibility policies.
    Every mapping decision includes target assignment (PIM or CPU),
    mapped instruction mnemonic, memory metadata, and a detailed reason.
    """
    def __init__(self, policy: Optional[PIMPolicy] = None):
        self.policy = policy or PIMPolicy()

    def map_instructions(self, ir_instructions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Maps an ordered sequence of IR instructions into simulated PIM or CPU operations.
        Returns mapped instructions, summary metrics, and policy details.
        """
        mapped_list = []
        pim_count = 0
        cpu_count = 0

        for instr in ir_instructions:
            mapped_item = self._evaluate_instruction(instr)
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
                "cpu_fallback": cpu_count
            }
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
                    "source_var": f"{arg1}[{arg2}]",
                    "dest_var": dest,
                    "bytes_transferred": 0  # In-situ read eliminates bus traffic
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
                    f"Array-indexed writeback '{dest}[{arg1}]' stores directly into the local memory partition; "
                    "eligible for PIM in-situ store without external memory bus traffic."
                ),
                "memory_metadata": {
                    "operation_type": "memory_store",
                    "data_type": "int",
                    "memory_region": "array_buffer",
                    "source_var": arg2,
                    "dest_var": f"{dest}[{arg1}]",
                    "bytes_transferred": 0  # In-situ writeback eliminates bus traffic
                },
                "formatted": f"PIM_STORE {dest}[{arg1}], {arg2}"
            }

        # Rule 3: PIM-Eligible Arithmetic (ADD, SUB, MUL)
        if opcode in self.policy.PIM_ARITHMETIC:
            mapped_op = self.policy.PIM_ARITHMETIC[opcode]
            return {
                "ir_id": instr.get("id"),
                "ir_opcode": opcode,
                "target": "PIM",
                "mapped_instruction": mapped_op,
                "is_pim": True,
                "dest": dest,
                "arg1": arg1,
                "arg2": arg2,
                "reason": (
                    f"Integer arithmetic '{opcode}' is natively supported by the simulated in-memory ALU banks, "
                    "allowing local computation adjacent to memory cells."
                ),
                "memory_metadata": {
                    "operation_type": "arithmetic",
                    "data_type": "int",
                    "memory_region": "pim_registers",
                    "bytes_transferred": 0
                },
                "formatted": f"{mapped_op} {dest}, {arg1}, {arg2}"
            }

        # Rule 4: PIM-Eligible Comparisons (COMPARE_LT, LE, GT, GE, EQ, NE)
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
                    f"Comparison '{opcode}' is evaluated locally by the simulated in-memory comparator circuit."
                ),
                "memory_metadata": {
                    "operation_type": "comparison",
                    "data_type": "int",
                    "memory_region": "pim_registers",
                    "bytes_transferred": 0
                },
                "formatted": f"PIM_COMPARE {dest}, {arg1}, {arg2} ({opcode})"
            }

        # Rule 5: CPU-Fallback Arithmetic (DIV, MOD)
        if opcode in ("DIV", "MOD"):
            return {
                "ir_id": instr.get("id"),
                "ir_opcode": opcode,
                "target": "CPU",
                "mapped_instruction": f"CPU_{opcode}",
                "is_pim": False,
                "dest": dest,
                "arg1": arg1,
                "arg2": arg2,
                "reason": (
                    f"Integer '{opcode}' requires multi-cycle iterative divider hardware that is not implemented "
                    "in the simulated in-memory processing units; routed to CPU fallback."
                ),
                "memory_metadata": {
                    "operation_type": "arithmetic",
                    "data_type": "int",
                    "memory_region": "host_cpu",
                    "bytes_transferred": 0
                },
                "formatted": f"CPU_{opcode} {dest}, {arg1}, {arg2}"
            }

        # Rule 6: Scalar Memory Access (LOAD, STORE) -> CPU Fallback
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
                    f"Scalar variable '{arg1}' resides in the host CPU stack frame; "
                    "accessed via host memory controller, not eligible for PIM row buffer mapping."
                ),
                "memory_metadata": {
                    "operation_type": "memory_load",
                    "data_type": "int",
                    "memory_region": "stack",
                    "source_var": arg1,
                    "dest_var": dest,
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
                    f"Scalar variable '{dest}' resides in host CPU stack space; "
                    "stored by host CPU sequencer."
                ),
                "memory_metadata": {
                    "operation_type": "memory_store",
                    "data_type": "int",
                    "memory_region": "stack",
                    "source_var": arg1,
                    "dest_var": dest,
                    "bytes_transferred": 4
                },
                "formatted": f"CPU_STORE {dest}, {arg1}"
            }

        # Rule 7: Immediate Constants (CONST) -> CPU Fallback
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
                "reason": f"Immediate constant '{arg1}' is encoded directly into the host CPU instruction stream.",
                "memory_metadata": {
                    "operation_type": "immediate",
                    "data_type": "int",
                    "memory_region": "host_registers",
                    "bytes_transferred": 0
                },
                "formatted": f"CPU_CONST {dest}, {arg1}"
            }

        # Rule 8: Control Flow (JUMP, BRANCH, LABEL, RETURN) -> CPU Fallback
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
