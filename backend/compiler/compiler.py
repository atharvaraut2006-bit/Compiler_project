"""
Compiler Orchestration Module for Phase 1.
Executes Lexer -> Parser -> AST Generation -> Semantic Analysis in strict sequence
and returns a structured compilation result.
"""
from typing import Dict, Any, List, Optional
from .lexer import Lexer, LexerError
from .parser import Parser, ParserError
from .semantic import SemanticAnalyzer, SemanticError


class Compiler:
    """
    Main compiler orchestrator for the C front end.
    """
    SUPPORTED_SUBSET = {
        "types": ["int", "int arrays"],
        "operators": ["+", "-", "*", "/", "%", "=", "+=", "-=", "*=", "/=", "<", "<=", ">", ">=", "==", "!=", "&&", "||", "!", "++", "--"],
        "control_flow": ["for loops", "while loops", "if/else conditions", "return"],
        "program_structure": ["int main() { ... } function definitions", "global/top-level statements", "blocks { ... }"],
        "builtins": ["print(expr);"]
    }

    def compile(self, source_code: str) -> Dict[str, Any]:
        """
        Orchestrates full Phase 1 compilation.
        """
        if not source_code or not source_code.strip():
            return {
                "success": False,
                "error": "Source code cannot be empty.",
                "stages": {
                    "lexical": {"status": "error", "message": "Source code is empty."},
                    "syntax": {"status": "skipped", "message": "Skipped due to empty input."},
                    "semantic": {"status": "skipped", "message": "Skipped due to empty input."}
                },
                "tokens": [],
                "ast": None,
                "symbol_table": {},
                "diagnostics": [{"severity": "error", "message": "Source code cannot be empty.", "line": 1, "column": 1}],
                "supported_language": self.SUPPORTED_SUBSET
            }

        # Stage 1: Lexical Analysis
        try:
            lexer = Lexer(source_code)
            tokens = lexer.tokenize()
            token_dicts = [t.to_dict() for t in tokens]
            stage_lexical = {
                "status": "success",
                "message": f"{len(tokens)} tokens generated.",
                "token_count": len(tokens)
            }
        except LexerError as e:
            return {
                "success": False,
                "error": str(e),
                "stages": {
                    "lexical": {"status": "error", "message": str(e)},
                    "syntax": {"status": "skipped", "message": "Skipped due to lexical error."},
                    "semantic": {"status": "skipped", "message": "Skipped due to lexical error."}
                },
                "tokens": [],
                "ast": None,
                "symbol_table": {},
                "diagnostics": [{"severity": "error", "message": e.message, "line": e.line, "column": e.column}],
                "supported_language": self.SUPPORTED_SUBSET
            }

        # Stage 2: Syntax Analysis & AST Construction
        try:
            parser = Parser(tokens)
            ast = parser.parse()
            ast_dict = ast.to_dict()
            stage_syntax = {
                "status": "success",
                "message": "Abstract Syntax Tree (AST) constructed successfully."
            }
        except ParserError as e:
            return {
                "success": False,
                "error": str(e),
                "stages": {
                    "lexical": stage_lexical,
                    "syntax": {"status": "error", "message": str(e)},
                    "semantic": {"status": "skipped", "message": "Skipped due to syntax error."}
                },
                "tokens": token_dicts,
                "ast": None,
                "symbol_table": {},
                "diagnostics": [{"severity": "error", "message": e.message, "line": e.line, "column": e.column}],
                "supported_language": self.SUPPORTED_SUBSET
            }

        # Stage 3: Semantic Analysis
        analyzer = SemanticAnalyzer()
        semantic_res = analyzer.analyze(ast)

        if not semantic_res["success"]:
            first_err = next((d["message"] for d in semantic_res["diagnostics"] if d["severity"] == "error"), "Semantic validation failed")
            return {
                "success": False,
                "error": first_err,
                "stages": {
                    "lexical": stage_lexical,
                    "syntax": stage_syntax,
                    "semantic": {"status": "error", "message": first_err}
                },
                "tokens": token_dicts,
                "ast": ast_dict,
                "symbol_table": semantic_res["symbols"],
                "diagnostics": semantic_res["diagnostics"],
                "supported_language": self.SUPPORTED_SUBSET
            }

        # All stages succeeded!
        return {
            "success": True,
            "error": None,
            "stages": {
                "lexical": stage_lexical,
                "syntax": stage_syntax,
                "semantic": {
                    "status": "success",
                    "message": f"Verified {len(semantic_res['symbols'])} symbols with 0 semantic errors."
                }
            },
            "tokens": token_dicts,
            "ast": ast_dict,
            "symbol_table": semantic_res["symbols"],
            "diagnostics": semantic_res["diagnostics"],
            "supported_language": self.SUPPORTED_SUBSET
        }
