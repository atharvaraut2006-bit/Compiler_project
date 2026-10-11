# Compiler for Processing in Memory (PIM): Design and Simulation
## Phase 1: C Compiler Front End

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19.0-61dafb.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.0-purple.svg)](https://vitejs.dev/)
[![Tests](https://img.shields.io/badge/Tests-35%20Passed-brightgreen.svg)]()

> **Project Phase Scope**: This repository implements **Phase 1: C Compiler Front End**. It establishes a reliable foundation for lexical analysis, recursive descent parsing, Abstract Syntax Tree (AST) construction, semantic analysis with scoped symbol tables, and diagnostic reporting. Later phases (IR, PIM mapping, simulation, and performance modeling) will build directly upon this foundation.

---

## 1. Phase 1 Architecture Overview

The compiler front end operates in a strictly decoupled sequence:

```
[ C Source Code ]
       │
       ▼
 [ Lexer Module ] ──► Produces ordered Token stream with exact line & col coordinates
       │
       ▼
[ Parser Module ] ──► Builds structured Abstract Syntax Tree (AST) with precedence climbing
       │
       ▼
[ Semantic Analyzer ] ──► Scoped Symbol Table & Diagnostic Validation (Errors & Warnings)
       │
       ▼
[ Compilation Result ] ──► Structured JSON response consumable by FastAPI and React UI
```

---

## 2. Supported C Language Subset

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
  - Arithmetic operators: `+`, `-`, `*`, `/`, `%` (with constant division-by-zero detection)
  - Assignment operators: `=`, `+=`, `-=`, `*=`, `/=`
  - Increment / Decrement: `++`, `--`
  - Relational operators: `<`, `<=`, `>`, `>=`
  - Equality operators: `==`, `!=`
  - Logical operators: `&&`, `||`, `!`
- **Statements**:
  - Variable & array declarations
  - Assignments & compound assignments
  - `for` loops: `for (int i = 0; i < 4; i++) { ... }`
  - `while` loops: `while (cond) { ... }`
  - `if` and `else` conditionals
  - `return` statements: `return 0;`
  - Built-in `print` statements: `print(sum);`
  - Blocks: `{ ... }`
- **Functions**: Function definitions including `int main() { ... }`.
- **Comments**: Single-line (`// ...`) and multi-line (`/* ... */`).

### B. Explicitly Unsupported C Features
To maintain a strict, testable boundary, the following are unsupported:
- Pointers and reference operators (`*ptr`, `&var`)
- Dynamic memory allocation (`malloc`, `free`)
- Structures and unions (`struct`, `union`)
- Preprocessor macros and directives (`#include`, `#define`)
- Floating-point data types (`float`, `double`)
- Multi-dimensional arrays (`int matrix[2][2]`)
- Arbitrary C standard library calls.

---

## 3. Quick Start & Execution

### Prerequisites
- Python 3.10+ (Tested on Python 3.12)
- Node.js 18+ and npm (Tested on Node 24 / npm 11)

### 1. Start the FastAPI Backend
```bash
# In project root:
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Backend API URL**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Start the React Frontend Dashboard
```bash
# In frontend directory:
cd frontend
npm install
npm run dev
```
- **Web Dashboard URL**: [http://localhost:5173](http://localhost:5173)

---

## 4. Running Automated Tests

Run the complete 35-test automated test suite using pytest:
```bash
python -m pytest backend/tests -v
```

All 35 unit and integration tests pass in ~0.35s:
- `test_lexer.py` (8 tests): Token types, keywords, literals, operators, comments, line/col coordinates, invalid characters.
- `test_parser.py` (9 tests): Declarations, precedence climbing, array indexing, for/while loops, `int main()`, syntax error handling.
- `test_semantic.py` (7 tests): Undeclared variables, duplicate declarations, scalar indexing, array initializer overflow, static bounds.
- `test_compiler_orchestration.py` (5 tests): Section 11 demo program, empty input, stage error cascades.
- `test_api.py` (6 tests): Health, catalog examples, valid and invalid compilation requests.

---

## 5. College Review Demonstration Guide

### Demonstration 1: The Required Array Summation Program (Section 11)
1. Open [http://localhost:5173](http://localhost:5173).
2. Select **"1. Valid Array Summation (Demo Program)"** from the benchmark dropdown.
   ```c
   int main() {
       int arr[4] = {10, 20, 30, 40};
       int sum = 0;

       for (int i = 0; i < 4; i++) {
           sum = sum + arr[i];
       }

       return 0;
   }
   ```
3. Click **▶ Compile & Analyze**.
4. Show the review panel:
   - **Pipeline Stage Cards**: Show that Lexical, Syntax, and Semantic stages all succeeded.
   - **Tokens Tab**: Show the 48 identified tokens with line/column coordinates.
   - **AST Hierarchy Tab**: Expand the AST nodes to show `Program` $\rightarrow$ `FunctionDef: main` $\rightarrow$ `Block` $\rightarrow$ `ArrayDecl: arr` $\rightarrow$ `VarDecl: sum` $\rightarrow$ `ForLoop` $\rightarrow$ `ReturnStatement`.
   - **Semantic Tab**: Show the Scoped Symbol Table displaying `main` (function), `arr` (array, size 4), `sum` (scalar), and `i` (loop variable in scope 2).

### Demonstration 2: Syntax Error Handling (Missing Semicolon)
1. Select **"3. Invalid Syntax (Missing Semicolon Error)"**.
   ```c
   int a = 10
   int b = 20;
   ```
2. Click **Compile & Analyze**.
3. Point out that the Lexical stage passed, but the Syntax stage caught the error with exact line and column diagnostic: `Expected ';' after variable declaration (got 'int') at line 2, column 1`.

### Demonstration 3: Semantic Error Handling (Undeclared Variable)
1. Select **"4. Invalid Semantic (Undeclared Variable Error)"**.
   ```c
   int x = 10;
   int y = 20;
   total = x + y;
   ```
2. Click **Compile & Analyze**.
3. Point out that Lexical and Syntax stages passed, but Semantic validation identified: `Undeclared variable 'total' at line 3, column 1`.

---

## 6. Handover Record
As required, the persistent handover file [`change`](./change) is maintained in the project root. It tracks the complete 6-phase roadmap, completed Phase 1 specifications, and next steps for Phase 2.
