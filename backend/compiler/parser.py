"""
Recursive Descent Parser for Phase 1 of C Compiler Front End.
Constructs an Abstract Syntax Tree (AST) with precedence climbing and error locations.
"""
from typing import List, Optional, Any, Union
from .lexer import Token, TokenType
from .ast_nodes import (
    ASTNode, Program, FunctionDef, VarDecl, ArrayDecl, Block,
    Assignment, CompoundAssignment, ForLoop, WhileLoop, IfStatement,
    ReturnStatement, PrintStatement, ExprStatement, BinaryOp, UnaryOp,
    ArrayAccess, Identifier, IntLiteral
)


class ParserError(Exception):
    """Exception raised for syntax errors during parsing."""
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"Syntax error at line {line}, column {column}: {message}")
        self.message = message
        self.line = line
        self.column = column


class Parser:
    """
    Handwritten recursive-descent parser for the supported C subset.
    """
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def _current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    def _peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def _advance(self) -> Token:
        tok = self._current()
        if tok.type != TokenType.EOF:
            self.pos += 1
        return tok

    def _check(self, token_type: TokenType) -> bool:
        return self._current().type == token_type

    def _match(self, *token_types: TokenType) -> bool:
        for tt in token_types:
            if self._check(tt):
                self._advance()
                return True
        return False

    def _expect(self, token_type: TokenType, error_message: str) -> Token:
        tok = self._current()
        if tok.type == token_type:
            return self._advance()
        raise ParserError(f"{error_message} (got '{tok.value}')", tok.line, tok.column)

    # -------------------------------------------------------------
    # Entry Point: Program Parsing
    # -------------------------------------------------------------
    def parse(self) -> Program:
        declarations: List[ASTNode] = []
        first_token = self._current()
        start_line = first_token.line
        start_col = first_token.column

        while not self._check(TokenType.EOF):
            decl = self._parse_top_level()
            if decl:
                declarations.append(decl)

        return Program(declarations, line=start_line, column=start_col)

    def _parse_top_level(self) -> ASTNode:
        # Check if function definition: int ident ( ... ) { ... }
        if self._check(TokenType.INT) and self._peek(1).type == TokenType.IDENTIFIER and self._peek(2).type == TokenType.LPAREN:
            return self._parse_function_definition()
        # Otherwise, parse general statement (declaration, loop, etc.)
        return self._parse_statement()

    def _parse_function_definition(self) -> FunctionDef:
        ret_tok = self._expect(TokenType.INT, "Expected return type 'int'")
        name_tok = self._expect(TokenType.IDENTIFIER, "Expected function name")
        self._expect(TokenType.LPAREN, "Expected '(' after function name")
        
        params = []
        if not self._check(TokenType.RPAREN):
            # Parse parameters: int a, int b
            while True:
                p_type = self._expect(TokenType.INT, "Expected parameter type 'int'")
                p_name = self._expect(TokenType.IDENTIFIER, "Expected parameter name")
                params.append({"type": p_type.value, "name": p_name.value})
                if not self._match(TokenType.COMMA):
                    break

        self._expect(TokenType.RPAREN, "Expected ')' after parameter list")
        self._expect(TokenType.LBRACE, "Expected '{' to start function body")
        body = self._parse_block_body(ret_tok.line, ret_tok.column)
        return FunctionDef(
            return_type=ret_tok.value,
            name=name_tok.value,
            params=params,
            body=body,
            line=ret_tok.line,
            column=ret_tok.column
        )

    # -------------------------------------------------------------
    # Statements
    # -------------------------------------------------------------
    def _parse_statement(self) -> ASTNode:
        tok = self._current()

        # Variable or array declaration: int ...
        if tok.type == TokenType.INT:
            return self._parse_declaration_statement()

        # Block statement: { ... }
        if tok.type == TokenType.LBRACE:
            self._advance()
            return self._parse_block_body(tok.line, tok.column)

        # For loop: for ( ... )
        if tok.type == TokenType.FOR:
            return self._parse_for_loop()

        # While loop: while ( ... )
        if tok.type == TokenType.WHILE:
            return self._parse_while_loop()

        # If statement: if ( ... )
        if tok.type == TokenType.IF:
            return self._parse_if_statement()

        # Return statement: return ... ;
        if tok.type == TokenType.RETURN:
            return self._parse_return_statement()

        # Print statement: print( ... );
        if tok.type == TokenType.PRINT:
            return self._parse_print_statement()

        # Assignment, increment, or expression statement
        return self._parse_expr_or_assignment_statement()

    def _parse_declaration_statement(self) -> ASTNode:
        type_tok = self._expect(TokenType.INT, "Expected type 'int'")
        name_tok = self._expect(TokenType.IDENTIFIER, "Expected identifier in declaration")

        # Array declaration: int arr[N] = { ... }; or int arr[N];
        if self._match(TokenType.LBRACKET):
            size_tok = self._expect(TokenType.INT_LITERAL, "Expected integer literal for array size")
            self._expect(TokenType.RBRACKET, "Expected ']' after array size")

            initializers: List[ASTNode] = []
            if self._match(TokenType.ASSIGN):
                self._expect(TokenType.LBRACE, "Expected '{' for array initializer list")
                if not self._check(TokenType.RBRACE):
                    while True:
                        init_expr = self._parse_expression()
                        initializers.append(init_expr)
                        if not self._match(TokenType.COMMA):
                            break
                self._expect(TokenType.RBRACE, "Expected '}' after array initializer list")

            self._expect(TokenType.SEMICOLON, "Expected ';' after array declaration")
            return ArrayDecl(
                type_name=type_tok.value,
                name=name_tok.value,
                size=size_tok.value,
                initializers=initializers,
                line=type_tok.line,
                column=type_tok.column
            )

        # Scalar variable declaration: int x = 10; or int x;
        initializer = None
        if self._match(TokenType.ASSIGN):
            initializer = self._parse_expression()

        self._expect(TokenType.SEMICOLON, "Expected ';' after variable declaration")
        return VarDecl(
            type_name=type_tok.value,
            name=name_tok.value,
            initializer=initializer,
            line=type_tok.line,
            column=type_tok.column
        )

    def _parse_block_body(self, line: int, column: int) -> Block:
        stmts: List[ASTNode] = []
        while not self._check(TokenType.RBRACE) and not self._check(TokenType.EOF):
            stmts.append(self._parse_statement())
        self._expect(TokenType.RBRACE, "Expected '}' at end of block")
        return Block(statements=stmts, line=line, column=column)

    def _parse_for_loop(self) -> ForLoop:
        for_tok = self._expect(TokenType.FOR, "Expected 'for'")
        self._expect(TokenType.LPAREN, "Expected '(' after 'for'")

        # Init: int i = 0 or i = 0 or empty
        init = None
        if not self._check(TokenType.SEMICOLON):
            if self._check(TokenType.INT):
                type_tok = self._advance()
                name_tok = self._expect(TokenType.IDENTIFIER, "Expected loop variable identifier")
                init_val = None
                if self._match(TokenType.ASSIGN):
                    init_val = self._parse_expression()
                init = VarDecl(type_tok.value, name_tok.value, init_val, line=type_tok.line, column=type_tok.column)
            else:
                target = self._parse_primary()
                if self._match(TokenType.ASSIGN):
                    val = self._parse_expression()
                    init = Assignment(target, val, line=target.line, column=target.column)
                else:
                    init = ExprStatement(target, line=target.line, column=target.column)
        self._expect(TokenType.SEMICOLON, "Expected ';' after for-loop initialization")

        # Condition
        cond = None
        if not self._check(TokenType.SEMICOLON):
            cond = self._parse_expression()
        self._expect(TokenType.SEMICOLON, "Expected ';' after for-loop condition")

        # Update: i++ or sum = sum + 1 or i += 1
        update = None
        if not self._check(TokenType.RPAREN):
            target = self._parse_primary()
            if self._match(TokenType.INCREMENT):
                update = UnaryOp("++", target, is_prefix=False, line=target.line, column=target.column)
            elif self._match(TokenType.DECREMENT):
                update = UnaryOp("--", target, is_prefix=False, line=target.line, column=target.column)
            elif self._match(TokenType.PLUS_ASSIGN):
                val = self._parse_expression()
                update = CompoundAssignment(target, "+=", val, line=target.line, column=target.column)
            elif self._match(TokenType.MINUS_ASSIGN):
                val = self._parse_expression()
                update = CompoundAssignment(target, "-=", val, line=target.line, column=target.column)
            elif self._match(TokenType.STAR_ASSIGN):
                val = self._parse_expression()
                update = CompoundAssignment(target, "*=", val, line=target.line, column=target.column)
            elif self._match(TokenType.ASSIGN):
                val = self._parse_expression()
                update = Assignment(target, val, line=target.line, column=target.column)
            else:
                update = target

        self._expect(TokenType.RPAREN, "Expected ')' after for-loop update")
        body = self._parse_statement()
        return ForLoop(init, cond, update, body, line=for_tok.line, column=for_tok.column)

    def _parse_while_loop(self) -> WhileLoop:
        while_tok = self._expect(TokenType.WHILE, "Expected 'while'")
        self._expect(TokenType.LPAREN, "Expected '(' after 'while'")
        cond = self._parse_expression()
        self._expect(TokenType.RPAREN, "Expected ')' after while condition")
        body = self._parse_statement()
        return WhileLoop(condition=cond, body=body, line=while_tok.line, column=while_tok.column)

    def _parse_if_statement(self) -> IfStatement:
        if_tok = self._expect(TokenType.IF, "Expected 'if'")
        self._expect(TokenType.LPAREN, "Expected '(' after 'if'")
        cond = self._parse_expression()
        self._expect(TokenType.RPAREN, "Expected ')' after if condition")
        then_branch = self._parse_statement()
        else_branch = None
        if self._match(TokenType.ELSE):
            else_branch = self._parse_statement()
        return IfStatement(cond, then_branch, else_branch, line=if_tok.line, column=if_tok.column)

    def _parse_return_statement(self) -> ReturnStatement:
        ret_tok = self._expect(TokenType.RETURN, "Expected 'return'")
        val = None
        if not self._check(TokenType.SEMICOLON):
            val = self._parse_expression()
        self._expect(TokenType.SEMICOLON, "Expected ';' after return statement")
        return ReturnStatement(value=val, line=ret_tok.line, column=ret_tok.column)

    def _parse_print_statement(self) -> PrintStatement:
        print_tok = self._expect(TokenType.PRINT, "Expected 'print'")
        self._expect(TokenType.LPAREN, "Expected '(' after 'print'")
        expr = self._parse_expression()
        self._expect(TokenType.RPAREN, "Expected ')' after print expression")
        self._expect(TokenType.SEMICOLON, "Expected ';' after print statement")
        return PrintStatement(expression=expr, line=print_tok.line, column=print_tok.column)

    def _parse_expr_or_assignment_statement(self) -> ASTNode:
        expr = self._parse_expression()

        # Check for assignment operators: =, +=, -=, *=, /=
        if self._match(TokenType.ASSIGN):
            val = self._parse_expression()
            self._expect(TokenType.SEMICOLON, "Expected ';' after assignment")
            return Assignment(target=expr, value=val, line=expr.line, column=expr.column)

        if self._match(TokenType.PLUS_ASSIGN):
            val = self._parse_expression()
            self._expect(TokenType.SEMICOLON, "Expected ';' after compound assignment")
            return CompoundAssignment(target=expr, op="+=", value=val, line=expr.line, column=expr.column)

        if self._match(TokenType.MINUS_ASSIGN):
            val = self._parse_expression()
            self._expect(TokenType.SEMICOLON, "Expected ';' after compound assignment")
            return CompoundAssignment(target=expr, op="-=", value=val, line=expr.line, column=expr.column)

        if self._match(TokenType.STAR_ASSIGN):
            val = self._parse_expression()
            self._expect(TokenType.SEMICOLON, "Expected ';' after compound assignment")
            return CompoundAssignment(target=expr, op="*=", value=val, line=expr.line, column=expr.column)

        if self._match(TokenType.SLASH_ASSIGN):
            val = self._parse_expression()
            self._expect(TokenType.SEMICOLON, "Expected ';' after compound assignment")
            return CompoundAssignment(target=expr, op="/=", value=val, line=expr.line, column=expr.column)

        # Post-increment/decrement statement: x++;
        if self._match(TokenType.INCREMENT):
            self._expect(TokenType.SEMICOLON, "Expected ';' after '++'")
            return ExprStatement(UnaryOp("++", expr, is_prefix=False, line=expr.line, column=expr.column), line=expr.line, column=expr.column)

        if self._match(TokenType.DECREMENT):
            self._expect(TokenType.SEMICOLON, "Expected ';' after '--'")
            return ExprStatement(UnaryOp("--", expr, is_prefix=False, line=expr.line, column=expr.column), line=expr.line, column=expr.column)

        self._expect(TokenType.SEMICOLON, "Expected ';' after expression statement")
        return ExprStatement(expression=expr, line=expr.line, column=expr.column)

    # -------------------------------------------------------------
    # Expressions: Operator Precedence Climbing
    # -------------------------------------------------------------
    def _parse_expression(self) -> ASTNode:
        return self._parse_logical_or()

    def _parse_logical_or(self) -> ASTNode:
        left = self._parse_logical_and()
        while self._match(TokenType.LOGICAL_OR):
            op_tok = self.tokens[self.pos - 1]
            right = self._parse_logical_and()
            left = BinaryOp(left, op_tok.value, right, line=left.line, column=left.column)
        return left

    def _parse_logical_and(self) -> ASTNode:
        left = self._parse_equality()
        while self._match(TokenType.LOGICAL_AND):
            op_tok = self.tokens[self.pos - 1]
            right = self._parse_equality()
            left = BinaryOp(left, op_tok.value, right, line=left.line, column=left.column)
        return left

    def _parse_equality(self) -> ASTNode:
        left = self._parse_relational()
        while self._match(TokenType.EQ, TokenType.NE):
            op_tok = self.tokens[self.pos - 1]
            right = self._parse_relational()
            left = BinaryOp(left, op_tok.value, right, line=left.line, column=left.column)
        return left

    def _parse_relational(self) -> ASTNode:
        left = self._parse_additive()
        while self._match(TokenType.LT, TokenType.LE, TokenType.GT, TokenType.GE):
            op_tok = self.tokens[self.pos - 1]
            right = self._parse_additive()
            left = BinaryOp(left, op_tok.value, right, line=left.line, column=left.column)
        return left

    def _parse_additive(self) -> ASTNode:
        left = self._parse_multiplicative()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op_tok = self.tokens[self.pos - 1]
            right = self._parse_multiplicative()
            left = BinaryOp(left, op_tok.value, right, line=left.line, column=left.column)
        return left

    def _parse_multiplicative(self) -> ASTNode:
        left = self._parse_unary()
        while self._match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op_tok = self.tokens[self.pos - 1]
            right = self._parse_unary()
            left = BinaryOp(left, op_tok.value, right, line=left.line, column=left.column)
        return left

    def _parse_unary(self) -> ASTNode:
        # Prefix operators: -, !, ++, --
        if self._match(TokenType.MINUS, TokenType.LOGICAL_NOT, TokenType.INCREMENT, TokenType.DECREMENT):
            op_tok = self.tokens[self.pos - 1]
            operand = self._parse_unary()
            return UnaryOp(op=op_tok.value, operand=operand, is_prefix=True, line=op_tok.line, column=op_tok.column)
        return self._parse_primary()

    def _parse_primary(self) -> ASTNode:
        tok = self._current()

        # Integer literal
        if self._match(TokenType.INT_LITERAL):
            return IntLiteral(value=tok.value, line=tok.line, column=tok.column)

        # Identifier or Array Access
        if self._match(TokenType.IDENTIFIER):
            ident_name = tok.value
            if self._match(TokenType.LBRACKET):
                idx_expr = self._parse_expression()
                self._expect(TokenType.RBRACKET, "Expected ']' after array index expression")
                return ArrayAccess(array_name=ident_name, index=idx_expr, line=tok.line, column=tok.column)
            return Identifier(name=ident_name, line=tok.line, column=tok.column)

        # Parenthesized expression: ( expr )
        if self._match(TokenType.LPAREN):
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN, "Expected ')' to close parenthesized expression")
            return expr

        raise ParserError(f"Unexpected token '{tok.value}' in expression", tok.line, tok.column)
