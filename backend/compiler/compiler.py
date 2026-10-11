"""
Compiler Orchestration Module.
Executes Lexer -> Parser -> AST Generation -> Semantic Analysis ->
IR Generation -> PIM Instruction Mapping in strict sequence
and returns structured compilation results.
"""
from typing import Dict, Any, List, Optional
from .lexer import Lexer, LexerError
from .parser import Parser, ParserError
from .semantic import SemanticAnalyzer, SemanticError
from .ir_generator import IRGenerator
from .pim_mapper import PIMMapper


class Compiler:
    """
    Main compiler orchestrator for the C front end, IR generator, and PIM instruction mapper.
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
        Orchestrates full compilation pipeline.
        """
        empty_ir = {"instructions": [], "formatted": "", "instruction_count": 0}
        empty_mapping = {"instructions": [], "pim_count": 0, "cpu_count": 0, "unsupported_count": 0, "total_instructions": 0, "summary": {"total": 0, "pim_allocated": 0, "cpu_fallback": 0}}

        if not source_code or not source_code.strip():
            return {
                "success": False,
                "error": "Source code cannot be empty.",
                "stages": {
                    "lexical": {"status": "error", "message": "Source code is empty."},
                    "syntax": {"status": "skipped", "message": "Skipped due to empty input."},
                    "semantic": {"status": "skipped", "message": "Skipped due to empty input."},
                    "ir": {"status": "skipped", "message": "Skipped due to empty input."},
                    "pim_mapping": {"status": "skipped", "message": "Skipped due to empty input."}
                },
                "tokens": [],
                "ast": None,
                "symbol_table": {},
                "diagnostics": [{"severity": "error", "message": "Source code cannot be empty.", "line": 1, "column": 1}],
                "ir": empty_ir,
                "mapping": empty_mapping,
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
                    "semantic": {"status": "skipped", "message": "Skipped due to lexical error."},
                    "ir": {"status": "skipped", "message": "Skipped due to lexical error."},
                    "pim_mapping": {"status": "skipped", "message": "Skipped due to lexical error."}
                },
                "tokens": [],
                "ast": None,
                "symbol_table": {},
                "diagnostics": [{"severity": "error", "message": e.message, "line": e.line, "column": e.column}],
                "ir": empty_ir,
                "mapping": empty_mapping,
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
                    "semantic": {"status": "skipped", "message": "Skipped due to syntax error."},
                    "ir": {"status": "skipped", "message": "Skipped due to syntax error."},
                    "pim_mapping": {"status": "skipped", "message": "Skipped due to syntax error."}
                },
                "tokens": token_dicts,
                "ast": None,
                "symbol_table": {},
                "diagnostics": [{"severity": "error", "message": e.message, "line": e.line, "column": e.column}],
                "ir": empty_ir,
                "mapping": empty_mapping,
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
                    "semantic": {"status": "error", "message": first_err},
                    "ir": {"status": "skipped", "message": "Skipped due to semantic error."},
                    "pim_mapping": {"status": "skipped", "message": "Skipped due to semantic error."}
                },
                "tokens": token_dicts,
                "ast": ast_dict,
                "symbol_table": semantic_res["symbols"],
                "diagnostics": semantic_res["diagnostics"],
                "ir": empty_ir,
                "mapping": empty_mapping,
                "supported_language": self.SUPPORTED_SUBSET
            }

        stage_semantic = {
            "status": "success",
            "message": f"Verified {len(semantic_res['symbols'])} symbols with 0 semantic errors."
        }

        # Stage 4: Intermediate Representation (IR) Generation
        try:
            ir_gen = IRGenerator()
            ir_res = ir_gen.generate(ast)
            stage_ir = {
                "status": "success",
                "message": f"Generated {ir_res['instruction_count']} 3AC instructions."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"IR Generation failed: {str(e)}",
                "stages": {
                    "lexical": stage_lexical,
                    "syntax": stage_syntax,
                    "semantic": stage_semantic,
                    "ir": {"status": "error", "message": str(e)},
                    "pim_mapping": {"status": "skipped", "message": "Skipped due to IR failure."}
                },
                "tokens": token_dicts,
                "ast": ast_dict,
                "symbol_table": semantic_res["symbols"],
                "diagnostics": semantic_res["diagnostics"] + [{"severity": "error", "message": f"IR Generation failed: {str(e)}", "line": 1, "column": 1}],
                "ir": empty_ir,
                "mapping": empty_mapping,
                "supported_language": self.SUPPORTED_SUBSET
            }

        # Stage 5: PIM Eligibility Analysis & Instruction Mapping
        try:
            pim_mapper = PIMMapper()
            mapping_res = pim_mapper.map_instructions(ir_res["instructions"], ast=ast)
            stage_pim = {
                "status": "success",
                "message": f"Mapped {mapping_res['pim_count']} PIM / {mapping_res['cpu_count']} CPU instructions. Optimal strategy: {mapping_res.get('optimization', {}).get('selected_strategy', 'N/A')}."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"PIM Mapping failed: {str(e)}",
                "stages": {
                    "lexical": stage_lexical,
                    "syntax": stage_syntax,
                    "semantic": stage_semantic,
                    "ir": stage_ir,
                    "pim_mapping": {"status": "error", "message": str(e)}
                },
                "tokens": token_dicts,
                "ast": ast_dict,
                "symbol_table": semantic_res["symbols"],
                "diagnostics": semantic_res["diagnostics"] + [{"severity": "error", "message": f"PIM Mapping failed: {str(e)}", "line": 1, "column": 1}],
                "ir": ir_res,
                "mapping": empty_mapping,
                "optimization": {},
                "supported_language": self.SUPPORTED_SUBSET
            }

        # Complete Pipeline Succeeded!
        return {
            "success": True,
            "error": None,
            "stages": {
                "lexical": stage_lexical,
                "syntax": stage_syntax,
                "semantic": stage_semantic,
                "ir": stage_ir,
                "pim_mapping": stage_pim
            },
            "tokens": token_dicts,
            "ast": ast_dict,
            "symbol_table": semantic_res["symbols"],
            "diagnostics": semantic_res["diagnostics"],
            "ir": ir_res,
            "mapping": mapping_res,
            "optimization": mapping_res.get("optimization", {}),
            "supported_language": self.SUPPORTED_SUBSET
        }
