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
    from .compiler.simulation_runner import SimulationRunner
except (ImportError, ValueError):
    from compiler.compiler import Compiler
    from compiler.simulation_runner import SimulationRunner


app = FastAPI(
    title="Compiler for Processing in Memory",
    description="Compiler Front End for C Subset with CPU and PIM Simulators",
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
simulation_runner_instance = SimulationRunner()


# --- Request Models ---

class CompileRequest(BaseModel):
    source_code: str


class SimulateRequest(BaseModel):
    source_code: Optional[str] = None
    ir_instructions: Optional[List[Dict[str, Any]]] = None
    mapped_instructions: Optional[List[Dict[str, Any]]] = None


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
    Source -> Lexer -> Parser -> AST -> Semantic Analyzer -> IR -> PIM Mapping -> Simulation
    """
    result = compiler_instance.compile(req.source_code)
    return result


@app.post("/api/simulate")
def simulate_code(req: SimulateRequest):
    """
    Runs dual CPU and PIM simulations with correctness comparison.
    Accepts either raw source_code or pre-generated ir_instructions + mapped_instructions.
    """
    if req.source_code:
        comp_res = compiler_instance.compile(req.source_code)
        if not comp_res.get("success"):
            raise HTTPException(status_code=400, detail=comp_res.get("error", "Compilation failed"))
        return comp_res.get("simulation")

    if req.ir_instructions is not None and req.mapped_instructions is not None:
        return simulation_runner_instance.run(req.ir_instructions, req.mapped_instructions)

    raise HTTPException(status_code=400, detail="Must provide either source_code or ir_instructions and mapped_instructions")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
