# Compiler for Processing in Memory (PIM): Design and Simulation

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19.0-61dafb.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.0-purple.svg)](https://vitejs.dev/)
[![Tests](https://img.shields.io/badge/Tests-58%20Passed-brightgreen.svg)]()

An educational compiler and simulation platform that accepts C source programs, transforms them into an intermediate representation (IR), identifies operations eligible for in-memory acceleration (Processing in Memory), evaluates research-informed analytical cost models, maps them to simulated PIM instructions, and prepares execution traces for cycle-accurate CPU and PIM simulation.

---

## 1. Compiler Pipeline Architecture

The compilation engine executes in a sequential 5-stage pipeline:

```
[ C Source Code ]
       │
       ▼
 [ Lexer Module ] ──► Token sequence with line & column coordinates
       │
       ▼
[ Parser Module ] ──► Structured Abstract Syntax Tree (AST) with precedence climbing
       │
       ▼
[ Semantic Analyzer ] ──► Scoped Symbol Table & Diagnostic Validation
       │
       ▼
 [ IR Generator ] ──► Three-Address-Code (3AC) Intermediate Representation
       │
       ▼
 [ PIM Mapper & Cost Model ] ──► Static Workload Analysis & 4-Term Cost-Aware Offload Optimization
       │
       ▼
[ Structured Results ] ──► Consumable by FastAPI backend and React developer dashboard
```

---

## 2. Research-Informed Cost-Aware Optimization (NMC-Opt Inspired)

Rather than blindly mapping every supported instruction to in-memory hardware, the compiler implements an analytical, research-informed cost model inspired by Near-Memory Computing optimization literature (NMC-Opt).

### A. Four-Term Analytical Cost Model
For each candidate execution strategy, the compiler computes:
$$\text{total\_cost} = \text{compute\_cost} + \text{transfer\_cost} + \text{layout\_cost} + \text{synchronization\_cost}$$

- **Compute Cost ($C_{\text{comp}}$)**: Operational latency based on core speed assumptions (`CPU: 1.0 cyc/op`, `PIM: 1.2 cyc/op`).
- **Transfer Cost ($C_{\text{xfer}}$)**: Time spent moving data across the off-chip memory bus (`2.0 B/cyc`) vs high-speed internal TSV/bank row buffers (`32.0 B/cyc`).
- **Layout Cost ($C_{\text{layout}}$)**: Reorganization penalty for strided or non-contiguous data layouts (`0.25 cyc/B`).
- **Synchronization Cost ($C_{\text{sync}}$)**: Host CPU kernel launch, command register setup, and barrier synchronization overhead (`60.0 cyc`).

### B. Candidate Execution Strategies
1. **`CPU_ONLY`**: Host CPU executes the workload; all array lines traverse the memory bus.
2. **`DIRECT_PIM`**: Operations execute in-situ in DRAM row buffers; only small scalar inputs traverse the bus.
3. **`TRANSFORMED_PIM`**: Layout-aware PIM offload accounting for in-memory data restructuring.

### C. Cost-Aware Decision Logic
- **Small Workloads** (e.g. scalar addition or small arrays): PIM launch synchronization overhead (60 cycles) exceeds compute savings. The cost model intelligently assigns execution to the **Host CPU**.
- **Large Memory-Bound Workloads** (e.g. 100-element array accumulation): Eliminating hundreds of bytes of memory bus traffic far outweighs the launch overhead, yielding an analytical speedup (> 1.3×) and selecting **In-Memory PIM Offload**.

---

## 3. Centralized PIM Instruction Eligibility Policy

The project defines an explicit, centralized architectural policy for mapping intermediate operations to simulated Processing in Memory (PIM) units versus host CPU fallback.

> **Note**: These are project simulation rules designed for educational simulation and performance comparison, not claims about all real-world PIM hardware implementations.

### A. PIM-Eligible Operations
The simulated in-memory architecture embeds arithmetic/logic units and comparators directly adjacent to memory array banks:
- **Addition (`PIM_ADD`)**: Native in-memory integer addition (`ADD`).
- **Subtraction (`PIM_SUB`)**: Native in-memory integer subtraction (`SUB`).
- **Multiplication (`PIM_MUL`)**: Integer multiplication (`MUL`) in memory units.
- **Comparisons (`PIM_COMPARE`)**: Relational and equality comparisons (`<`, `<=`, `>`, `>=`, `==`, `!=`).
- **Memory Loads (`PIM_LOAD`)**: In-situ row buffer reads for array elements (`LOAD_INDEXED`).
- **Memory Stores (`PIM_STORE`)**: In-situ bank partition writes for array elements (`STORE_INDEXED`).

### B. CPU-Fallback Operations
Operations routed to host CPU execution due to hardware or control-flow constraints:
- **Division (`CPU_DIV`)**: Multi-cycle iterative divider hardware is omitted from low-power PIM banks.
- **Modulo (`CPU_MOD`)**: Modulo relies on division circuitry; routed to host CPU fallback.
- **Control Flow (`CPU_BRANCH`, `CPU_JUMP`, `LABEL`)**: Program counter sequencing, jump targets, and branch condition dispatching are managed by the host CPU control unit.
- **Function Returns (`CPU_RETURN`)**: Stack unwinding and calling conventions managed by host CPU.
- **Declarations (`DECLARE`) & Immediates (`CPU_CONST`)**: Handled by host runtime environment.
- **Scalar Memory Access (`CPU_LOAD`, `CPU_STORE`)**: Variables residing in the host CPU stack frame.
- **Standard Output (`CPU_PRINT`)**: Host operating system I/O system calls.
- **Any Unrecognized Operation**: Safely defaults to CPU fallback.

### C. Explicit Memory-Access Eligibility Rules
- **Array-Indexed Operations (`LOAD_INDEXED`, `STORE_INDEXED`)**: Allocated directly to DRAM bank row buffers; executed in-situ without traversing the external memory bus.
- **Scalar Variables (`LOAD`, `STORE`)**: Allocated on the host CPU stack frame; dispatched by the CPU memory controller over the bus.

### D. Mixed CPU/PIM Execution in Loops
For loops and iterative workloads:
1. The **Host CPU** controls loop iteration, counter incrementation, and termination checks (`COMPARE_LT`, `BRANCH`, `JUMP`).
2. Inside the loop body, compute-intensive array operations and vector arithmetic (`PIM_LOAD`, `PIM_ADD`, `PIM_STORE`) execute **in-situ inside the memory banks**.
3. This models real-world heterogeneous architectures where the host CPU offloads memory-bound kernels to PIM.

---

## 4. Supported C Language Subset

### A. Supported Constructs
- **Data Types**: `int` (32-bit signed scalar and 1D fixed-size integer arrays).
- **Declarations**: 
  - Scalar variables: `int x = 10;`, `int y;`
  - Fixed-size arrays: `int arr[4] = {10, 20, 30, 40};`, `int buffer[16];`
- **Expressions**:
  - Integer constants: `0`, `42`, `1000`
  - Identifiers: `[a-zA-Z_][a-zA-Z0-9_]*`
  - Array element access: `arr[i]`, `values[0]`
  - Parenthesized grouping: `(a + b) * c`
  - Arithmetic operators: `+`, `-`, `*`, `/`, `%`
  - Assignment operators: `=`, `+=`, `-=`, `*=`, `/=`
  - Increment / Decrement: `++`, `--`
  - Relational & equality operators: `<`, `<=`, `>`, `>=`, `==`, `!=`
  - Logical operators: `&&`, `||`, `!`
- **Control Flow**: `for` loops, `while` loops, `if`/`else` conditionals, `return`, and `print`.
- **Functions**: `int main() { ... }` and top-level block structures.
- **Comments**: `// single-line` and `/* multi-line */`.

### B. Explicitly Unsupported Constructs
- Pointers and reference operators (`*ptr`, `&var`)
- Dynamic memory allocation (`malloc`, `free`)
- Structures and unions (`struct`, `union`)
- Preprocessor directives (`#include`, `#define`)
- Floating-point data types (`float`, `double`)
- Multi-dimensional arrays (`int matrix[2][2]`)
- Arbitrary standard library calls.

---

## 5. Running the Application Locally

### Prerequisites
- Python 3.10+ (Tested on Python 3.12)
- Node.js 18+ (Tested on Node 24 / npm 11)

### 1. Start the FastAPI Backend
```bash
# In project root:
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Backend API URL**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Start the React Frontend Dashboard
```bash
# In frontend directory:
cd frontend
npm install
npm run dev
```
- **Frontend Dashboard**: [http://localhost:5173](http://localhost:5173)

---

## 6. Automated Tests

Execute the automated test suite with pytest:
```bash
python -m pytest backend/tests -v
```

All 58 unit and integration tests pass in ~0.38s:
- `test_cost_model.py` (8 tests): Small workload CPU preference, large memory-bound PIM offload, unsupported operation fallback, 4-term formula mathematical integrity, strided pattern detection, layout transformation evaluation, explicit unknown handling, cost enforcement.
- `test_lexer.py` (8 tests): Token identification, line/col tracking, comment stripping, invalid character detection.
- `test_parser.py` (9 tests): Precedence climbing, array indexing, loop structures, syntax error diagnostics.
- `test_semantic.py` (7 tests): Scoped symbol table, undeclared variables, duplicate declarations, bounds checking.
- `test_ir_generator.py` (7 tests): 3AC opcode generation, operator precedence preservation, array loads/stores, loop control flow, deterministic temporary numbering.
- `test_pim_mapper.py` (8 tests): PIM arithmetic mapping, CPU division/modulo fallback, array-access memory rules, comparisons, mixed CPU/PIM execution, fallback defaults.
- `test_compiler_orchestration.py` (5 tests): End-to-end 5-stage pipeline execution, error cascade handling.
- `test_api.py` (6 tests): Endpoints `/api/health`, `/api/examples`, `/api/compile` schema validation.

---

## 7. Handover Record
The persistent handover file [`change`](./change) is maintained in the project root. It documents the complete roadmap, completed features, centralized policies, research-informed cost model formulas, test verification results, and preparation for CPU/PIM cycle simulation.
