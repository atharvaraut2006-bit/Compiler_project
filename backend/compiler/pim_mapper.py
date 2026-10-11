"""
PIM Eligibility Analyzer & Instruction Mapper.
Analyzes 3AC Intermediate Representation (IR) instructions, applies explicit
eligibility rules, and maps operations to simulated PIM instructions or CPU fallback.
"""
from typing import List, Dict, Any, Optional


class PIMMapper:
    """
    Evaluates IR instructions for simulated PIM execution suitability
    and generates mapped instruction traces with educational explanations.
    """
    # Explicit PIM Supported Opcodes
    PIM_SUPPORTED_OPERATIONS = {
        "ADD": "PIM_ADD",
        "SUB": "PIM_SUB",
        "MUL": "PIM_MUL",
        "LOAD_INDEXED": "PIM_LOAD",
        "STORE_INDEXED": "PIM_STORE",
        "COMPARE_LT": "PIM_COMPARE",
        "COMPARE_LE": "PIM_COMPARE",
        "COMPARE_GT": "PIM_COMPARE",
        "COMPARE_GE": "PIM_COMPARE",
        "COMPARE_EQ": "PIM_COMPARE",
        "COMPARE_NE": "PIM_COMPARE",
    }

    def map_instructions(self, ir_instructions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Maps a sequence of IR instructions into PIM operations or CPU fallbacks.
        Returns mapped instructions and summary metrics.
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
        op_type = metadata.get("operation_type", "")
        mem_region = metadata.get("memory_region", "register")

        # 1. Direct Array & Vector Memory Operations (Primary PIM Target)
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
                "reason": f"Direct indexed array access '{arg1}[{arg2}]' executed in-situ from local row buffer without memory bus transfer.",
                "memory_metadata": {
                    "operation_type": "memory_load",
                    "data_type": "int",
                    "memory_region": "array_buffer",
                    "source_var": f"{arg1}[{arg2}]",
                    "dest_var": dest,
                    "bytes_transferred": 4
                },
                "formatted": f"PIM_LOAD {dest}, {arg1}[{arg2}]"
            }

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
                "reason": f"Direct in-situ array writeback into memory partition '{dest}[{arg1}]' without external bus traffic.",
                "memory_metadata": {
                    "operation_type": "memory_store",
                    "data_type": "int",
                    "memory_region": "array_buffer",
                    "source_var": arg2,
                    "dest_var": f"{dest}[{arg1}]",
                    "bytes_transferred": 4
                },
                "formatted": f"PIM_STORE {dest}[{arg1}], {arg2}"
            }

        # 2. Arithmetic Acceleration (ADD, SUB, MUL)
        if opcode in ("ADD", "SUB", "MUL"):
            pim_op = self.PIM_SUPPORTED_OPERATIONS[opcode]
            return {
                "ir_id": instr.get("id"),
                "ir_opcode": opcode,
                "target": "PIM",
                "mapped_instruction": pim_op,
                "is_pim": True,
                "dest": dest,
                "arg1": arg1,
                "arg2": arg2,
                "reason": f"Integer arithmetic '{opcode}' is natively supported by the simulated in-memory ALU banks without host CPU execution.",
                "memory_metadata": {
                    "operation_type": "arithmetic",
                    "data_type": "int",
                    "memory_region": "pim_registers",
                    "bytes_transferred": 0
                },
                "formatted": f"{pim_op} {dest}, {arg1}, {arg2}"
            }

        # 3. High-Latency Arithmetic Excluded from PIM (DIV, MOD) -> CPU Fallback
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
                "reason": f"Integer '{opcode}' requires multi-cycle iterative divider hardware omitted from in-memory processing units; routed to CPU fallback.",
                "memory_metadata": {
                    "operation_type": "arithmetic",
                    "data_type": "int",
                    "memory_region": "host_cpu",
                    "bytes_transferred": 0
                },
                "formatted": f"CPU_{opcode} {dest}, {arg1}, {arg2}"
            }

        # 4. Comparisons (COMPARE_LT, LE, GT, GE, EQ, NE)
        if opcode.startswith("COMPARE_"):
            return {
                "ir_id": instr.get("id"),
                "ir_opcode": opcode,
                "target": "PIM",
                "mapped_instruction": "PIM_COMPARE",
                "is_pim": True,
                "dest": dest,
                "arg1": arg1,
                "arg2": arg2,
                "reason": f"Condition evaluation '{opcode}' is executed by the simulated in-memory comparator circuit.",
                "memory_metadata": {
                    "operation_type": "comparison",
                    "data_type": "int",
                    "memory_region": "pim_registers",
                    "bytes_transferred": 0
                },
                "formatted": f"PIM_COMPARE {dest}, {arg1}, {arg2} ({opcode})"
            }

        # 5. Scalar Loads and Stores
        if opcode == "LOAD":
            # If load comes from stack or host variable
            return {
                "ir_id": instr.get("id"),
                "ir_opcode": opcode,
                "target": "CPU",
                "mapped_instruction": "CPU_LOAD",
                "is_pim": False,
                "dest": dest,
                "arg1": arg1,
                "arg2": None,
                "reason": f"Scalar load of variable '{arg1}' from host stack frame; dispatched by CPU memory controller.",
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
                "reason": f"Scalar store of '{arg1}' into variable '{dest}' residing in host CPU stack space.",
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

        # 6. Immediate Constants
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
                "reason": f"Immediate constant '{arg1}' encoded into CPU instruction stream.",
                "memory_metadata": {
                    "operation_type": "immediate",
                    "data_type": "int",
                    "memory_region": "host_registers",
                    "bytes_transferred": 0
                },
                "formatted": f"CPU_CONST {dest}, {arg1}"
            }

        # 7. Control Flow (JUMP, BRANCH, LABEL, RETURN) -> CPU Fallback
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
                "reason": f"Control-flow instruction sequencing and program counter updates are managed by the host CPU control unit.",
                "memory_metadata": {
                    "operation_type": "control_flow",
                    "memory_region": "host_control_unit",
                    "bytes_transferred": 0
                },
                "formatted": instr.get("formatted", f"{opcode}")
            }

        # 8. Declarations
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
                "reason": f"Variable allocation and memory layout managed by the host runtime environment.",
                "memory_metadata": {
                    "operation_type": "declaration",
                    "data_type": metadata.get("data_type", "int"),
                    "memory_region": "host_runtime",
                    "bytes_transferred": 0
                },
                "formatted": f"DECLARE {arg1} : {metadata.get('data_type', 'int')}"
            }

        # 9. I/O (PRINT)
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
                "reason": "Host OS input/output system call executed exclusively by host CPU.",
                "memory_metadata": {
                    "operation_type": "io",
                    "memory_region": "host_os",
                    "bytes_transferred": 0
                },
                "formatted": f"CPU_PRINT {arg1}"
            }

        # Fallback default
        return {
            "ir_id": instr.get("id"),
            "ir_opcode": opcode,
            "target": "CPU",
            "mapped_instruction": f"CPU_{opcode}",
            "is_pim": False,
            "dest": dest,
            "arg1": arg1,
            "arg2": arg2,
            "reason": "Operation not eligible for PIM offloading; executed on host CPU.",
            "memory_metadata": {"operation_type": "unknown"},
            "formatted": instr.get("formatted", f"{opcode}")
        }
