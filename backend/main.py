"""
FastAPI Server for Compiler for Processing in Memory.
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
    title="Compiler for Processing in Memory",
    description="Compiler Front End for C Subset",
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
        "id": "sample_1",
        "name": "Sample 1",
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
        "id": "sample_2",
        "name": "Sample 2",
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
        "id": "sample_syntax_err",
        "name": "Syntax Error Test",
        "source_code": """int a = 10
int b = 20;
int c = a + b;"""
    },
    {
        "id": "sample_semantic_err",
        "name": "Semantic Error Test",
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
        "service": "Compiler Service",
        "version": "1.0.0"
    }


@app.get("/api/examples")
def get_examples():
    """Returns catalog of example C programs."""
    return EXAMPLES


@app.post("/api/compile")
def compile_code(req: CompileRequest):
    """
    Runs compilation pipeline:
    Source -> Lexer -> Parser -> AST -> Semantic Analyzer -> IR -> PIM Mapping
    """
    result = compiler_instance.compile(req.source_code)
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
