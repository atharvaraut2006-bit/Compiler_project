"""
Intermediate Representation (IR) Generator.
Transforms the Phase 1 Abstract Syntax Tree (AST) into a structured
three-address-code (3AC) intermediate representation.
"""
from typing import List, Dict, Any, Optional
from .ast_nodes import (
    ASTNode, Program, FunctionDef, VarDecl, ArrayDecl, Block,
    Assignment, CompoundAssignment, ForLoop, WhileLoop, IfStatement,
    ReturnStatement, PrintStatement, ExprStatement, BinaryOp, UnaryOp,
    ArrayAccess, Identifier, IntLiteral
)


class IRInstruction:
    """
    Structured 3-address-code intermediate instruction.
    """
    def __init__(
        self,
        instruction_id: str,
        opcode: str,
        dest: Optional[str] = None,
        arg1: Optional[str] = None,
        arg2: Optional[str] = None,
        arg3: Optional[str] = None,
        line: int = 1,
        column: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = instruction_id
        self.opcode = opcode
        self.dest = dest
        self.arg1 = arg1
        self.arg2 = arg2
        self.arg3 = arg3
        self.line = line
        self.column = column
        self.metadata = metadata or {}

    def to_formatted_string(self) -> str:
        """Returns human-readable 3AC representation."""
        op = self.opcode
        if op == "LABEL":
            return f"{self.arg1}:"
        elif op == "DECLARE":
            return f"DECLARE {self.arg1} : {self.metadata.get('data_type', 'int')}"
        elif op == "CONST":
            return f"CONST {self.dest}, {self.arg1}"
        elif op == "LOAD":
            return f"LOAD {self.dest}, {self.arg1}"
        elif op == "STORE":
            return f"STORE {self.dest}, {self.arg1}"
        elif op == "LOAD_INDEXED":
            return f"LOAD_INDEXED {self.dest}, {self.arg1}[{self.arg2}]"
        elif op == "STORE_INDEXED":
            return f"STORE_INDEXED {self.dest}[{self.arg1}], {self.arg2}"
        elif op in ("ADD", "SUB", "MUL", "DIV", "MOD",
                    "COMPARE_LT", "COMPARE_LE", "COMPARE_GT", "COMPARE_GE", "COMPARE_EQ", "COMPARE_NE"):
            return f"{op} {self.dest}, {self.arg1}, {self.arg2}"
        elif op == "JUMP":
            return f"JUMP {self.arg1}"
        elif op == "BRANCH":
            return f"BRANCH {self.arg1}, {self.arg2}, {self.arg3}"
        elif op == "RETURN":
            return f"RETURN {self.arg1}" if self.arg1 else "RETURN"
        elif op == "PRINT":
            return f"PRINT {self.arg1}"
        else:
            operands = [x for x in [self.dest, self.arg1, self.arg2, self.arg3] if x is not None]
            return f"{op} {', '.join(operands)}"

    def to_dict(self) -> Dict[str, Any]:
        """Serializes instruction for JSON API response."""
        return {
            "id": self.id,
            "opcode": self.opcode,
            "dest": self.dest,
            "arg1": self.arg1,
            "arg2": self.arg2,
            "arg3": self.arg3,
            "line": self.line,
            "column": self.column,
            "formatted": self.to_formatted_string(),
            "metadata": self.metadata
        }


class IRGenerator:
    """
    Generates structured three-address code from AST.
    """
    def __init__(self):
        self.instructions: List[IRInstruction] = []
        self._temp_counter: int = 1
        self._label_counter: int = 1
        self._instruction_counter: int = 1

    def _next_temp(self) -> str:
        t = f"t{self._temp_counter}"
        self._temp_counter += 1
        return t

    def _next_label(self) -> str:
        l = f"L{self._label_counter}"
        self._label_counter += 1
        return l

    def _next_id(self) -> str:
        iid = f"ir_{self._instruction_counter}"
        self._instruction_counter += 1
        return iid

    def _emit(
        self,
        opcode: str,
        dest: Optional[str] = None,
        arg1: Optional[str] = None,
        arg2: Optional[str] = None,
        arg3: Optional[str] = None,
        line: int = 1,
        column: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> IRInstruction:
        instr = IRInstruction(
            instruction_id=self._next_id(),
            opcode=opcode,
            dest=dest,
            arg1=arg1,
            arg2=arg2,
            arg3=arg3,
            line=line,
            column=column,
            metadata=metadata or {}
        )
        self.instructions.append(instr)
        return instr

    def generate(self, ast: ASTNode) -> Dict[str, Any]:
        """
        Translates AST root into structured IR instructions.
        Returns dict with instructions and formatted string.
        """
        self.instructions = []
        self._temp_counter = 1
        self._label_counter = 1
        self._instruction_counter = 1

        if not ast:
            return {"instructions": [], "formatted": ""}

        self._visit_node(ast)

        formatted_lines = [instr.to_formatted_string() for instr in self.instructions]
        return {
            "instructions": [instr.to_dict() for instr in self.instructions],
            "formatted": "\n".join(formatted_lines),
            "instruction_count": len(self.instructions)
        }

    def _visit_node(self, node: ASTNode):
        if isinstance(node, Program):
            for decl in node.declarations:
                self._visit_node(decl)
        elif isinstance(node, FunctionDef):
            if node.body:
                self._visit_node(node.body)
        elif isinstance(node, Block):
            for stmt in node.statements:
                self._visit_node(stmt)
        elif isinstance(node, VarDecl):
            self._visit_var_decl(node)
        elif isinstance(node, ArrayDecl):
            self._visit_array_decl(node)
        elif isinstance(node, Assignment):
            self._visit_assignment(node)
        elif isinstance(node, CompoundAssignment):
            self._visit_compound_assignment(node)
        elif isinstance(node, ForLoop):
            self._visit_for_loop(node)
        elif isinstance(node, WhileLoop):
            self._visit_while_loop(node)
        elif isinstance(node, IfStatement):
            self._visit_if_statement(node)
        elif isinstance(node, ReturnStatement):
            self._visit_return_statement(node)
        elif isinstance(node, PrintStatement):
            self._visit_print_statement(node)
        elif isinstance(node, ExprStatement):
            self._generate_expr(node.expression)

    def _visit_var_decl(self, node: VarDecl):
        self._emit(
            opcode="DECLARE",
            arg1=node.name,
            line=node.line,
            column=node.column,
            metadata={"operation_type": "declaration", "data_type": node.type_name, "var_name": node.name}
        )
        if node.initializer:
            t_val = self._generate_expr(node.initializer)
            self._emit(
                opcode="STORE",
                dest=node.name,
                arg1=t_val,
                line=node.line,
                column=node.column,
                metadata={"operation_type": "memory_store", "dest_var": node.name, "source_var": t_val, "memory_region": "stack"}
            )

    def _visit_array_decl(self, node: ArrayDecl):
        self._emit(
            opcode="DECLARE",
            arg1=f"{node.name}[{node.size}]",
            line=node.line,
            column=node.column,
            metadata={
                "operation_type": "declaration",
                "data_type": f"{node.type_name}[]",
                "array_name": node.name,
                "size": node.size
            }
        )
        for idx, init_expr in enumerate(node.initializers):
            t_val = self._generate_expr(init_expr)
            t_idx = self._next_temp()
            self._emit(
                opcode="CONST",
                dest=t_idx,
                arg1=str(idx),
                line=init_expr.line,
                column=init_expr.column,
                metadata={"operation_type": "immediate", "value": idx}
            )
            self._emit(
                opcode="STORE_INDEXED",
                dest=node.name,
                arg1=t_idx,
                arg2=t_val,
                line=init_expr.line,
                column=init_expr.column,
                metadata={
                    "operation_type": "memory_store",
                    "array_name": node.name,
                    "index_expr": t_idx,
                    "index_value": idx,
                    "source_var": t_val,
                    "memory_region": "array_buffer",
                    "bytes_transferred": 4
                }
            )

    def _visit_assignment(self, node: Assignment):
        t_val = self._generate_expr(node.value)
        if isinstance(node.target, ArrayAccess):
            t_idx = self._generate_expr(node.target.index)
            self._emit(
                opcode="STORE_INDEXED",
                dest=node.target.array_name,
                arg1=t_idx,
                arg2=t_val,
                line=node.line,
                column=node.column,
                metadata={
                    "operation_type": "memory_store",
                    "array_name": node.target.array_name,
                    "index_expr": t_idx,
                    "source_var": t_val,
                    "memory_region": "array_buffer",
                    "bytes_transferred": 4
                }
            )
        elif isinstance(node.target, Identifier):
            self._emit(
                opcode="STORE",
                dest=node.target.name,
                arg1=t_val,
                line=node.line,
                column=node.column,
                metadata={
                    "operation_type": "memory_store",
                    "dest_var": node.target.name,
                    "source_var": t_val,
                    "memory_region": "stack"
                }
            )

    def _visit_compound_assignment(self, node: CompoundAssignment):
        op_map = {"+=": "ADD", "-=": "SUB", "*=": "MUL", "/=": "DIV", "%=": "MOD"}
        ir_op = op_map.get(node.op, "ADD")

        if isinstance(node.target, ArrayAccess):
            t_idx = self._generate_expr(node.target.index)
            t_curr = self._next_temp()
            self._emit(
                opcode="LOAD_INDEXED",
                dest=t_curr,
                arg1=node.target.array_name,
                arg2=t_idx,
                line=node.line,
                column=node.column,
                metadata={
                    "operation_type": "memory_load",
                    "array_name": node.target.array_name,
                    "index_expr": t_idx,
                    "memory_region": "array_buffer",
                    "bytes_transferred": 4
                }
            )
            t_val = self._generate_expr(node.value)
            t_res = self._next_temp()
            self._emit(
                opcode=ir_op,
                dest=t_res,
                arg1=t_curr,
                arg2=t_val,
                line=node.line,
                column=node.column,
                metadata={"operation_type": "arithmetic", "operator": node.op}
            )
            self._emit(
                opcode="STORE_INDEXED",
                dest=node.target.array_name,
                arg1=t_idx,
                arg2=t_res,
                line=node.line,
                column=node.column,
                metadata={
                    "operation_type": "memory_store",
                    "array_name": node.target.array_name,
                    "index_expr": t_idx,
                    "source_var": t_res,
                    "memory_region": "array_buffer",
                    "bytes_transferred": 4
                }
            )
        elif isinstance(node.target, Identifier):
            t_curr = self._next_temp()
            self._emit(
                opcode="LOAD",
                dest=t_curr,
                arg1=node.target.name,
                line=node.line,
                column=node.column,
                metadata={"operation_type": "memory_load", "source_var": node.target.name, "memory_region": "stack"}
            )
            t_val = self._generate_expr(node.value)
            t_res = self._next_temp()
            self._emit(
                opcode=ir_op,
                dest=t_res,
                arg1=t_curr,
                arg2=t_val,
                line=node.line,
                column=node.column,
                metadata={"operation_type": "arithmetic", "operator": node.op}
            )
            self._emit(
                opcode="STORE",
                dest=node.target.name,
                arg1=t_res,
                line=node.line,
                column=node.column,
                metadata={"operation_type": "memory_store", "dest_var": node.target.name, "source_var": t_res, "memory_region": "stack"}
            )

    def _visit_for_loop(self, node: ForLoop):
        # 1. Initialization
        if node.init:
            self._visit_node(node.init)

        l_start = self._next_label()
        l_body = self._next_label()
        l_end = self._next_label()

        self._emit(opcode="LABEL", arg1=l_start, line=node.line, column=node.column)

        # 2. Condition
        if node.condition:
            t_cond = self._generate_expr(node.condition)
            self._emit(
                opcode="BRANCH",
                arg1=t_cond,
                arg2=l_body,
                arg3=l_end,
                line=node.line,
                column=node.column,
                metadata={"operation_type": "control_flow"}
            )
        else:
            self._emit(opcode="JUMP", arg1=l_body, line=node.line, column=node.column)

        # 3. Body
        self._emit(opcode="LABEL", arg1=l_body, line=node.body.line, column=node.body.column)
        self._visit_node(node.body)

        # 4. Update
        if node.update:
            self._generate_expr(node.update)

        # 5. Jump back to loop test
        self._emit(opcode="JUMP", arg1=l_start, line=node.line, column=node.column)
        self._emit(opcode="LABEL", arg1=l_end, line=node.line, column=node.column)

    def _visit_while_loop(self, node: WhileLoop):
        l_start = self._next_label()
        l_body = self._next_label()
        l_end = self._next_label()

        self._emit(opcode="LABEL", arg1=l_start, line=node.line, column=node.column)
        t_cond = self._generate_expr(node.condition)
        self._emit(
            opcode="BRANCH",
            arg1=t_cond,
            arg2=l_body,
            arg3=l_end,
            line=node.line,
            column=node.column,
            metadata={"operation_type": "control_flow"}
        )
        self._emit(opcode="LABEL", arg1=l_body, line=node.body.line, column=node.body.column)
        self._visit_node(node.body)
        self._emit(opcode="JUMP", arg1=l_start, line=node.line, column=node.column)
        self._emit(opcode="LABEL", arg1=l_end, line=node.line, column=node.column)

    def _visit_if_statement(self, node: IfStatement):
        l_then = self._next_label()
        l_else = self._next_label() if node.else_branch else None
        l_end = self._next_label()

        t_cond = self._generate_expr(node.condition)
        false_target = l_else if l_else else l_end

        self._emit(
            opcode="BRANCH",
            arg1=t_cond,
            arg2=l_then,
            arg3=false_target,
            line=node.line,
            column=node.column,
            metadata={"operation_type": "control_flow"}
        )

        self._emit(opcode="LABEL", arg1=l_then, line=node.then_branch.line, column=node.then_branch.column)
        self._visit_node(node.then_branch)

        if node.else_branch:
            self._emit(opcode="JUMP", arg1=l_end, line=node.line, column=node.column)
            self._emit(opcode="LABEL", arg1=l_else, line=node.else_branch.line, column=node.else_branch.column)
            self._visit_node(node.else_branch)

        self._emit(opcode="LABEL", arg1=l_end, line=node.line, column=node.column)

    def _visit_return_statement(self, node: ReturnStatement):
        t_val = self._generate_expr(node.value) if node.value else None
        self._emit(
            opcode="RETURN",
            arg1=t_val,
            line=node.line,
            column=node.column,
            metadata={"operation_type": "control_flow"}
        )

    def _visit_print_statement(self, node: PrintStatement):
        t_val = self._generate_expr(node.expression)
        self._emit(
            opcode="PRINT",
            arg1=t_val,
            line=node.line,
            column=node.column,
            metadata={"operation_type": "io"}
        )

    def _generate_expr(self, expr: ASTNode) -> str:
        """Evaluates an AST expression and returns the operand/temporary holding the result."""
        if isinstance(expr, IntLiteral):
            t = self._next_temp()
            self._emit(
                opcode="CONST",
                dest=t,
                arg1=str(expr.value),
                line=expr.line,
                column=expr.column,
                metadata={"operation_type": "immediate", "value": expr.value}
            )
            return t

        elif isinstance(expr, Identifier):
            t = self._next_temp()
            self._emit(
                opcode="LOAD",
                dest=t,
                arg1=expr.name,
                line=expr.line,
                column=expr.column,
                metadata={"operation_type": "memory_load", "source_var": expr.name, "memory_region": "stack"}
            )
            return t

        elif isinstance(expr, ArrayAccess):
            t_idx = self._generate_expr(expr.index)
            t_res = self._next_temp()
            self._emit(
                opcode="LOAD_INDEXED",
                dest=t_res,
                arg1=expr.array_name,
                arg2=t_idx,
                line=expr.line,
                column=expr.column,
                metadata={
                    "operation_type": "memory_load",
                    "array_name": expr.array_name,
                    "index_expr": t_idx,
                    "memory_region": "array_buffer",
                    "bytes_transferred": 4
                }
            )
            return t_res

        elif isinstance(expr, BinaryOp):
            t_left = self._generate_expr(expr.left)
            t_right = self._generate_expr(expr.right)
            t_res = self._next_temp()

            op_map = {
                "+": "ADD",
                "-": "SUB",
                "*": "MUL",
                "/": "DIV",
                "%": "MOD",
                "<": "COMPARE_LT",
                "<=": "COMPARE_LE",
                ">": "COMPARE_GT",
                ">=": "COMPARE_GE",
                "==": "COMPARE_EQ",
                "!=": "COMPARE_NE",
                "&&": "COMPARE_NE",
                "||": "COMPARE_NE"
            }
            opcode = op_map.get(expr.op, "ADD")
            is_cmp = opcode.startswith("COMPARE")
            self._emit(
                opcode=opcode,
                dest=t_res,
                arg1=t_left,
                arg2=t_right,
                line=expr.line,
                column=expr.column,
                metadata={
                    "operation_type": "comparison" if is_cmp else "arithmetic",
                    "operator": expr.op
                }
            )
            return t_res

        elif isinstance(expr, UnaryOp):
            if expr.op == "-":
                t_val = self._generate_expr(expr.operand)
                t_zero = self._next_temp()
                self._emit(opcode="CONST", dest=t_zero, arg1="0", line=expr.line, column=expr.column)
                t_res = self._next_temp()
                self._emit(
                    opcode="SUB",
                    dest=t_res,
                    arg1=t_zero,
                    arg2=t_val,
                    line=expr.line,
                    column=expr.column,
                    metadata={"operation_type": "arithmetic", "operator": "-"}
                )
                return t_res

            elif expr.op == "!":
                t_val = self._generate_expr(expr.operand)
                t_zero = self._next_temp()
                self._emit(opcode="CONST", dest=t_zero, arg1="0", line=expr.line, column=expr.column)
                t_res = self._next_temp()
                self._emit(
                    opcode="COMPARE_EQ",
                    dest=t_res,
                    arg1=t_val,
                    arg2=t_zero,
                    line=expr.line,
                    column=expr.column,
                    metadata={"operation_type": "comparison", "operator": "!"}
                )
                return t_res

            elif expr.op in ("++", "--"):
                if isinstance(expr.operand, Identifier):
                    var_name = expr.operand.name
                    t_curr = self._next_temp()
                    self._emit(
                        opcode="LOAD",
                        dest=t_curr,
                        arg1=var_name,
                        line=expr.line,
                        column=expr.column,
                        metadata={"operation_type": "memory_load", "source_var": var_name, "memory_region": "stack"}
                    )
                    t_one = self._next_temp()
                    self._emit(opcode="CONST", dest=t_one, arg1="1", line=expr.line, column=expr.column)
                    t_new = self._next_temp()
                    ir_op = "ADD" if expr.op == "++" else "SUB"
                    self._emit(
                        opcode=ir_op,
                        dest=t_new,
                        arg1=t_curr,
                        arg2=t_one,
                        line=expr.line,
                        column=expr.column,
                        metadata={"operation_type": "arithmetic", "operator": expr.op}
                    )
                    self._emit(
                        opcode="STORE",
                        dest=var_name,
                        arg1=t_new,
                        line=expr.line,
                        column=expr.column,
                        metadata={"operation_type": "memory_store", "dest_var": var_name, "source_var": t_new, "memory_region": "stack"}
                    )
                    return t_new if expr.is_prefix else t_curr

        # Fallback
        t_fallback = self._next_temp()
        self._emit(opcode="CONST", dest=t_fallback, arg1="0", line=expr.line, column=expr.column)
        return t_fallback
