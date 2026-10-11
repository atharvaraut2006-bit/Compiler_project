"""
Semantic Analyzer for Phase 1 of C Compiler Front End.
Maintains scoped symbol tables, validates types and declarations,
and reports clear diagnostics (errors and warnings).
"""
from typing import Dict, List, Optional, Any
from .ast_nodes import (
    ASTNode, Program, FunctionDef, VarDecl, ArrayDecl, Block,
    Assignment, CompoundAssignment, ForLoop, WhileLoop, IfStatement,
    ReturnStatement, PrintStatement, ExprStatement, BinaryOp, UnaryOp,
    ArrayAccess, Identifier, IntLiteral
)


class Diagnostic:
    """Represents a compiler diagnostic (error or warning)."""
    def __init__(self, severity: str, message: str, line: int, column: int):
        self.severity = severity  # "error" or "warning"
        self.message = message
        self.line = line
        self.column = column

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "message": self.message,
            "line": self.line,
            "column": self.column
        }

    def __repr__(self) -> str:
        return f"[{self.severity.upper()}] L{self.line}:C{self.column} - {self.message}"


class Symbol:
    """Represents a symbol in the symbol table."""
    def __init__(
        self,
        name: str,
        type_name: str,
        is_array: bool = False,
        size: Optional[int] = None,
        line: int = 1,
        column: int = 1,
        scope_level: int = 0
    ):
        self.name = name
        self.type_name = type_name
        self.is_array = is_array
        self.size = size
        self.line = line
        self.column = column
        self.scope_level = scope_level

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type_name": self.type_name,
            "is_array": self.is_array,
            "size": self.size,
            "line": self.line,
            "column": self.column,
            "scope_level": self.scope_level
        }


class Scope:
    """Lexical scope holding symbol definitions."""
    def __init__(self, parent: Optional['Scope'] = None, level: int = 0):
        self.parent = parent
        self.level = level
        self.symbols: Dict[str, Symbol] = {}

    def define(self, symbol: Symbol) -> bool:
        if symbol.name in self.symbols:
            return False  # Duplicate declaration in current scope
        symbol.scope_level = self.level
        self.symbols[symbol.name] = symbol
        return True

    def resolve(self, name: str) -> Optional[Symbol]:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.resolve(name)
        return None


class SemanticError(Exception):
    """Exception raised when fatal semantic errors occur."""
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"Semantic error at line {line}, column {column}: {message}")
        self.message = message
        self.line = line
        self.column = column


