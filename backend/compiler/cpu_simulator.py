"""
CPU Execution Simulator for C-subset Three-Address Code (IR).
Maintains a runtime environment for variables, arrays, and temporaries,
executes arithmetic, memory, and control-flow instructions, and produces
an execution trace with state snapshots and return values.
"""
from typing import List, Dict, Any, Optional
import math


class SimulationError(Exception):
    """Exception raised during simulation runtime errors."""
    def __init__(self, message: str, pc: Optional[int] = None, instruction: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.pc = pc
        self.instruction = instruction


class CPUSimulator:
    """
    Simulates execution of 3AC IR instructions on a model host CPU.
    Tracks scalar variables, array memory, temporaries, program counter,
    and records an ordered execution trace.
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
        self.halted: bool = False

    def run(self, instructions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes an IR instruction list until RETURN, end of instructions, or error.
        Returns a structured dictionary with status, return value, variables, arrays, trace.
        """
        self.reset()

        if isinstance(instructions, dict):
            instructions = instructions.get("instructions", [])

        if not instructions:
            return {
                "status": "SUCCESS",
                "error": None,
                "return_value": 0,
                "final_variables": {},
                "final_arrays": {},
                "output": [],
                "execution_trace": [],
                "total_steps": 0
            }

        # 1. Pre-index label positions
        label_to_pc: Dict[str, int] = {}
        for idx, instr in enumerate(instructions):
            if instr.get("opcode") == "LABEL":
                label_name = instr.get("arg1")
                if label_name:
                    label_to_pc[label_name] = idx

        # 2. Execution loop
        try:
            while self.pc < len(instructions) and not self.halted:
                if self.steps >= self.max_steps:
                    raise SimulationError(
                        f"Execution step limit exceeded ({self.max_steps} steps). Infinite loop detected.",
                        pc=self.pc,
                        instruction=instructions[self.pc] if self.pc < len(instructions) else None
                    )

                instr = instructions[self.pc]
                self._execute_instruction(instr, label_to_pc, len(instructions))
                self.steps += 1

            return {
                "status": "SUCCESS",
                "error": None,
                "return_value": self.return_value if self.return_value is not None else 0,
                "final_variables": dict(self.variables),
                "final_arrays": {k: list(v) for k, v in self.arrays.items()},
                "output": list(self.output),
                "execution_trace": self.trace,
                "total_steps": self.steps
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
                "total_steps": self.steps
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "error": f"Runtime execution exception: {str(e)}",
                "return_value": None,
                "final_variables": dict(self.variables),
                "final_arrays": {k: list(v) for k, v in self.arrays.items()},
                "output": list(self.output),
                "execution_trace": self.trace,
                "total_steps": self.steps
            }

    def _resolve(self, operand: Any) -> int:
        """Resolves an operand string or int to an integer value."""
        if operand is None:
            return 0
        if isinstance(operand, (int, float)):
            return int(operand)

        s = str(operand).strip()
        # Direct integer literal (supports negative)
        try:
            return int(s)
        except ValueError:
            pass

        # Check temporaries first
        if s in self.temporaries:
            return self.temporaries[s]
        # Check scalar variables
        if s in self.variables:
            return self.variables[s]

        # Default fallback
        return 0

    def _execute_instruction(
        self,
        instr: Dict[str, Any],
        label_to_pc: Dict[str, int],
        total_instructions: int
    ):
        opcode = instr.get("opcode", "")
        dest = instr.get("dest")
        arg1 = instr.get("arg1")
        arg2 = instr.get("arg2")
        arg3 = instr.get("arg3")
        line = instr.get("line")

        op_desc = ""
        res_val = None
        next_pc = self.pc + 1

        # -------------------------------------------------------------
        # 1. Variable and Array Declarations
        # -------------------------------------------------------------
        if opcode == "DECLARE":
            meta = instr.get("metadata", {})
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
                op_desc = f"Allocated array '{arr_name}' of size {size}"
            else:
                var_name = meta.get("var_name") or arg1
                if var_name:
                    self.variables[var_name] = 0
                op_desc = f"Declared variable '{var_name}' = 0"

        # -------------------------------------------------------------
        # 2. Immediates and Constants
        # -------------------------------------------------------------
        elif opcode == "CONST":
            val = self._resolve(arg1)
            if dest:
                self.temporaries[dest] = val
            res_val = val
            op_desc = f"{dest} = {val}"

        # -------------------------------------------------------------
        # 3. Scalar Memory Access (Stack)
        # -------------------------------------------------------------
        elif opcode == "LOAD":
            val = self.variables.get(arg1, 0)
            if dest:
                self.temporaries[dest] = val
            res_val = val
            op_desc = f"{dest} = {arg1} ({val})"

        elif opcode == "STORE":
            val = self._resolve(arg1)
            if dest:
                self.variables[dest] = val
            res_val = val
            op_desc = f"{dest} = {val}"

        # -------------------------------------------------------------
        # 4. Array Indexed Memory Access (Heap/Buffer)
        # -------------------------------------------------------------
        elif opcode == "LOAD_INDEXED":
            arr_name = arg1
            idx = self._resolve(arg2)
            if arr_name not in self.arrays:
                raise SimulationError(f"Array '{arr_name}' accessed before declaration", pc=self.pc, instruction=instr)

            arr = self.arrays[arr_name]
            if idx < 0 or idx >= len(arr):
                raise SimulationError(
                    f"Array index {idx} out of bounds for array '{arr_name}' of size {len(arr)}",
                    pc=self.pc,
                    instruction=instr
                )

            val = arr[idx]
            if dest:
                self.temporaries[dest] = val
            res_val = val
            op_desc = f"{dest} = {arr_name}[{idx}] ({val})"

        elif opcode == "STORE_INDEXED":
            arr_name = dest
            idx = self._resolve(arg1)
            val = self._resolve(arg2)
            if arr_name not in self.arrays:
                raise SimulationError(f"Array '{arr_name}' accessed before declaration", pc=self.pc, instruction=instr)

            arr = self.arrays[arr_name]
            if idx < 0 or idx >= len(arr):
                raise SimulationError(
                    f"Array index {idx} out of bounds for array '{arr_name}' of size {len(arr)}",
                    pc=self.pc,
                    instruction=instr
                )

            arr[idx] = val
            res_val = val
            op_desc = f"{arr_name}[{idx}] = {val}"

        # -------------------------------------------------------------
        # 5. Arithmetic Operations
        # -------------------------------------------------------------
        elif opcode in ("ADD", "SUB", "MUL", "DIV", "MOD"):
            v1 = self._resolve(arg1)
            v2 = self._resolve(arg2)

            if opcode == "ADD":
                res = v1 + v2
                sym = "+"
            elif opcode == "SUB":
                res = v1 - v2
                sym = "-"
            elif opcode == "MUL":
                res = v1 * v2
                sym = "*"
            elif opcode == "DIV":
                if v2 == 0:
                    raise SimulationError("Division by zero", pc=self.pc, instruction=instr)
                res = int(v1 / v2)  # C-style integer truncation towards 0
                sym = "/"
            elif opcode == "MOD":
                if v2 == 0:
                    raise SimulationError("Modulo by zero", pc=self.pc, instruction=instr)
                # C-style integer remainder (sign matches dividend)
                res = v1 - int(v1 / v2) * v2
                sym = "%"

            if dest:
                self.temporaries[dest] = res
            res_val = res
            op_desc = f"{dest} = {v1} {sym} {v2} -> {res}"

        # -------------------------------------------------------------
        # 6. Comparisons
        # -------------------------------------------------------------
        elif opcode.startswith("COMPARE_"):
            v1 = self._resolve(arg1)
            v2 = self._resolve(arg2)

            if opcode == "COMPARE_LT":
                res = 1 if v1 < v2 else 0
                sym = "<"
            elif opcode == "COMPARE_LE":
                res = 1 if v1 <= v2 else 0
                sym = "<="
            elif opcode == "COMPARE_GT":
                res = 1 if v1 > v2 else 0
                sym = ">"
            elif opcode == "COMPARE_GE":
                res = 1 if v1 >= v2 else 0
                sym = ">="
            elif opcode == "COMPARE_EQ":
                res = 1 if v1 == v2 else 0
                sym = "=="
            elif opcode == "COMPARE_NE":
                res = 1 if v1 != v2 else 0
                sym = "!="
            else:
                res = 0
                sym = "?"

            if dest:
                self.temporaries[dest] = res
            res_val = res
            op_desc = f"{dest} = ({v1} {sym} {v2}) -> {res}"

        # -------------------------------------------------------------
        # 7. Control Flow: Labels, Jumps, Branches
        # -------------------------------------------------------------
        elif opcode == "LABEL":
            op_desc = f"Label {arg1}"

        elif opcode == "JUMP":
            target_label = arg1
            if target_label not in label_to_pc:
                raise SimulationError(f"Undefined jump label '{target_label}'", pc=self.pc, instruction=instr)
            next_pc = label_to_pc[target_label]
            op_desc = f"JUMP -> {target_label} (PC {next_pc})"

        elif opcode == "BRANCH":
            cond_val = self._resolve(arg1)
            target_true = arg2
            target_false = arg3

            if cond_val != 0:
                if target_true not in label_to_pc:
                    raise SimulationError(f"Undefined branch label '{target_true}'", pc=self.pc, instruction=instr)
                next_pc = label_to_pc[target_true]
                op_desc = f"BRANCH {arg1}({cond_val}) TRUE -> {target_true} (PC {next_pc})"
            else:
                if target_false:
                    if target_false not in label_to_pc:
                        raise SimulationError(f"Undefined branch label '{target_false}'", pc=self.pc, instruction=instr)
                    next_pc = label_to_pc[target_false]
                    op_desc = f"BRANCH {arg1}({cond_val}) FALSE -> {target_false} (PC {next_pc})"
                else:
                    op_desc = f"BRANCH {arg1}({cond_val}) FALSE -> fallthrough"

        # -------------------------------------------------------------
        # 8. Function Return & I/O
        # -------------------------------------------------------------
        elif opcode == "RETURN":
            val = self._resolve(arg1) if arg1 is not None else 0
            self.return_value = val
            self.halted = True
            res_val = val
            op_desc = f"RETURN {val}"

        elif opcode == "PRINT":
            val = self._resolve(arg1)
            self.output.append(str(val))
            res_val = val
            op_desc = f"PRINT {val}"

        else:
            raise SimulationError(f"Unsupported instruction opcode '{opcode}'", pc=self.pc, instruction=instr)

        # Record trace entry
        self.trace.append({
            "step": self.steps + 1,
            "pc": self.pc,
            "ir_id": instr.get("id"),
            "opcode": opcode,
            "dest": dest,
            "arg1": arg1,
            "arg2": arg2,
            "processor": "CPU",
            "operation_desc": op_desc,
            "result_value": res_val,
            "variables_snapshot": dict(self.variables),
            "arrays_snapshot": {k: list(v) for k, v in self.arrays.items()},
            "line": line
        })

        self.pc = next_pc
