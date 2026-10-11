"""
FastAPI Server for Phase 1: C Compiler Front End.
Provides compilation, examples, and health check endpoints.
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure backend directory and parent are on sys.path
_current_dir = Path(__file__).resolve().parent
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))
if str(_current_dir.parent) not in sys.path:
    sys.path.insert(0, str(_current_dir.parent))

try:
    from .compiler.compiler import Compiler
except (ImportError, ValueError):
    from compiler.compiler import Compiler


app = FastAPI(
    title="C Compiler Front End (Phase 1)",
    description="Lexical, Syntax, and Semantic Analyzer for C Subset",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

compiler_instance = Compiler()


# --- Request Models ---

class CompileRequest(BaseModel):
    source_code: str


# --- Example Programs ---

EXAMPLES = [
    {
        "id": "array_summation_main",
        "name": "1. Valid Array Summation (Demo Program)",
        "category": "valid",
        "description": "The required college review demonstration program with int main(), array declaration, and loop accumulation.",
        "source_code": """int main() {
    int arr[4] = {10, 20, 30, 40};
    int sum = 0;

    for (int i = 0; i < 4; i++) {
        sum = sum + arr[i];
    }

    return 0;
}"""
    },
    {
        "id": "simple_arithmetic",
        "name": "2. Valid Simple Arithmetic & Control Flow",
        "category": "valid",
        "description": "Standard arithmetic expressions, parenthesization, conditionals, and built-in print.",
        "source_code": """int x = 15;
int y = 25;
int total = (x + y) * 2;

if (total > 50) {
    total = total - 10;
} else {
    total = total + 10;
}

print(total);"""
    },
    {
        "id": "syntax_error_missing_semicolon",
        "name": "3. Invalid Syntax (Missing Semicolon)",
        "category": "invalid_syntax",
        "description": "Demonstrates parser syntax diagnostic when a semicolon is omitted after variable declaration.",
        "source_code": """int a = 10
int b = 20;
int c = a + b;"""
    },
    {
        "id": "semantic_error_undeclared",
        "name": "4. Invalid Semantic (Undeclared Variable)",
        "category": "invalid_semantic",
        "description": "Demonstrates semantic analyzer error detection when assigning to an undeclared identifier 'total'.",
        "source_code": """int x = 10;
int y = 20;
total = x + y;"""
    }
]


# --- Endpoints ---

@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "phase": "Phase 1: C Compiler Front End",
        "version": "1.0.0"
    }


@app.get("/api/examples")
def get_examples():
    """Returns catalog of example C programs."""
    return EXAMPLES


@app.post("/api/compile")
def compile_code(req: CompileRequest):
    """
    Runs Phase 1 Compiler Front End pipeline:
    Source -> Lexer -> Parser -> AST -> Semantic Analyzer
    """
    result = compiler_instance.compile(req.source_code)
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