class SemanticAnalyzer:
    """
    Performs type checking, symbol resolution, and semantic validation.
    """
    def __init__(self):
        self.global_scope = Scope(level=0)
        self.current_scope = self.global_scope
        self.diagnostics: List[Diagnostic] = []
        self.all_symbols: Dict[str, Dict[str, Any]] = {}

    def _error(self, message: str, line: int, column: int):
        self.diagnostics.append(Diagnostic("error", message, line, column))

    def _warning(self, message: str, line: int, column: int):
        self.diagnostics.append(Diagnostic("warning", message, line, column))

    def _enter_scope(self):
        self.current_scope = Scope(parent=self.current_scope, level=self.current_scope.level + 1)

    def _exit_scope(self):
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent

    def analyze(self, ast: Program) -> Dict[str, Any]:
        self.diagnostics.clear()
        self.all_symbols.clear()
        self.global_scope = Scope(level=0)
        self.current_scope = self.global_scope

        self._visit(ast)

        has_errors = any(d.severity == "error" for d in self.diagnostics)
        return {
            "success": not has_errors,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "symbols": self.all_symbols,
            "error_count": sum(1 for d in self.diagnostics if d.severity == "error"),
            "warning_count": sum(1 for d in self.diagnostics if d.severity == "warning")
        }

    def _visit(self, node: Optional[ASTNode]):
        if node is None:
            return

        method_name = f"_visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self._generic_visit)
        return visitor(node)

    def _generic_visit(self, node: ASTNode):
        for attr, value in vars(node).items():
            if isinstance(value, ASTNode):
                self._visit(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, ASTNode):
                        self._visit(item)

    # -------------------------------------------------------------
    # Declarations and Functions
    # -------------------------------------------------------------
    def _visit_Program(self, node: Program):
        for decl in node.declarations:
            self._visit(decl)

    def _visit_FunctionDef(self, node: FunctionDef):
        # Define function symbol in current (global) scope
        sym = Symbol(
            name=node.name,
            type_name=f"function()->{node.return_type}",
            line=node.line,
            column=node.column
        )
        if not self.current_scope.define(sym):
            self._error(f"Redeclaration of function '{node.name}'", node.line, node.column)
        else:
            self.all_symbols[node.name] = sym.to_dict()

        # Enter function scope
        self._enter_scope()

        # Define parameters in function scope
        for param in node.params:
            p_sym = Symbol(
                name=param["name"],
                type_name=param["type"],
                line=node.line,
                column=node.column
            )
            if not self.current_scope.define(p_sym):
                self._error(f"Redeclaration of parameter '{param['name']}' in function '{node.name}'", node.line, node.column)
            else:
                self.all_symbols[param["name"]] = p_sym.to_dict()

        # Visit function body
        if node.body:
            for stmt in node.body.statements:
                self._visit(stmt)

        self._exit_scope()

    def _visit_VarDecl(self, node: VarDecl):
        sym = Symbol(
            name=node.name,
            type_name=node.type_name,
            is_array=False,
            line=node.line,
            column=node.column
        )
        if not self.current_scope.define(sym):
            self._error(f"Redeclaration of variable '{node.name}' in the same scope", node.line, node.column)
        else:
            self.all_symbols[node.name] = sym.to_dict()

        if node.initializer:
            self._visit(node.initializer)

    def _visit_ArrayDecl(self, node: ArrayDecl):
        if node.size <= 0:
            self._error(f"Array '{node.name}' declared with invalid size {node.size}; size must be positive", node.line, node.column)

        sym = Symbol(
            name=node.name,
            type_name=node.type_name,
            is_array=True,
            size=node.size,
            line=node.line,
            column=node.column
        )
        if not self.current_scope.define(sym):
            self._error(f"Redeclaration of array '{node.name}' in the same scope", node.line, node.column)
        else:
            self.all_symbols[node.name] = sym.to_dict()

        # Check initializer list size
        if node.initializers:
            if len(node.initializers) > node.size:
                self._error(
                    f"Initializer list has {len(node.initializers)} elements, exceeding declared size {node.size} of array '{node.name}'",
                    node.line, node.column
                )
            for init_expr in node.initializers:
                self._visit(init_expr)

    def _visit_Block(self, node: Block):
        self._enter_scope()
        for stmt in node.statements:
            self._visit(stmt)
        self._exit_scope()

    # -------------------------------------------------------------
    # Control Flow Statements
    # -------------------------------------------------------------
    def _visit_ForLoop(self, node: ForLoop):
        self._enter_scope()
        if node.init:
            self._visit(node.init)
        if node.condition:
            self._visit(node.condition)
        if node.update:
            self._visit(node.update)
        self._visit(node.body)
        self._exit_scope()

    def _visit_WhileLoop(self, node: WhileLoop):
        if node.condition:
            self._visit(node.condition)
        self._visit(node.body)

    def _visit_IfStatement(self, node: IfStatement):
        if node.condition:
            self._visit(node.condition)
        self._visit(node.then_branch)
        if node.else_branch:
            self._visit(node.else_branch)

    def _visit_ReturnStatement(self, node: ReturnStatement):
        if node.value:
            self._visit(node.value)

    def _visit_PrintStatement(self, node: PrintStatement):
        self._visit(node.expression)

    def _visit_ExprStatement(self, node: ExprStatement):
        self._visit(node.expression)

    # -------------------------------------------------------------
    # Expressions & Assignments
    # -------------------------------------------------------------
    def _visit_Assignment(self, node: Assignment):
        self._visit(node.target)
        self._visit(node.value)

    def _visit_CompoundAssignment(self, node: CompoundAssignment):
        self._visit(node.target)
        self._visit(node.value)

    def _visit_BinaryOp(self, node: BinaryOp):
        self._visit(node.left)
        self._visit(node.right)

        # Check division by zero for constant literals
        if node.op in ("/", "%") and isinstance(node.right, IntLiteral) and node.right.value == 0:
            self._error(f"Division by zero detected in expression", node.line, node.column)

    def _visit_UnaryOp(self, node: UnaryOp):
        self._visit(node.operand)

    def _visit_ArrayAccess(self, node: ArrayAccess):
        sym = self.current_scope.resolve(node.array_name)
        if not sym:
            self._error(f"Undeclared array identifier '{node.array_name}'", node.line, node.column)
        elif not sym.is_array:
            self._error(f"Cannot index non-array scalar variable '{node.array_name}'", node.line, node.column)
        else:
            # Static bounds check if index is an integer literal
            if isinstance(node.index, IntLiteral) and sym.size is not None:
                if node.index.value < 0 or node.index.value >= sym.size:
                    self._error(
                        f"Array index {node.index.value} out of bounds for array '{node.array_name}' of declared size {sym.size}",
                        node.line, node.column
                    )

        self._visit(node.index)

    def _visit_Identifier(self, node: Identifier):
        sym = self.current_scope.resolve(node.name)
        if not sym:
            self._error(f"Undeclared variable '{node.name}'", node.line, node.column)
        elif sym.is_array:
            # Array used as raw scalar identifier without index
            pass

    def _visit_IntLiteral(self, node: IntLiteral):
        pass
