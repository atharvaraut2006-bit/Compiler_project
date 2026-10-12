"""
PIM Execution Simulator for C-subset Three-Address Code.
Simulates in-memory processing operations mapped by Phase 2 (PIM_ADD, PIM_SUB,
PIM_MUL, PIM_LOAD, PIM_STORE, PIM_COMPARE) in DRAM row buffer ALUs, and executes
control-flow and unsupported operations on CPU fallback.
Produces a unified mixed-execution trace with processor annotations.
"""
from typing import List, Dict, Any, Optional
from .cpu_simulator import SimulationError


class PIMSimulator:
    """
    Simulates execution of Phase 2 mapped instructions on a model PIM architecture.
    Follows Phase 2 hardware mapping decisions:
    - PIM-eligible operations execute in simulated near-memory ALUs/row-buffers.
    - Control flow (branches, jumps) and unsupported ops execute via CPU fallback.
    - Preserves data consistency across processor transitions.
    """
    MAX_STEPS = 50000

    def __init__(self, max_steps: int = MAX_STEPS):
        self.max_steps = max_steps
        self.reset()

    def reset(self):
        self.variables: Dict[str, int] = {}
        self.arrays: Dict[str, List[int]] = {}
        self.temporaries: Dict[str, int] = {}
        self.output: List[str] = []
        self.return_value: Optional[int] = None
        self.trace: List[Dict[str, Any]] = []
        self.pc: int = 0
        self.steps: int = 0
        self.pim_steps: int = 0
        self.cpu_steps: int = 0
        self.halted: bool = False

    def run(
        self,
        mapped_instructions: List[Dict[str, Any]],
        ir_instructions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Executes a mapped instruction list.
        Each item contains 'target' ('PIM' vs 'CPU'), 'mapped_instruction', 'is_pim', and operands.
        """
        self.reset()

        if isinstance(mapped_instructions, dict):
            mapped_instructions = mapped_instructions.get("instructions", [])

        if not mapped_instructions:
            return {
                "status": "SUCCESS",
                "error": None,
                "return_value": 0,
                "final_variables": {},
                "final_arrays": {},
                "output": [],
                "execution_trace": [],
                "total_steps": 0,
                "pim_steps": 0,
                "cpu_steps": 0
            }

        # 1. Pre-index label positions
        label_to_pc: Dict[str, int] = {}
        for idx, item in enumerate(mapped_instructions):
            opcode = item.get("ir_opcode") or item.get("opcode")
            if opcode == "LABEL":
                label_name = item.get("arg1")
                if label_name:
                    label_to_pc[label_name] = idx

        # 2. Execution loop
        try:
            while self.pc < len(mapped_instructions) and not self.halted:
                if self.steps >= self.max_steps:
                    raise SimulationError(
                        f"Execution step limit exceeded ({self.max_steps} steps). Infinite loop detected.",
                        pc=self.pc,
                        instruction=mapped_instructions[self.pc] if self.pc < len(mapped_instructions) else None
                    )

                item = mapped_instructions[self.pc]
                self._execute_mapped_instruction(item, label_to_pc, len(mapped_instructions))
                self.steps += 1

            return {
                "status": "SUCCESS",
                "error": None,
                "return_value": self.return_value if self.return_value is not None else 0,
                "final_variables": dict(self.variables),
                "final_arrays": {k: list(v) for k, v in self.arrays.items()},
                "output": list(self.output),
                "execution_trace": self.trace,
                "total_steps": self.steps,
                "pim_steps": self.pim_steps,
                "cpu_steps": self.cpu_steps
            }

        except SimulationError as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "return_value": None,
                "final_variables": dict(self.variables),
                "final_arrays": {k: list(v) for k, v in self.arrays.items()},
                "output": list(self.output),
                "execution_trace": self.trace,
                "total_steps": self.steps,
                "pim_steps": self.pim_steps,
                "cpu_steps": self.cpu_steps
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "error": f"PIM simulation runtime exception: {str(e)}",
                "return_value": None,
                "final_variables": dict(self.variables),
                "final_arrays": {k: list(v) for k, v in self.arrays.items()},
                "output": list(self.output),
                "execution_trace": self.trace,
                "total_steps": self.steps,
                "pim_steps": self.pim_steps,
                "cpu_steps": self.cpu_steps
            }

    def _resolve(self, operand: Any) -> int:
        """Resolves operand to integer."""
        if operand is None:
            return 0
        if isinstance(operand, (int, float)):
            return int(operand)

        s = str(operand).strip()
        try:
            return int(s)
        except ValueError:
            pass

        if s in self.temporaries:
            return self.temporaries[s]
        if s in self.variables:
            return self.variables[s]
        return 0

    def _execute_mapped_instruction(
        self,
        item: Dict[str, Any],
        label_to_pc: Dict[str, int],
        total_instructions: int
    ):
        ir_opcode = item.get("ir_opcode") or item.get("opcode", "")
        mapped_op = item.get("mapped_instruction", ir_opcode)
        target = item.get("target", "CPU")
        is_pim = (target == "PIM")
        dest = item.get("dest")
        arg1 = item.get("arg1")
        arg2 = item.get("arg2")
        arg3 = item.get("arg3")
        line = item.get("line")
        fallback_reason = item.get("reason") if not is_pim else None

        op_desc = ""
        res_val = None
        next_pc = self.pc + 1

        if is_pim:
            self.pim_steps += 1
            processor = "PIM"
        else:
            self.cpu_steps += 1
            processor = "CPU"

        # -------------------------------------------------------------
        # 1. PIM INSTRUCTIONS (In-Memory Processing)
        # -------------------------------------------------------------
        if mapped_op == "PIM_LOAD":
            # Array read directly from DRAM row buffer
            arr_name = arg1
            idx = self._resolve(arg2)
            if arr_name not in self.arrays:
                raise SimulationError(f"Array '{arr_name}' accessed before declaration", pc=self.pc, instruction=item)

            arr = self.arrays[arr_name]
            if idx < 0 or idx >= len(arr):
                raise SimulationError(
                    f"Array index {idx} out of bounds for array '{arr_name}' of size {len(arr)}",
                    pc=self.pc,
                    instruction=item
                )

            val = arr[idx]
            if dest:
                self.temporaries[dest] = val
            res_val = val
            op_desc = f"[PIM Row-Buffer Read] {dest} = {arr_name}[{idx}] ({val})"

        elif mapped_op == "PIM_STORE":
            # Array write into DRAM bank partition
            arr_name = dest
            idx = self._resolve(arg1)
            val = self._resolve(arg2)
            if arr_name not in self.arrays:
                raise SimulationError(f"Array '{arr_name}' accessed before declaration", pc=self.pc, instruction=item)

            arr = self.arrays[arr_name]
            if idx < 0 or idx >= len(arr):
                raise SimulationError(
                    f"Array index {idx} out of bounds for array '{arr_name}' of size {len(arr)}",
                    pc=self.pc,
                    instruction=item
                )

            arr[idx] = val
            res_val = val
            op_desc = f"[PIM Bank Write] {arr_name}[{idx}] = {val}"

        elif mapped_op in ("PIM_ADD", "PIM_SUB", "PIM_MUL"):
            v1 = self._resolve(arg1)
            v2 = self._resolve(arg2)

            if mapped_op == "PIM_ADD":
                res = v1 + v2
                sym = "+"
            elif mapped_op == "PIM_SUB":
                res = v1 - v2
                sym = "-"
            else:
                res = v1 * v2
                sym = "*"

            if dest:
                self.temporaries[dest] = res
            res_val = res
            op_desc = f"[PIM ALU {sym}] {dest} = {v1} {sym} {v2} -> {res}"

        elif mapped_op == "PIM_COMPARE":
            v1 = self._resolve(arg1)
            v2 = self._resolve(arg2)

            if ir_opcode == "COMPARE_LT":
                res = 1 if v1 < v2 else 0
                sym = "<"
            elif ir_opcode == "COMPARE_LE":
                res = 1 if v1 <= v2 else 0
                sym = "<="
            elif ir_opcode == "COMPARE_GT":
                res = 1 if v1 > v2 else 0
                sym = ">"
            elif ir_opcode == "COMPARE_GE":
                res = 1 if v1 >= v2 else 0
                sym = ">="
            elif ir_opcode == "COMPARE_EQ":
                res = 1 if v1 == v2 else 0
                sym = "=="
            elif ir_opcode == "COMPARE_NE":
                res = 1 if v1 != v2 else 0
                sym = "!="
            else:
                res = 0
                sym = "?"

            if dest:
                self.temporaries[dest] = res
            res_val = res
            op_desc = f"[PIM Compare] {dest} = ({v1} {sym} {v2}) -> {res}"

        # -------------------------------------------------------------
        # 2. CPU FALLBACK INSTRUCTIONS (Host CPU Core)
        # -------------------------------------------------------------
        elif mapped_op in ("DECLARE",):
            meta = item.get("memory_metadata") or item.get("metadata", {})
            if meta.get("data_type", "").endswith("[]") or "[" in str(arg1):
                arr_name = meta.get("array_name")
                if not arr_name and arg1 and "[" in str(arg1):
                    arr_name = str(arg1).split("[")[0]
                size = meta.get("size")
                if size is None and arg1 and "[" in str(arg1):
                    try:
                        size = int(str(arg1).split("[")[1].split("]")[0])
                    except (IndexError, ValueError):
                        size = 0
                size = size or 0
                self.arrays[arr_name] = [0] * size
                op_desc = f"[CPU Decl] Allocated DRAM buffer '{arr_name}' of size {size}"
            else:
                var_name = meta.get("var_name") or arg1
                if var_name:
                    self.variables[var_name] = 0
                op_desc = f"[CPU Decl] Stack variable '{var_name}' = 0"

        elif mapped_op in ("CPU_CONST", "CONST"):
            val = self._resolve(arg1)
            if dest:
                self.temporaries[dest] = val
            res_val = val
            op_desc = f"[CPU Const] {dest} = {val}"

        elif mapped_op in ("CPU_LOAD", "LOAD"):
            val = self.variables.get(arg1, 0)
            if dest:
                self.temporaries[dest] = val
            res_val = val
            op_desc = f"[CPU Stack Load] {dest} = {arg1} ({val})"

        elif mapped_op in ("CPU_STORE", "STORE"):
            val = self._resolve(arg1)
            if dest:
                self.variables[dest] = val
            res_val = val
            op_desc = f"[CPU Stack Store] {dest} = {val}"

        elif mapped_op in ("CPU_DIV", "DIV", "CPU_MOD", "MOD"):
            v1 = self._resolve(arg1)
            v2 = self._resolve(arg2)
            if v2 == 0:
                raise SimulationError(
                    f"{'Division' if 'DIV' in mapped_op else 'Modulo'} by zero on CPU core",
                    pc=self.pc,
                    instruction=item
                )

            if "DIV" in mapped_op:
                res = int(v1 / v2)
                sym = "/"
            else:
                res = v1 - int(v1 / v2) * v2
                sym = "%"

            if dest:
                self.temporaries[dest] = res
            res_val = res
            op_desc = f"[CPU Fallback ALU {sym}] {dest} = {v1} {sym} {v2} -> {res}"

        elif mapped_op == "LABEL":
            op_desc = f"Label {arg1}"

        elif mapped_op in ("CPU_JUMP", "JUMP"):
            target_label = arg1
            if target_label not in label_to_pc:
                raise SimulationError(f"Undefined jump label '{target_label}'", pc=self.pc, instruction=item)
            next_pc = label_to_pc[target_label]
            op_desc = f"[CPU Jump] -> {target_label} (PC {next_pc})"

        elif mapped_op in ("CPU_BRANCH", "BRANCH"):
            cond_val = self._resolve(arg1)
            target_true = arg2
            target_false = arg3

            if cond_val != 0:
                if target_true not in label_to_pc:
                    raise SimulationError(f"Undefined branch label '{target_true}'", pc=self.pc, instruction=item)
                next_pc = label_to_pc[target_true]
                op_desc = f"[CPU Branch] {arg1}({cond_val}) TRUE -> {target_true} (PC {next_pc})"
            else:
                if target_false:
                    if target_false not in label_to_pc:
                        raise SimulationError(f"Undefined branch label '{target_false}'", pc=self.pc, instruction=item)
                    next_pc = label_to_pc[target_false]
                    op_desc = f"[CPU Branch] {arg1}({cond_val}) FALSE -> {target_false} (PC {next_pc})"
                else:
                    op_desc = f"[CPU Branch] {arg1}({cond_val}) FALSE -> fallthrough"

        elif mapped_op in ("CPU_RETURN", "RETURN"):
            val = self._resolve(arg1) if arg1 is not None else 0
            self.return_value = val
            self.halted = True
            res_val = val
            op_desc = f"[CPU Host Return] {val}"

        elif mapped_op in ("CPU_PRINT", "PRINT"):
            val = self._resolve(arg1)
            self.output.append(str(val))
            res_val = val
            op_desc = f"[CPU I/O Print] {val}"

        else:
            raise SimulationError(f"Unsupported simulated instruction '{mapped_op}'", pc=self.pc, instruction=item)

        # Record mixed trace step
        self.trace.append({
            "step": self.steps + 1,
            "pc": self.pc,
            "ir_id": item.get("ir_id"),
            "processor": processor,
            "mapped_instruction": mapped_op,
            "is_fallback": not is_pim,
            "fallback_reason": fallback_reason,
            "dest": dest,
            "arg1": arg1,
            "arg2": arg2,
            "operation_desc": op_desc,
            "result_value": res_val,
            "variables_snapshot": dict(self.variables),
            "arrays_snapshot": {k: list(v) for k, v in self.arrays.items()},
            "line": line
        })

        self.pc = next_pc
