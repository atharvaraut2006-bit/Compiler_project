"""
Recursive Descent Parser for C Compiler Front End with Extended C Language Features.
Constructs an Abstract Syntax Tree (AST) supporting custom function definitions,
function calls, preprocessor integration, pointers, structs, floats, and strings.
"""
from typing import List, Optional, Any, Union, Dict, Tuple
from .lexer import Token, TokenType
from .ast_nodes import (
    ASTNode, Program, FunctionDef, VarDecl, ArrayDecl, Block,
    Assignment, CompoundAssignment, ForLoop, WhileLoop, IfStatement,
    ReturnStatement, PrintStatement, ExprStatement, BinaryOp, UnaryOp,
    ArrayAccess, Identifier, IntLiteral, FloatLiteral, StringLiteral,
    FunctionCall, MemberAccess, StructDef
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
    Handwritten recursive-descent parser for C with extended language features.
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

    def _is_type_token(self, tok: Optional[Token] = None) -> bool:
        if tok is None:
            tok = self._current()
        return tok.type in (
            TokenType.INT, TokenType.FLOAT, TokenType.DOUBLE, TokenType.VOID,
            TokenType.CHAR, TokenType.STRUCT, TokenType.UNION, TokenType.CONST_KW,
            TokenType.STATIC, TokenType.AUTO
        )

    def _parse_type_specifier(self) -> Tuple[str, int, int]:
        """
        Parses a type specifier like 'int', 'float', 'void', 'struct Point', or pointer types like 'int*'.
        Returns (type_str, start_line, start_col).
        """
        first = self._current()
        start_line = first.line
        start_col = first.column

        # Optional qualifiers (const, static, auto)
        while self._match(TokenType.CONST_KW, TokenType.STATIC, TokenType.AUTO):
            pass

        base_type = ""
        if self._match(TokenType.STRUCT, TokenType.UNION):
            tag = self.tokens[self.pos - 1].value
            name_tok = self._expect(TokenType.IDENTIFIER, "Expected struct/union tag name")
            base_type = f"{tag} {name_tok.value}"
        elif self._match(TokenType.INT, TokenType.FLOAT, TokenType.DOUBLE, TokenType.VOID, TokenType.CHAR):
            base_type = self.tokens[self.pos - 1].value
        else:
            tok = self._current()
            raise ParserError(f"Expected type specifier (got '{tok.value}')", tok.line, tok.column)

        # Handle pointer stars: int*, char**, etc.
        while self._match(TokenType.STAR):
            base_type += "*"

        return base_type, start_line, start_col

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
        # Check if struct or union definition: struct Name { ... };
        if (self._check(TokenType.STRUCT) or self._check(TokenType.UNION)) and \
           self._peek(1).type == TokenType.IDENTIFIER and self._peek(2).type == TokenType.LBRACE:
            return self._parse_struct_definition()

        # Check if function definition vs variable declaration
        if self._is_type_token():
            # Lookahead to distinguish function definition from variable/array declaration
            # Pattern for function: <type> [*] <ident> ( ... ) { ... }
            offset = 1
            if self._check(TokenType.STRUCT) or self._check(TokenType.UNION):
                offset += 1  # skip struct/union name
            while self._peek(offset).type == TokenType.STAR:
                offset += 1
            if self._peek(offset).type == TokenType.IDENTIFIER and self._peek(offset + 1).type == TokenType.LPAREN:
                return self._parse_function_definition()
            else:
                return self._parse_declaration_statement()

        # Otherwise, parse general statement
        return self._parse_statement()

    def _parse_struct_definition(self) -> StructDef:
        is_union = self._match(TokenType.UNION)
        if not is_union:
            self._expect(TokenType.STRUCT, "Expected 'struct'")
        name_tok = self._expect(TokenType.IDENTIFIER, "Expected struct name")
        self._expect(TokenType.LBRACE, "Expected '{' to start struct body")
        members: List[Dict[str, str]] = []
        while not self._check(TokenType.RBRACE) and not self._check(TokenType.EOF):
            m_type, _, _ = self._parse_type_specifier()
            m_name = self._expect(TokenType.IDENTIFIER, "Expected member name").value
            self._expect(TokenType.SEMICOLON, "Expected ';' after member declaration")
            members.append({"type": m_type, "name": m_name})
        self._expect(TokenType.RBRACE, "Expected '}' after struct body")
        self._expect(TokenType.SEMICOLON, "Expected ';' after struct definition")
        return StructDef(name=name_tok.value, members=members, is_union=is_union, line=name_tok.line, column=name_tok.column)

    def _parse_function_definition(self) -> FunctionDef:
        ret_type, start_line, start_col = self._parse_type_specifier()
        name_tok = self._expect(TokenType.IDENTIFIER, "Expected function name")
        self._expect(TokenType.LPAREN, "Expected '(' after function name")

        params: List[Dict[str, str]] = []
        if not self._check(TokenType.RPAREN):
            # Parse parameters: (int a, float b, int arr[])
            while True:
                # Handle 'void' parameter list: (void)
                if self._check(TokenType.VOID) and self._peek(1).type == TokenType.RPAREN:
                    self._advance()
                    break

                p_type, _, _ = self._parse_type_specifier()
                p_name_tok = self._expect(TokenType.IDENTIFIER, "Expected parameter name")
                p_name = p_name_tok.value

                # Optional array brackets: int arr[] or int arr[10]
                if self._match(TokenType.LBRACKET):
                    if self._check(TokenType.INT_LITERAL):
                        self._advance()
                    self._expect(TokenType.RBRACKET, "Expected ']' for array parameter")
                    p_type += "[]"

                params.append({"type": p_type, "name": p_name})
                if not self._match(TokenType.COMMA):
                    break

        self._expect(TokenType.RPAREN, "Expected ')' after parameter list")
        self._expect(TokenType.LBRACE, "Expected '{' to start function body")
        body = self._parse_block_body(start_line, start_col)
        return FunctionDef(
            return_type=ret_type,
            name=name_tok.value,
            params=params,
            body=body,
            line=start_line,
            column=start_col
        )

    # -------------------------------------------------------------
    # Statements
    # -------------------------------------------------------------
    def _parse_statement(self) -> ASTNode:
        tok = self._current()

        # Variable or array declaration: int, float, void*, struct ...
        if self._is_type_token():
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

        # Assignment, increment, function call, or expression statement
        return self._parse_expr_or_assignment_statement()

    def _parse_declaration_statement(self) -> ASTNode:
        type_name, start_line, start_col = self._parse_type_specifier()

        # Pointer star attached to identifier: int *ptr;
        is_ptr = False
        while self._match(TokenType.STAR):
            is_ptr = True
            type_name += "*"

        name_tok = self._expect(TokenType.IDENTIFIER, "Expected identifier in declaration")

        # Array declaration: int arr[N] = { ... }; or 2D array: int m[R][C];
        if self._match(TokenType.LBRACKET):
            size_tok = self._expect(TokenType.INT_LITERAL, "Expected integer literal for array size")
            self._expect(TokenType.RBRACKET, "Expected ']' after array size")

            # Check for second dimension (2D array): int m[2][2]
            dim2 = None
            if self._match(TokenType.LBRACKET):
                dim2_tok = self._expect(TokenType.INT_LITERAL, "Expected integer literal for second array dimension")
                self._expect(TokenType.RBRACKET, "Expected ']' after second array size")
                dim2 = dim2_tok.value
                total_size = size_tok.value * dim2
            else:
                total_size = size_tok.value

            initializers: List[ASTNode] = []
            if self._match(TokenType.ASSIGN):
                self._expect(TokenType.LBRACE, "Expected '{' for array initializer list")
                if not self._check(TokenType.RBRACE):
                    while True:
                        # Nested brace for 2D array initializer: {{1, 2}, {3, 4}}
                        if self._match(TokenType.LBRACE):
                            while True:
                                initializers.append(self._parse_expression())
                                if not self._match(TokenType.COMMA):
                                    break
                            self._expect(TokenType.RBRACE, "Expected '}' for nested array initializer")
                        else:
                            initializers.append(self._parse_expression())
                        if not self._match(TokenType.COMMA):
                            break
                self._expect(TokenType.RBRACE, "Expected '}' after array initializer list")

            self._expect(TokenType.SEMICOLON, "Expected ';' after array declaration")
            return ArrayDecl(
                type_name=type_name,
                name=name_tok.value,
                size=total_size,
                initializers=initializers,
                line=start_line,
                column=start_col
            )

        # Scalar or pointer variable declaration: int x = 10; or float pi = 3.14; or int *p = &x;
        initializer = None
        if self._match(TokenType.ASSIGN):
            initializer = self._parse_expression()

        self._expect(TokenType.SEMICOLON, "Expected ';' after variable declaration")
        return VarDecl(
            type_name=type_name,
            name=name_tok.value,
            initializer=initializer,
            line=start_line,
            column=start_col
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
            if self._is_type_token():
                t_name, s_line, s_col = self._parse_type_specifier()
                name_tok = self._expect(TokenType.IDENTIFIER, "Expected loop variable identifier")
                init_val = None
                if self._match(TokenType.ASSIGN):
                    init_val = self._parse_expression()
                init = VarDecl(t_name, name_tok.value, init_val, line=s_line, column=s_col)
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
        left = self._parse_bitwise_or()
        while self._match(TokenType.LOGICAL_AND):
            op_tok = self.tokens[self.pos - 1]
            right = self._parse_bitwise_or()
            left = BinaryOp(left, op_tok.value, right, line=left.line, column=left.column)
        return left

    def _parse_bitwise_or(self) -> ASTNode:
        left = self._parse_bitwise_xor()
        while self._match(TokenType.PIPE):
            op_tok = self.tokens[self.pos - 1]
            right = self._parse_bitwise_xor()
            left = BinaryOp(left, op_tok.value, right, line=left.line, column=left.column)
        return left

    def _parse_bitwise_xor(self) -> ASTNode:
        left = self._parse_bitwise_and()
        while self._match(TokenType.CARET):
            op_tok = self.tokens[self.pos - 1]
            right = self._parse_bitwise_and()
            left = BinaryOp(left, op_tok.value, right, line=left.line, column=left.column)
        return left

    def _parse_bitwise_and(self) -> ASTNode:
        left = self._parse_equality()
        while self._match(TokenType.AMPERSAND):
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
        # Prefix operators: -, !, ++, --, &, *, ~, sizeof
        if self._match(TokenType.MINUS, TokenType.LOGICAL_NOT, TokenType.INCREMENT, TokenType.DECREMENT,
                       TokenType.AMPERSAND, TokenType.STAR, TokenType.TILDE):
            op_tok = self.tokens[self.pos - 1]
            operand = self._parse_unary()
            return UnaryOp(op=op_tok.value, operand=operand, is_prefix=True, line=op_tok.line, column=op_tok.column)

        if self._match(TokenType.SIZEOF):
            s_tok = self.tokens[self.pos - 1]
            self._expect(TokenType.LPAREN, "Expected '(' after sizeof")
            if self._is_type_token():
                self._parse_type_specifier()
            else:
                self._parse_expression()
            self._expect(TokenType.RPAREN, "Expected ')' after sizeof argument")
            return IntLiteral(value=4, line=s_tok.line, column=s_tok.column)

        return self._parse_primary()

    def _parse_primary(self) -> ASTNode:
        tok = self._current()

        # Integer literal
        if self._match(TokenType.INT_LITERAL):
            return IntLiteral(value=tok.value, line=tok.line, column=tok.column)

        # Float literal
        if self._match(TokenType.FLOAT_LITERAL):
            return FloatLiteral(value=tok.value, line=tok.line, column=tok.column)

        # String literal
        if self._match(TokenType.STRING_LITERAL):
            return StringLiteral(value=tok.value, line=tok.line, column=tok.column)

        # Character literal
        if self._match(TokenType.CHAR_LITERAL):
            val = ord(tok.value[0]) if tok.value else 0
            return IntLiteral(value=val, line=tok.line, column=tok.column)

        # Identifier, Function Call, or Array Access
        if self._match(TokenType.IDENTIFIER):
            ident_name = tok.value

            # Function Call: printf(...), add(x, y), malloc(100)
            if self._match(TokenType.LPAREN):
                args: List[ASTNode] = []
                if not self._check(TokenType.RPAREN):
                    while True:
                        args.append(self._parse_expression())
                        if not self._match(TokenType.COMMA):
                            break
                self._expect(TokenType.RPAREN, "Expected ')' after function arguments")
                primary_node: ASTNode = FunctionCall(func_name=ident_name, args=args, line=tok.line, column=tok.column)

            # Array Access: arr[i] or 2D arr[i][j]
            elif self._match(TokenType.LBRACKET):
                idx_expr = self._parse_expression()
                self._expect(TokenType.RBRACKET, "Expected ']' after array index expression")
                primary_node = ArrayAccess(array_name=ident_name, index=idx_expr, line=tok.line, column=tok.column)

                # Check for 2D array access: m[i][j]
                if self._match(TokenType.LBRACKET):
                    idx2_expr = self._parse_expression()
                    self._expect(TokenType.RBRACKET, "Expected ']' after second array index expression")
                    primary_node = ArrayAccess(array_name=f"{ident_name}_2d", index=idx2_expr, line=tok.line, column=tok.column)

            else:
                primary_node = Identifier(name=ident_name, line=tok.line, column=tok.column)

            # Handle postfix operators: .member, ->member
            while self._check(TokenType.DOT) or self._check(TokenType.ARROW):
                if self._match(TokenType.DOT):
                    m_tok = self._expect(TokenType.IDENTIFIER, "Expected member name after '.'")
                    primary_node = MemberAccess(object_=primary_node, member=m_tok.value, is_arrow=False, line=m_tok.line, column=m_tok.column)
                elif self._match(TokenType.ARROW):
                    m_tok = self._expect(TokenType.IDENTIFIER, "Expected member name after '->'")
                    primary_node = MemberAccess(object_=primary_node, member=m_tok.value, is_arrow=True, line=m_tok.line, column=m_tok.column)

            return primary_node

        # Parenthesized expression: ( expr )
        if self._match(TokenType.LPAREN):
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN, "Expected ')' to close parenthesized expression")
            return expr

        raise ParserError(f"Unexpected token '{tok.value}' in expression", tok.line, tok.column)
