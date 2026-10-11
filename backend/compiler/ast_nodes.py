"""
AST Node definitions for Phase 1 of the C Compiler Front End.
"""
from typing import List, Optional, Any, Dict


class ASTNode:
    """Base class for all AST nodes."""
    def __init__(self, line: int = 1, column: int = 1):
        self.line = line
        self.column = column

    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement to_dict()")


class Program(ASTNode):
    """Root program node containing functions and/or top-level statements."""
    def __init__(self, declarations: List[ASTNode], line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.declarations = declarations

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "Program",
            "line": self.line,
            "column": self.column,
            "body": [decl.to_dict() for decl in self.declarations]
        }


class FunctionDef(ASTNode):
    """Function definition node (e.g., int main() { ... })."""
    def __init__(self, return_type: str, name: str, params: List[Dict[str, str]], body: 'Block', line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.return_type = return_type
        self.name = name
        self.params = params
        self.body = body

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "FunctionDef",
            "name": self.name,
            "return_type": self.return_type,
            "params": self.params,
            "body": self.body.to_dict() if self.body else None,
            "line": self.line,
            "column": self.column
        }


class VarDecl(ASTNode):
    """Scalar variable declaration node (e.g., int x = 10; or int x;)."""
    def __init__(self, type_name: str, name: str, initializer: Optional[ASTNode] = None, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.type_name = type_name
        self.name = name
        self.initializer = initializer

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "VarDecl",
            "type_name": self.type_name,
            "name": self.name,
            "initializer": self.initializer.to_dict() if self.initializer else None,
            "line": self.line,
            "column": self.column
        }


class ArrayDecl(ASTNode):
    """Array declaration node (e.g., int arr[4] = {10, 20, 30, 40};)."""
    def __init__(self, type_name: str, name: str, size: int, initializers: Optional[List[ASTNode]] = None, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.type_name = type_name
        self.name = name
        self.size = size
        self.initializers = initializers or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "ArrayDecl",
            "type_name": self.type_name,
            "name": self.name,
            "size": self.size,
            "initializers": [init.to_dict() for init in self.initializers],
            "line": self.line,
            "column": self.column
        }


class Block(ASTNode):
    """Block statement containing a list of statements."""
    def __init__(self, statements: List[ASTNode], line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.statements = statements

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "Block",
            "statements": [stmt.to_dict() for stmt in self.statements],
            "line": self.line,
            "column": self.column
        }


class Assignment(ASTNode):
    """Assignment statement (e.g., x = y + 2; or arr[i] = 5;)."""
    def __init__(self, target: ASTNode, value: ASTNode, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.target = target
        self.value = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "Assignment",
            "target": self.target.to_dict(),
            "value": self.value.to_dict(),
            "line": self.line,
            "column": self.column
        }


class CompoundAssignment(ASTNode):
    """Compound assignment (e.g., sum += arr[i];)."""
    def __init__(self, target: ASTNode, op: str, value: ASTNode, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.target = target
        self.op = op
        self.value = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "CompoundAssignment",
            "target": self.target.to_dict(),
            "op": self.op,
            "value": self.value.to_dict(),
            "line": self.line,
            "column": self.column
        }


class ForLoop(ASTNode):
    """For loop statement."""
    def __init__(self, init: Optional[ASTNode], condition: Optional[ASTNode], update: Optional[ASTNode], body: ASTNode, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.init = init
        self.condition = condition
        self.update = update
        self.body = body

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "ForLoop",
            "init": self.init.to_dict() if self.init else None,
            "condition": self.condition.to_dict() if self.condition else None,
            "update": self.update.to_dict() if self.update else None,
            "body": self.body.to_dict(),
            "line": self.line,
            "column": self.column
        }


class WhileLoop(ASTNode):
    """While loop statement."""
    def __init__(self, condition: ASTNode, body: ASTNode, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.condition = condition
        self.body = body

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "WhileLoop",
            "condition": self.condition.to_dict(),
            "body": self.body.to_dict(),
            "line": self.line,
            "column": self.column
        }


class IfStatement(ASTNode):
    """If-Else conditional statement."""
    def __init__(self, condition: ASTNode, then_branch: ASTNode, else_branch: Optional[ASTNode] = None, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "IfStatement",
            "condition": self.condition.to_dict(),
            "then_branch": self.then_branch.to_dict(),
            "else_branch": self.else_branch.to_dict() if self.else_branch else None,
            "line": self.line,
            "column": self.column
        }


class ReturnStatement(ASTNode):
    """Return statement (e.g., return 0;)."""
    def __init__(self, value: Optional[ASTNode] = None, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.value = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "ReturnStatement",
            "value": self.value.to_dict() if self.value else None,
            "line": self.line,
            "column": self.column
        }


class PrintStatement(ASTNode):
    """Built-in print statement (e.g., print(sum);)."""
    def __init__(self, expression: ASTNode, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.expression = expression

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "PrintStatement",
            "expression": self.expression.to_dict(),
            "line": self.line,
            "column": self.column
        }


class ExprStatement(ASTNode):
    """Standalone expression statement."""
    def __init__(self, expression: ASTNode, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.expression = expression

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "ExprStatement",
            "expression": self.expression.to_dict(),
            "line": self.line,
            "column": self.column
        }


class BinaryOp(ASTNode):
    """Binary expression (e.g., a + b, x < y, a && b)."""
    def __init__(self, left: ASTNode, op: str, right: ASTNode, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.left = left
        self.op = op
        self.right = right

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "BinaryOp",
            "op": self.op,
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
            "line": self.line,
            "column": self.column
        }


class UnaryOp(ASTNode):
    """Unary expression (e.g., -x, !flag, ++i)."""
    def __init__(self, op: str, operand: ASTNode, is_prefix: bool = True, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.op = op
        self.operand = operand
        self.is_prefix = is_prefix

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "UnaryOp",
            "op": self.op,
            "operand": self.operand.to_dict(),
            "is_prefix": self.is_prefix,
            "line": self.line,
            "column": self.column
        }


class ArrayAccess(ASTNode):
    """Array indexing expression (e.g., arr[i])."""
    def __init__(self, array_name: str, index: ASTNode, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.array_name = array_name
        self.index = index

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "ArrayAccess",
            "array_name": self.array_name,
            "index": self.index.to_dict(),
            "line": self.line,
            "column": self.column
        }


class Identifier(ASTNode):
    """Identifier node."""
    def __init__(self, name: str, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.name = name

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "Identifier",
            "name": self.name,
            "line": self.line,
            "column": self.column
        }


class IntLiteral(ASTNode):
    """Integer literal constant node."""
    def __init__(self, value: int, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.value = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "IntLiteral",
            "value": self.value,
            "line": self.line,
            "column": self.column
        }
