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
    from .compiler.performance_evaluator import PerformanceEvaluator
except (ImportError, ValueError):
    from compiler.compiler import Compiler
    from compiler.performance_evaluator import PerformanceEvaluator


app = FastAPI(
    title="Compiler for Processing in Memory",
    description="Compiler Front End for C Subset with IR Generation, PIM Mapping, and Performance Analysis",
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
performance_evaluator_instance = PerformanceEvaluator()


# --- Request Models ---

class CompileRequest(BaseModel):
    source_code: str


class EvaluateRequest(BaseModel):
    source_code: Optional[str] = None
    custom_params: Optional[Dict[str, Any]] = None
    ir_instructions: Optional[List[Dict[str, Any]]] = None
    mapped_instructions: Optional[List[Dict[str, Any]]] = None


# --- Example Programs ---

EXAMPLES = [
    {
        "id": "sample_1",
        "name": "Sample 1: Array Summation",
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
        "id": "sample_add",
        "name": "Benchmark: Array Addition",
        "source_code": """int main() {
    int a[4] = {1, 2, 3, 4};
    int b[4] = {10, 20, 30, 40};
    int c[4] = {0, 0, 0, 0};

    for (int i = 0; i < 4; i++) {
        c[i] = a[i] + b[i];
    }

    return 0;
}"""
    },
    {
        "id": "sample_scale",
        "name": "Benchmark: Array Scaling",
        "source_code": """int main() {
    int weights[4] = {5, 10, 15, 20};
    int factor = 3;

    for (int i = 0; i < 4; i++) {
        weights[i] = weights[i] * factor;
    }

    return 0;
}"""
    },
    {
        "id": "sample_large",
        "name": "Benchmark: Large Array (32 Elements - PIM Speedup)",
        "source_code": """int main() {
    int data[32] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32};
    int total = 0;

    for (int i = 0; i < 32; i++) {
        total = total + data[i];
    }

    return 0;
}"""
    },
    {
        "id": "sample_fallback",
        "name": "Benchmark: CPU Fallback (Division)",
        "source_code": """int main() {
    int arr[4] = {100, 200, 300, 400};
    int result = 0;

    for (int i = 0; i < 4; i++) {
        int val = arr[i] / 10;
        result = result + val;
    }

    return 0;
}"""
    },
    {
        "id": "sample_2",
        "name": "Sample 2: Conditional Branching",
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
        "id": "sample_stdio_functions",
        "name": "Extended C: #include <stdio.h> & Functions",
        "source_code": """#include <stdio.h>
#define N 4

int compute_square(int x) {
    return x * x;
}

int main() {
    int arr[N] = {2, 4, 6, 8};
    int total = 0;

    for (int i = 0; i < N; i++) {
        total += compute_square(arr[i]);
    }

    printf("Sum of squares: %d\\n", total);
    return 0;
}"""
    },
    {
        "id": "sample_pointers_structs",
        "name": "Extended C: Pointers & Structs",
        "source_code": """#include <stdio.h>

struct Vector2D {
    int x;
    int y;
};

int main() {
    struct Vector2D v;
    v.x = 15;
    v.y = 25;

    int *px = &v.x;
    *px = 30;

    int arr[2] = {v.x, v.y};
    int magnitude_squared = arr[0] * arr[0] + arr[1] * arr[1];

    printf("Magnitude squared: %d\\n", magnitude_squared);
    return 0;
}"""
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


from fastapi.responses import FileResponse


@app.get("/api/cost-model-pdf")
def download_cost_model_pdf():
    """Serves the publication-quality cost model specification PDF."""
    pdf_path = _current_dir.parent / "Compiler_for_PIM_Cost_Model_Specification.pdf"
    if not pdf_path.exists():
        pdf_path = _current_dir.parent / "docs" / "Compiler_for_PIM_Cost_Model_Specification.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Specification PDF not found.")
    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        filename="Compiler_for_PIM_Cost_Model_Specification.pdf"
    )


@app.post("/api/compile")
def compile_code(req: CompileRequest):
    """
    Runs compilation pipeline:
    Source -> Lexer -> Parser -> AST -> Semantic Analyzer -> IR -> PIM Mapping & Cost Evaluation
    """
    result = compiler_instance.compile(req.source_code)
    return result


@app.post("/api/evaluate")
def evaluate_performance(req: EvaluateRequest):
    """
    Phase 4: Evaluates execution strategies (CPU_ONLY, DIRECT_PIM, TRANSFORMED_PIM),
    cost breakdowns, speedups, transfer savings, execution statistics,
    decision explanations, and interactive sensitivity analysis.
    """
    if req.source_code:
        comp_res = compiler_instance.compile(req.source_code)
        if not comp_res.get("success"):
            raise HTTPException(status_code=400, detail=comp_res.get("error", "Compilation failed"))

        if req.custom_params:
            return performance_evaluator_instance.evaluate(
                ir_instructions=comp_res["ir"]["instructions"],
                ast=comp_res.get("ast"),
                custom_params=req.custom_params
            )
        return comp_res.get("performance")

    if req.ir_instructions is not None:
        return performance_evaluator_instance.evaluate(
            ir_instructions=req.ir_instructions,
            custom_params=req.custom_params
        )

    raise HTTPException(status_code=400, detail="Must provide either source_code or ir_instructions")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
