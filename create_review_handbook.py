"""
Generates the Comprehensive Academic Project Review & Technical Reference Handbook
for "Compiler for Processing in Memory (PIM): Design, Intermediate Representation, and Execution Simulation".
Produces a publication-quality multi-page PDF document using ReportLab.
"""
import sys
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Canvas that computes total pages dynamically and adds running headers & footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running Header (Pages 2+)
        if self._pageNumber > 1:
            self.drawString(54, 755, "Compiler for Processing in Memory (PIM) — Capstone Review Handbook")
            self.setFont("Helvetica", 8)
            self.drawRightString(558, 755, "Architecture, IR & Phase 3 Simulation")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.75)
            self.line(54, 747, 558, 747)

        # Running Footer (All pages)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(54, 34, "Academic Project Review & Viva Reference — Department of Computer Science & Engineering")
        text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 34, text)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.75)
        self.line(54, 46, 558, 46)

        self.restoreState()


def build_pdf(filename="Compiler_PIM_Project_Review_Handbook.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    c_navy = colors.HexColor("#1e3a8a")
    c_blue = colors.HexColor("#2563eb")
    c_emerald = colors.HexColor("#059669")
    c_charcoal = colors.HexColor("#0f172a")
    c_body = colors.HexColor("#334155")
    c_border = colors.HexColor("#cbd5e1")
    c_bg_light = colors.HexColor("#f8fafc")
    c_bg_callout = colors.HexColor("#eff6ff")
    c_callout_border = colors.HexColor("#3b82f6")
    c_bg_warn = colors.HexColor("#fef3c7")
    c_warn_border = colors.HexColor("#f59e0b")

    # Typography Styles
    style_doc_title = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=c_navy,
        spaceAfter=4
    )

    style_doc_subtitle = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12
    )

    style_h1 = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=c_navy,
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True
    )

    style_h2 = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=c_blue,
        spaceBefore=9,
        spaceAfter=3,
        keepWithNext=True
    )

    style_h3 = ParagraphStyle(
        "SectionH3",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=c_charcoal,
        spaceBefore=5,
        spaceAfter=2,
        keepWithNext=True
    )

    style_body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.8,
        textColor=c_body,
        spaceAfter=5
    )

    style_bullet = ParagraphStyle(
        "Bullet",
        parent=style_body,
        leftIndent=12,
        bulletIndent=4,
        spaceAfter=3
    )

    style_code = ParagraphStyle(
        "CodeBlock",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor("#0f172a"),
        backColor=colors.HexColor("#f1f5f9"),
        borderColor=colors.HexColor("#e2e8f0"),
        borderWidth=0.5,
        borderPadding=5,
        spaceBefore=3,
        spaceAfter=5
    )

    style_callout = ParagraphStyle(
        "CalloutText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.2,
        leading=11.5,
        textColor=colors.HexColor("#1e40af")
    )

    style_th = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.8,
        leading=9.5,
        textColor=colors.white
    )

    style_td = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=c_charcoal
    )

    style_td_code = ParagraphStyle(
        "TableCellCode",
        parent=style_td,
        fontName="Courier",
        fontSize=7.2,
        leading=9.2
    )

    elements = []

    # -------------------------------------------------------------
    # COVER / HEADER BLOCK
    # -------------------------------------------------------------
    elements.append(Paragraph("Compiler for Processing in Memory (PIM)", style_doc_title))
    elements.append(Paragraph("Design, Intermediate Representation, and Execution Simulation<br/><b>Master Academic Review & Viva Technical Handbook</b>", style_doc_subtitle))

    meta_data = [
        [
            Paragraph("<b>Project Domain:</b> Computer Systems Architecture & Compilers", style_td),
            Paragraph("<b>Current Implementation:</b> Phase 1, Phase 2, & Phase 3 (100% Complete)", style_td)
        ],
        [
            Paragraph("<b>Target Architecture:</b> Heterogeneous CPU + Near-Memory PIM (Row-Buffer ALUs)", style_td),
            Paragraph("<b>Automated Test Suite:</b> 73 Backend Unit & Integration Tests Passing", style_td)
        ],
        [
            Paragraph("<b>Technology Stack:</b> Python (FastAPI, 3AC IR Engine), React 19, Vite, CodeMirror", style_td),
            Paragraph("<b>Primary Purpose:</b> Capstone Project Defense & Technical Review Committee", style_td)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[250, 254])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_bg_light),
        ('BOX', (0, 0), (-1, -1), 0.75, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 10))

    # -------------------------------------------------------------
    # SECTION 1: EXECUTIVE SUMMARY & ARCHITECTURAL MOTIVATION
    # -------------------------------------------------------------
    elements.append(Paragraph("1. Executive Summary & Architectural Motivation", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=c_navy, spaceBefore=2, spaceAfter=6))

    elements.append(Paragraph(
        "<b>The Von Neumann Memory Wall Bottleneck:</b> In classical von Neumann architecture, computational logic (CPU/ALU) is physically segregated from memory storage (DRAM) by an external printed circuit board (PCB) bus. While microprocessor computation speeds have scaled at ~50% per year for decades, DRAM bus latency and bandwidth have improved at merely ~7% annually. For data-intensive workloads—such as array reductions, vector operations, matrix arithmetic, and database filtering—modern systems spend up to <b>62% to 80% of total system energy and execution cycles purely moving data</b> across high-capacitance bus traces, rather than doing math. This fundamental hardware divergence is known as the <b>Memory Wall</b>.",
        style_body
    ))

    elements.append(Paragraph(
        "<b>The Processing in Memory (PIM) Paradigm:</b> PIM fundamentally reverses this model by moving computation directly into or immediately adjacent to the DRAM substrate. By placing compact Arithmetic Logic Units (ALUs) directly at the DRAM bank row buffers (Near-Memory Computing), operands can be accessed across thousands of internal bitlines with <b>terabytes-per-second internal bandwidth</b> and sub-nanosecond access latencies, eliminating the external memory bus bottleneck.",
        style_body
    ))

    elements.append(Paragraph(
        "<b>Project Scope & Purpose:</b> This project develops an end-to-end educational compiler and functional cycle simulator for PIM. It accepts high-level C code, executes full frontend compiler analysis, lowers ASTs to Three-Address Code (3AC) Intermediate Representation, identifies PIM-eligible instructions, maps them to near-memory operations, routes unsupported operations to host CPU fallback, executes the workload on dual software simulators (Pure CPU vs Heterogeneous Mixed CPU-PIM), and verifies mathematical equivalence with a 5-dimensional correctness comparator.",
        style_body
    ))

    callout_data = [[
        Paragraph("<b>Key Academic Distinction:</b> This project does NOT claim to emulate physical silicon transistors. It provides a mathematically rigorous <b>compiler-driven functional execution simulator and cycle cost model</b> that demonstrates how high-level software is partitioned onto near-memory hardware and verifies that offloading preserves 100% semantic equivalence.", style_callout)
    ]]
    callout_table = Table(callout_data, colWidths=[504])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_bg_callout),
        ('BOX', (0, 0), (-1, -1), 1, c_callout_border),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(callout_table)
    elements.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # SECTION 2: THE 6-PHASE ROADMAP & STATUS
    # -------------------------------------------------------------
    elements.append(Paragraph("2. Complete 6-Phase Architectural Roadmap", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=c_navy, spaceBefore=2, spaceAfter=6))

    roadmap_data = [
        [
            Paragraph("<b>Phase</b>", style_th),
            Paragraph("<b>Module Name</b>", style_th),
            Paragraph("<b>Responsibilities & Implemented Technical Features</b>", style_th),
            Paragraph("<b>Status</b>", style_th)
        ],
        [
            Paragraph("<b>Phase 1</b>", style_td),
            Paragraph("<b>Compiler Front End</b>", style_td_code),
            Paragraph("C tokenizer with exact line/column tracking, recursive descent parser with operator precedence climbing, Abstract Syntax Tree (AST), scoped symbol table (types, sizes, local/global scopes), and semantic diagnostic engine.", style_td),
            Paragraph("<font color='#059669'><b>Completed</b></font>", style_td)
        ],
        [
            Paragraph("<b>Phase 2</b>", style_td),
            Paragraph("<b>IR & PIM Mapping</b>", style_td_code),
            Paragraph("Three-Address Code (3AC) generation, temporaries (t0..tn), label sequencing, centralized PIM eligibility engine (PIM_ADD, PIM_LOAD, etc.), CPU fallback routing, and 4-term analytical cost model (NMC-Opt).", style_td),
            Paragraph("<font color='#059669'><b>Completed</b></font>", style_td)
        ],
        [
            Paragraph("<b>Phase 3</b>", style_td),
            Paragraph("<b>Simulators & Animation</b>", style_td_code),
            Paragraph("Pure CPU Simulator (baseline), Heterogeneous Mixed CPU-PIM Simulator (DRAM row buffer ALUs + CPU fallback), dynamic execution tracing, 5-dimensional Correctness Comparator (PASS/FAIL), and interactive animated UI.", style_td),
            Paragraph("<font color='#059669'><b>Completed</b></font>", style_td)
        ],
        [
            Paragraph("<b>Phase 4</b>", style_td),
            Paragraph("<b>Performance Analysis</b>", style_td_code),
            Paragraph("Quantitative memory bus traffic reduction metrics (bytes saved), cycle latency speedup curves, DRAM row-buffer hit ratios, and roofline operational intensity charts.", style_td),
            Paragraph("<font color='#d97706'><b>Next Phase</b></font>", style_td)
        ],
        [
            Paragraph("<b>Phase 5</b>", style_td),
            Paragraph("<b>Dashboard & UI</b>", style_td_code),
            Paragraph("Light-themed academic UI (React 19, Vite), live CodeMirror editor, compilation pipeline stepper, token inspect tables, AST hierarchy viewer, and FastAPI REST endpoints.", style_td),
            Paragraph("<font color='#059669'><b>Completed</b></font>", style_td)
        ],
        [
            Paragraph("<b>Phase 6</b>", style_td),
            Paragraph("<b>Evaluation Suite</b>", style_td_code),
            Paragraph("Comprehensive benchmark workloads: Vector Add, Array Reduction, GEMV (Matrix-Vector), Matrix Transpose, Array Scaling, and empirical scalability documentation.", style_td),
            Paragraph("<font color='#d97706'><b>In Progress</b></font>", style_td)
        ]
    ]

    roadmap_table = Table(roadmap_data, colWidths=[46, 104, 282, 72])
    roadmap_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_navy),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(roadmap_table)

    # Page Break for Phase Deep-Dives
    elements.append(PageBreak())

    # -------------------------------------------------------------
    # SECTION 3: IN-DEPTH TECHNICAL BREAKDOWN (PHASE BY PHASE)
    # -------------------------------------------------------------
    elements.append(Paragraph("3. In-Depth Technical Breakdown (Phases 1 to 3)", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=c_navy, spaceBefore=2, spaceAfter=6))

    # Phase 1 Deep-Dive
    elements.append(Paragraph("A. Phase 1: C Compiler Front End", style_h2))
    elements.append(Paragraph(
        "<b>1. Lexical Analysis (Scanner):</b> The tokenizer performs linear character scanning with deterministic regular expressions, converting C source code into a structured token stream with precise <code>(line, column)</code> tuples. Tokens recognize keywords (<code>int</code>, <code>return</code>, <code>if</code>, <code>else</code>, <code>for</code>, <code>while</code>), numeric literals, identifiers, arithmetic operators (<code>+</code>, <code>-</code>, <code>*</code>, <code>/</code>, <code>%</code>), relational operators (<code>==</code>, <code>!=</code>, <code>&lt;</code>, <code>&lt;=</code>, <code>&gt;</code>, <code>&gt;=</code>), delimiters (<code>;</code>, <code>,</code>, <code>{</code>, <code>}</code>, <code>(</code>, <code>)</code>, <code>[</code>, <code>]</code>), and strips single-line and multi-line comments.",
        style_body
    ))
    elements.append(Paragraph(
        "<b>2. Syntax Analysis (Parser):</b> Implemented as a handwritten recursive descent parser with precedence climbing for binary expressions. Operator precedence hierarchy from lowest to highest: Logical OR (<code>||</code>) &rarr; Logical AND (<code>&amp;&amp;</code>) &rarr; Equality (<code>==</code>, <code>!=</code>) &rarr; Relational (<code>&lt;</code>, <code>&gt;</code>, etc.) &rarr; Additive (<code>+</code>, <code>-</code>) &rarr; Multiplicative (<code>*</code>, <code>/</code>, <code>%</code>) &rarr; Unary prefix (<code>-</code>, <code>!</code>). Generates a typed Abstract Syntax Tree (AST) representing function definitions, variable declarations, array initializations, loop statements, and return blocks.",
        style_body
    ))
    elements.append(Paragraph(
        "<b>3. Semantic Analysis & Scoped Symbol Table:</b> Validates program semantics across nested lexical scopes (Global scope level 0, Local function/block scope level 1+). Traps undeclared variables, duplicate declarations in the same scope, illegal subscripting of scalar variables, array initializer size mismatches, compile-time division by zero, and static out-of-bounds array access. Tracks exact symbol metadata: <code>Type</code> (e.g. <code>int</code>, <code>int[]</code>), <code>Kind</code> (Function, Array, Scalar), <code>Size</code> (4 bytes for scalars, N &times; 4 bytes for arrays), and <code>Scope</code> (strictly <code>Global</code> or <code>Local</code>).",
        style_body
    ))

    # Phase 2 Deep-Dive
    elements.append(Paragraph("B. Phase 2: Intermediate Representation (IR) & PIM Instruction Mapping", style_h2))
    elements.append(Paragraph(
        "<b>1. Three-Address Code (3AC) Generation:</b> Translates nested AST expressions into a linearized Three-Address Code (3AC) format where each instruction has at most one destination register and two source operands. Employs a deterministic temporary register generator (<code>t0</code>, <code>t1</code>, <code>t2</code>, ...) and label sequencer (<code>L_loop_1</code>, <code>L_exit_1</code>). Supports array indexed loads (<code>LOAD_INDEXED dest, arr[idx]</code>), array indexed stores (<code>STORE_INDEXED arr[idx], val</code>), unconditional jumps (<code>JUMP label</code>), and conditional branches (<code>BRANCH cond, true_label, false_label</code>).",
        style_body
    ))
    elements.append(Paragraph(
        "<b>2. Centralized PIM Eligibility & Mapping Rules:</b> Evaluates each 3AC instruction according to realistic hardware offloading constraints:",
        style_body
    ))

    rules_data = [
        [Paragraph("<b>Instruction Opcode</b>", style_th), Paragraph("<b>Target</b>", style_th), Paragraph("<b>Mapped Mnemonic</b>", style_th), Paragraph("<b>Architectural Rationale & Hardware Justification</b>", style_th)],
        [Paragraph("LOAD_INDEXED", style_td_code), Paragraph("<font color='#059669'><b>PIM</b></font>", style_td), Paragraph("PIM_LOAD", style_td_code), Paragraph("In-situ array element read directly from DRAM bank row buffer; 0 bus cycles.", style_td)],
        [Paragraph("STORE_INDEXED", style_td_code), Paragraph("<font color='#059669'><b>PIM</b></font>", style_td), Paragraph("PIM_STORE", style_td_code), Paragraph("In-situ write committing directly into local DRAM bank partition; 0 bus cycles.", style_td)],
        [Paragraph("ADD / SUB / MUL", style_td_code), Paragraph("<font color='#059669'><b>PIM</b></font>", style_td), Paragraph("PIM_ADD/SUB/MUL", style_td_code), Paragraph("Low-area integer arithmetic executed in near-memory row-buffer ALUs.", style_td)],
        [Paragraph("COMPARE_LT/GT/EQ", style_td_code), Paragraph("<font color='#059669'><b>PIM</b></font>", style_td), Paragraph("PIM_COMPARE", style_td_code), Paragraph("Row-buffer comparator evaluating condition flags directly in memory.", style_td)],
        [Paragraph("DIV / MOD", style_td_code), Paragraph("<font color='#4f46e5'><b>CPU</b></font>", style_td), Paragraph("CPU_DIV / CPU_MOD", style_td_code), Paragraph("CPU Fallback: High area/power multi-cycle divider hardware excluded from DRAM die.", style_td)],
        [Paragraph("BRANCH / JUMP / LABEL", style_td_code), Paragraph("<font color='#4f46e5'><b>CPU</b></font>", style_td), Paragraph("CPU_BRANCH / JUMP", style_td_code), Paragraph("CPU Fallback: Program Counter, branch predictors, and loop control reside on host core.", style_td)],
        [Paragraph("CONST / LOAD / STORE", style_td_code), Paragraph("<font color='#4f46e5'><b>CPU</b></font>", style_td), Paragraph("CPU_CONST / LOAD", style_td_code), Paragraph("CPU Fallback: Immediates reside in code stream; scalar variables in host stack frame.", style_td)]
    ]
    rules_table = Table(rules_data, colWidths=[96, 44, 94, 270])
    rules_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_navy),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(rules_table)
    elements.append(Spacer(1, 6))

    elements.append(Paragraph(
        "<b>3. Research-Informed Analytical Cost Model:</b> Implements a 4-term analytical formulation inspired by NMC-Opt research: "
        "<code>Total_Cost = Compute_Cost + Transfer_Cost + Layout_Cost + Synchronization_Cost</code>. "
        "Evaluates whether offloading yields net positive cycle speedups under realistic hardware parameters: CPU execution (1.0 cycle/op), PIM ALU execution (1.2 cycles/op), Offload launch overhead (4.0 cycles), and Bus bandwidth (2.0 bytes/cycle). Evaluates candidate candidate placement strategies (<code>CPU_ONLY</code>, <code>DIRECT_PIM</code>, <code>TRANSFORMED_PIM</code>).",
        style_body
    ))

    # Phase 3 Deep-Dive
    elements.append(Paragraph("C. Phase 3: CPU & PIM Execution Simulators with Interactive Animation", style_h2))
    elements.append(Paragraph(
        "<b>1. Host CPU Simulator (Pure CPU Execution Baseline):</b> Executes raw 3AC IR instructions on a simulated classical von Neumann CPU core. Maintains runtime environments for stack-allocated scalar variables, heap memory for arrays, an arithmetic ALU, and a sequential program counter with branch redirection.",
        style_body
    ))
    elements.append(Paragraph(
        "<b>2. Heterogeneous Mixed CPU–PIM Simulator:</b> Simulates distributed execution across two cooperating domains: host CPU core and near-memory PIM units. Operations designated as <code>PIM</code> execute in simulated DRAM row-buffer ALUs with zero external bus cycles. Operations designated as <code>CPU</code> execute on host CPU fallback. The simulator faithfully manages state synchronization and data handoffs at every step.",
        style_body
    ))
    elements.append(Paragraph(
        "<b>3. 5-Dimensional Correctness Comparator:</b> Executes both simulators on the exact same input code and verifies semantic equivalence across 5 independent state dimensions: (1) Final return value, (2) Scalar variables dictionary, (3) DRAM array buffer contents, (4) Emitted console output, (5) Runtime fault consistency. Outputs definitive verdict: <b>PASS</b> (all 5 states match 100%), <b>FAIL</b> (state mismatch detected), or <b>ERROR</b> (runtime exception like division by zero).",
        style_body
    ))
    elements.append(Paragraph(
        "<b>4. Interactive Step-by-Step Animated Visualizer:</b> React 19 UI component providing Play, Pause, Step Forward, Step Backward, Restart, and adjustable animation speeds (Slow 1500ms, Normal 800ms, Fast 300ms). Synchronized dual-processor views (Host CPU Core with stack variables vs PIM DRAM Bank memory partitions) with glowing highlights on actively updated memory cells and ALU operators.",
        style_body
    ))

    # Page Break for Phase 3 Simulation Mechanics & Terminology
    elements.append(PageBreak())

    # -------------------------------------------------------------
    # SECTION 4: HOW THE SIMULATION ENGINE WORKS EXACTLY
    # -------------------------------------------------------------
    elements.append(Paragraph("4. How the Simulation Engine Works Step-by-Step", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=c_navy, spaceBefore=2, spaceAfter=6))

    elements.append(Paragraph(
        "A common review question is: <i>'How does your software simulator actually execute instructions, track memory, and prove correctness without real PIM silicon?'</i> This section explains the exact step-by-step lifecycle of the simulation engine:",
        style_body
    ))

    sim_steps = [
        ("Step 1: Program Lowering & Instruction Mapping",
         "The C source code is compiled into linearized 3AC instructions. The centralized mapper tags each instruction with an execution target (<code>target: 'PIM'</code> or <code>target: 'CPU'</code>) and a specialized mnemonic (e.g. <code>PIM_ADD</code> vs <code>CPU_BRANCH</code>)."),
        ("Step 2: Dual Independent Runtime Environments",
         "The backend instantiates two completely separate simulator runtimes: <b>Runtime A (Pure CPU Baseline)</b> and <b>Runtime B (Heterogeneous Mixed CPU-PIM)</b>. Both start with identical empty environments (empty variable dictionaries, unallocated array buffers, program counter <code>pc = 0</code>, step counter <code>step = 0</code>)."),
        ("Step 3: Baseline CPU Execution Loop",
         "Runtime A executes every instruction strictly on the host CPU model. For array reads, it simulates transporting elements over the memory bus into CPU registers, then performs CPU arithmetic. It logs every state change into <code>cpu_trace</code> until a <code>RETURN</code> instruction or program halt is reached."),
        ("Step 4: Heterogeneous Mixed CPU-PIM Execution Loop",
         "Runtime B inspects the instruction's <code>target</code> tag: "
         "<br/>&bull; If <code>target == 'PIM'</code>: The operation is executed inside the simulated <b>DRAM Bank Row Buffer ALU</b>. For array operations (<code>PIM_LOAD</code>, <code>PIM_STORE</code>), data is fetched directly from local bank partitions without bus traversal. The event is logged as an <code>in-situ</code> operation."
         "<br/>&bull; If <code>target == 'CPU'</code>: The operation executes on the <b>Host CPU fallback</b> (e.g. evaluating loop branches, updating stack-allocated loop index <code>i</code>). The event is logged as a <code>fallback</code> operation."
         "<br/>&bull; <b>Data Handoff:</b> When execution alternates between CPU and PIM, shared scalar variables and updated array elements are passed seamlessly between environments without losing intermediate values."),
        ("Step 5: Dynamic Step-by-Step Trace Serialization",
         "At every instruction executed, both runtimes capture an immutable snapshot: <code>step_number</code>, <code>ir_instruction</code>, <code>processor_location</code> ('CPU' or 'PIM'), <code>operands</code>, <code>operation_performed</code>, <code>result_value</code>, <code>memory_diff</code>, and complete memory dumps (scalars and arrays)."),
        ("Step 6: 5-Dimensional Equivalence Verification",
         "Upon completion of both simulation loops, the <b>Correctness Comparator</b> performs a deep comparison across 5 independent dimensions: (1) <code>return_value</code>, (2) <code>variables</code> dictionary, (3) <code>arrays</code> contents, (4) <code>stdout</code> output, and (5) <code>runtime_faults</code>. If all 5 match identically, it certifies the execution as <b>PASS</b>.")
    ]

    for title, desc in sim_steps:
        elements.append(Paragraph(f"<b>&bull; {title}:</b>", style_h3))
        elements.append(Paragraph(desc, style_body))

    elements.append(Spacer(1, 6))

    # -------------------------------------------------------------
    # SECTION 5: TERMINOLOGY DICTIONARY & ARCHITECTURAL CONCEPTS
    # -------------------------------------------------------------
    elements.append(Paragraph("5. Architectural Terminology Dictionary & Key Concepts", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=c_navy, spaceBefore=2, spaceAfter=6))
    elements.append(Paragraph("This section defines every technical term used in the project dashboard and simulator, explaining the exact computer systems principles behind them for viva questioning.", style_body))

    terms = [
        (
            "In-Situ Processing",
            "Latin for 'in place' or 'on-site'. In computer architecture, in-situ processing means performing mathematical operations directly inside the memory substrate where the data is stored (e.g., inside the DRAM bank row buffer), rather than moving the data across the system bus into CPU registers. In our simulator, operations like <code>PIM_ADD</code> and <code>PIM_LOAD</code> operate in-situ, incurring 0 external memory bus traffic."
        ),
        (
            "DRAM Bank",
            "An independent physical memory array inside a DRAM chip composed of rows and columns of capacitive storage cells. A typical modern DRAM chip contains 8 to 32 independent banks. In our PIM model, array buffers (e.g. <code>arr[4]</code>) are mapped into local DRAM bank partitions, allowing local PIM ALUs to access them in parallel with host CPU operations."
        ),
        (
            "DRAM Row Buffer",
            "A temporary internal latch circuit composed of sense amplifiers that holds an entire active row of DRAM memory (typically 2KB to 8KB). When memory is accessed, an entire row is opened into the row buffer. Near-Memory Computing places ALUs immediately next to this row buffer, allowing wide-word vector operations to execute across thousands of bits in parallel with massive internal bandwidth (terabytes/sec)."
        ),
        (
            "CPU Fallback",
            "The architectural mechanism where operations not supported by the limited near-memory logic are automatically redirected to the host CPU core. Because placing complex out-of-order branch predictors, deep pipelines, floating-point units, and hardware dividers inside DRAM would cause severe silicon area and thermal penalties, our compiler falls back to the host CPU for control-flow branching (<code>BRANCH</code>, <code>JUMP</code>), immediate constants (<code>CONST</code>), and complex math (<code>DIV</code>, <code>MOD</code>)."
        ),
        (
            "Near-Memory Computing (NMC) vs True PIM",
            "Near-Memory Computing (NMC) places digital logic ALUs on the periphery of memory banks, at the base logic die of 3D-stacked DRAM (e.g., HBM), or on the memory buffer chip. True Processing-in-Memory (PIM) performs computation using the analog charge-sharing properties of the bitlines themselves. Our educational project models the dominant industry standard: Near-Memory Computing with row-buffer ALUs."
        ),
        (
            "Three-Address Code (3AC)",
            "A standard compiler intermediate representation where every instruction has at most one operator and three operand addresses (e.g. <code>t3 = sum + t2</code>). 3AC is necessary because high-level C expressions like <code>sum = sum + arr[i]</code> must be broken down into discrete memory loads, address calculations, and additions before hardware mapping can occur."
        ),
        (
            "Semantic Equivalence",
            "A formal guarantee that running a program across a distributed, heterogeneous CPU-PIM architecture produces the exact same observable mathematical output and memory state as running it on a standard single-core CPU. Our Correctness Comparator verifies this after every simulation run."
        ),
        (
            "Dynamic Execution Trace",
            "A chronological log of every single instruction executed during runtime. Unlike static code inspection, the dynamic trace records the actual sequence of loop iterations, live operand values (e.g. <code>sum = 30 + 30 = 60</code>), runtime program counters, and snapshots of memory after every clock cycle."
        ),
        (
            "Data Handoff / Transfer Event",
            "An event where data is transferred between the host CPU execution environment and the near-memory PIM environment. For example, when the host CPU evaluates a loop condition and passes the array index <code>i</code> to the PIM row buffer, or when PIM commits an array write into DRAM bank memory."
        )
    ]

    for title, desc in terms:
        elements.append(Paragraph(f"<b>&bull; {title}:</b>", style_h3))
        elements.append(Paragraph(desc, style_body))

    # Page Break for Demonstration Walkthrough
    elements.append(PageBreak())

    # -------------------------------------------------------------
    # SECTION 6: DEMONSTRATION WORKLOAD (ARRAY SUMMATION)
    # -------------------------------------------------------------
    elements.append(Paragraph("6. Walkthrough of Demonstration Workload (Sample 1)", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=c_navy, spaceBefore=2, spaceAfter=6))

    elements.append(Paragraph("Consider the standard college demonstration test program supported by our compiler:", style_body))
    demo_code = """int main() {
    int arr[4] = {10, 20, 30, 40};
    int sum = 0;

    for (int i = 0; i < 4; i++) {
        sum = sum + arr[i];
    }

    return 0;
}"""
    elements.append(Paragraph(demo_code.replace("\n", "<br/>").replace(" ", "&nbsp;"), style_code))

    elements.append(Paragraph("<b>End-to-End Pipeline Execution Trace:</b>", style_h2))
    walkthrough_steps = [
        "<b>1. Lexical Analysis:</b> Generates 48 ordered tokens with exact line and column numbers. Identifies keywords (<code>int</code>, <code>for</code>, <code>return</code>), identifiers (<code>arr</code>, <code>sum</code>, <code>i</code>), brackets, and delimiters.",
        "<b>2. Syntax & AST Construction:</b> Builds a <code>Program</code> node with a <code>FunctionDef</code> (<code>main</code>), a <code>Block</code> containing an <code>ArrayDecl</code> (size 4, initializers 10, 20, 30, 40), a <code>VarDecl</code> (<code>sum = 0</code>), a <code>ForLoop</code> (init <code>i = 0</code>, cond <code>i &lt; 4</code>, update <code>i++</code>), and a <code>ReturnStatement</code>.",
        "<b>3. Scoped Symbol Table:</b> Registers <code>arr</code> as <code>int[]</code> Array (4 elements, 16 bytes, Local), <code>sum</code> as <code>int</code> Scalar (4 bytes, Local), and <code>i</code> as <code>int</code> Scalar (4 bytes, Local). All sizes and scopes are mathematically verified.",
        "<b>4. 3AC IR Generation:</b> Lowers the loop into discrete 3AC instructions: array element initialization, loop condition evaluation (<code>COMPARE_LT t_cmp, i, 4</code>), conditional jump (<code>BRANCH t_cmp, L_body, L_exit</code>), array indexed access (<code>LOAD_INDEXED t_elem, arr[i]</code>), addition (<code>ADD t_add, sum, t_elem</code>), assignment (<code>STORE sum, t_add</code>), and loop increment (<code>ADD t_inc, i, 1</code>).",
        "<b>5. PIM Mapping:</b> Categorizes instructions. <code>LOAD_INDEXED</code> is mapped to <code>PIM_LOAD</code> (row buffer read). <code>ADD t_add, sum, t_elem</code> and <code>ADD t_inc, i, 1</code> are mapped to <code>PIM_ADD</code> (near-memory ALU). The loop branch and jump are mapped to <code>CPU_BRANCH</code> and <code>CPU_JUMP</code> (CPU fallback).",
        "<b>6. Dual Simulation & Verification:</b> The CPU simulator executes all 91 dynamic steps in pure CPU mode. The PIM simulator executes 21 in-situ PIM steps and 70 CPU fallback steps. Both finish with identical states: <code>sum = 100</code>, <code>i = 4</code>, <code>arr = [10, 20, 30, 40]</code>, and <code>return_value = 0</code>. The comparator outputs <b>✓ VERIFIED: PASS</b>."
    ]
    for step in walkthrough_steps:
        elements.append(Paragraph(f"&bull; {step}", style_bullet))

    elements.append(Spacer(1, 6))

    # Step-by-Step Iteration Trace Table
    elements.append(Paragraph("<b>Dynamic Iteration-by-Iteration Execution Breakdown:</b>", style_h2))
    trace_table_data = [
        [Paragraph("<b>Phase / Iteration</b>", style_th), Paragraph("<b>Key IR Instruction Executed</b>", style_th), Paragraph("<b>Target</b>", style_th), Paragraph("<b>Live Values & Result Produced</b>", style_th), Paragraph("<b>Memory State After Step</b>", style_th)],
        [Paragraph("Init Phase", style_td), Paragraph("STORE sum, 0<br/>STORE i, 0", style_td_code), Paragraph("CPU", style_td), Paragraph("sum &larr; 0<br/>i &larr; 0", style_td), Paragraph("arr=[10,20,30,40], sum=0, i=0", style_td)],
        [Paragraph("Iteration 0 (i=0)", style_td), Paragraph("PIM_LOAD t0, arr[0]<br/>PIM_ADD t1, sum, t0", style_td_code), Paragraph("<font color='#059669'><b>PIM</b></font>", style_td), Paragraph("t0 &larr; 10 (row buffer)<br/>t1 &larr; 0 + 10 = 10", style_td), Paragraph("sum &larr; 10, i &larr; 1", style_td)],
        [Paragraph("Iteration 1 (i=1)", style_td), Paragraph("PIM_LOAD t0, arr[1]<br/>PIM_ADD t1, sum, t0", style_td_code), Paragraph("<font color='#059669'><b>PIM</b></font>", style_td), Paragraph("t0 &larr; 20 (row buffer)<br/>t1 &larr; 10 + 20 = 30", style_td), Paragraph("sum &larr; 30, i &larr; 2", style_td)],
        [Paragraph("Iteration 2 (i=2)", style_td), Paragraph("PIM_LOAD t0, arr[2]<br/>PIM_ADD t1, sum, t0", style_td_code), Paragraph("<font color='#059669'><b>PIM</b></font>", style_td), Paragraph("t0 &larr; 30 (row buffer)<br/>t1 &larr; 30 + 30 = 60", style_td), Paragraph("sum &larr; 60, i &larr; 3", style_td)],
        [Paragraph("Iteration 3 (i=3)", style_td), Paragraph("PIM_LOAD t0, arr[3]<br/>PIM_ADD t1, sum, t0", style_td_code), Paragraph("<font color='#059669'><b>PIM</b></font>", style_td), Paragraph("t0 &larr; 40 (row buffer)<br/>t1 &larr; 60 + 40 = 100", style_td), Paragraph("sum &larr; 100, i &larr; 4", style_td)],
        [Paragraph("Loop Exit", style_td), Paragraph("PIM_COMPARE i &lt; 4 &rarr; False<br/>CPU_BRANCH &rarr; L_exit<br/>RETURN 0", style_td_code), Paragraph("PIM<br/>CPU<br/>CPU", style_td), Paragraph("Condition fails (4 &lt; 4 = False)<br/>Exit loop jumped<br/>Exit code 0", style_td), Paragraph("<b>Final State:</b><br/>sum = 100, i = 4, ret = 0<br/><b>Verdict: PASS (100% Match)</b>", style_td)]
    ]
    trace_table = Table(trace_table_data, colWidths=[80, 120, 42, 130, 132])
    trace_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_navy),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(trace_table)

    # Page Break for Viva Q&A
    elements.append(PageBreak())

    # -------------------------------------------------------------
    # SECTION 7: ANTICIPATED VIVA / REVIEW QUESTIONS & ANSWERS
    # -------------------------------------------------------------
    elements.append(Paragraph("7. Anticipated Viva & Review Questions (10 Model Answers)", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=c_navy, spaceBefore=2, spaceAfter=6))

    qa_list = [
        (
            "Q1: Why do we need PIM if modern host CPUs already run at 4 GHz+ with large multi-megabyte L3 caches?",
            "<b>Answer:</b> While CPUs compute very fast, their performance on data-intensive workloads is severely starved by memory bandwidth and access latency (the von Neumann Memory Wall). Moving data over off-chip PCB traces takes ~20-50x more energy than computing it. When dataset sizes exceed cache capacities, CPU cores stall waiting for DRAM. PIM provides terabytes/sec internal row-buffer bandwidth directly at the memory cells with zero bus traversal."
        ),
        (
            "Q2: Why did our compiler map array addition to PIM, but kept loop branching on the CPU?",
            "<b>Answer:</b> This demonstrates fundamental heterogeneous architecture trade-offs. PIM logic inside DRAM is severely area- and thermal-constrained. Placing complex out-of-order branch predictors, deep pipeline registers, and speculative execution hardware inside DRAM would destroy memory density and cause severe thermal throttling. Arithmetic (ADD, SUB, MUL) is simple and compact, making it ideal for near-memory row buffer ALUs, while control flow is best managed by the host CPU."
        ),
        (
            "Q3: Does our simulator run on real physical PIM chips (like Samsung HBM-PIM or UPMEM)?",
            "<b>Answer:</b> No. This project is a software-based compiler and functional cycle simulator. Real physical PIM hardware is proprietary, expensive, and specialized. Our project models the architectural mechanics of PIM—instruction decomposition, eligibility analysis, offloading heuristics, fallback execution, and state equivalence—making it a complete educational and research compiler platform."
        ),
        (
            "Q4: How does our system guarantee that PIM execution doesn't corrupt program results?",
            "<b>Answer:</b> Through our 5-dimensional Correctness Comparator implemented in Phase 3. After dual execution, it performs deep semantic state comparisons on: (1) return value, (2) scalar variable values, (3) DRAM array contents, (4) stdout output, and (5) runtime faults. The verdict only reports PASS if all states are 100% identical."
        ),
        (
            "Q5: What is the difference between latency reduction and bandwidth reduction in PIM?",
            "<b>Answer:</b> Bandwidth reduction refers to eliminating bytes sent over the external memory bus (saving bus contention and energy). Latency reduction refers to doing the math immediately at the activated row buffer in ~1-2 memory cycles, avoiding the multi-nanosecond round-trip transit through memory controllers, cache buses, and CPU registers."
        ),
        (
            "Q6: What happens with Cache Coherence when PIM modifies array data in DRAM?",
            "<b>Answer:</b> Cache coherence is a central challenge in heterogeneous PIM systems. If PIM modifies DRAM directly, any cached copies in CPU L1/L2/L3 caches could become stale. In our compiler model, arrays mapped to PIM are marked uncacheable by the host or flushed/invalidated across offload boundaries to prevent stale cache lines."
        ),
        (
            "Q7: Why does PIM achieve high energy efficiency even if the PIM clock frequency is lower than the CPU?",
            "<b>Answer:</b> Driving capacitive PCB bus traces across DDR channels consumes ~20-50 pJ/bit, whereas computing inside the row buffer consumes ~1-2 pJ/bit. Because data movement accounts for up to 80% of total system energy, eliminating bus round-trips yields massive net energy savings even at modest 500 MHz DRAM frequencies."
        ),
        (
            "Q8: How does your 4-term Analytical Cost Model decide whether to offload an operation?",
            "<b>Answer:</b> Based on NMC-Opt research: it compares <code>Cost(CPU_ONLY)</code> vs <code>Cost(PIM_OFFLOAD)</code>. The offload cost accounts for <code>Compute_Cost + Transfer_Cost + Layout_Cost + Synchronization_Cost</code>. If array data is already memory-resident, <code>Transfer_Cost</code> is 0, so PIM wins. If heavy host-PIM synchronization or non-contiguous layout is required, the compiler falls back to CPU."
        ),
        (
            "Q9: Can PIM handle loops with loop-carried dependencies (e.g. sum = sum + arr[i])?",
            "<b>Answer:</b> Yes. In reduction loops, the accumulator (<code>sum</code>) can reside in a local row-buffer register, allowing each iteration to accumulate in-situ without CPU intervention until the loop terminates, at which point the single final scalar is handed back to the host CPU."
        ),
        (
            "Q10: How are the interactive animation controls synchronized with the backend traces?",
            "<b>Answer:</b> The FastAPI backend returns the complete serialized chronological list of execution steps (program counters, operands, memory diffs, and CPU/PIM tags). The React 19 UI stores this trace in state and drives a step-index cursor controlled by <code>requestAnimationFrame</code> and timers, updating DOM node glows and tabular states deterministically without running arbitrary frontend math."
        )
    ]

    for q, a in qa_list:
        elements.append(Paragraph(f"<b>{q}</b>", style_h3))
        elements.append(Paragraph(a, style_body))

    # Page Break for Viva Cheat-Sheet
    elements.append(PageBreak())

    # -------------------------------------------------------------
    # SECTION 8: 60-SECOND VIVA CHEAT-SHEET
    # -------------------------------------------------------------
    elements.append(Paragraph("8. 60-Second Viva Cheat-Sheet (Quick Defense Guide)", style_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=c_navy, spaceBefore=2, spaceAfter=6))

    cheat_data = [
        [
            Paragraph("<b>Reviewer Question</b>", style_th),
            Paragraph("<b>What to Say (Crisp 15-Second Defense)</b>", style_th)
        ],
        [
            Paragraph("<b>1. Introduce your project in 30 seconds.</b>", style_td_code),
            Paragraph("<i>'Our project is a compiler and execution simulator for Processing in Memory (PIM). Traditional computers waste up to 80% of energy moving data over the bus between CPU and RAM (the Memory Wall). Our compiler parses C code into Three-Address Code IR, identifies PIM-eligible array operations, maps them to near-memory DRAM row-buffer ALUs, routes control flow to CPU fallback, and proves correctness through dual-simulation verification with an interactive visualizer.'</i>", style_td)
        ],
        [
            Paragraph("<b>2. What was your specific contribution in Phase 3?</b>", style_td_code),
            Paragraph("<i>'In Phase 3, we built two complete execution simulators: a Pure CPU baseline and a Heterogeneous Mixed CPU-PIM simulator. We implemented dynamic cycle-by-cycle tracing, in-situ row buffer ALUs, CPU fallback routing, a 5-dimensional Correctness Comparator (which proved 100% semantic match on all 91 steps of our array sum workload), and an animated React visualizer with play/pause and step controls.'</i>", style_td)
        ],
        [
            Paragraph("<b>3. How do you prove your simulation is correct?</b>", style_td_code),
            Paragraph("<i>'Our Correctness Comparator checks 5 independent dimensions: return value (0), scalar variables (sum=100, i=4), DRAM array contents ([10,20,30,40]), console output, and runtime faults. Because all 5 dimensions match the CPU baseline identically, our simulation formally achieves a PASS verdict.'</i>", style_td)
        ],
        [
            Paragraph("<b>4. Why not run everything on PIM?</b>", style_td_code),
            Paragraph("<i>'DRAM is optimized for bit density, not high-power logic. Complex circuits like branch predictors, dividers, and floating point units cause severe thermal throttling inside DRAM stacks. Simple ALUs (ADD, SUB, LOAD, STORE) take minimal silicon area, so keeping control-flow on the CPU host (CPU fallback) is the optimal heterogeneous design.'</i>", style_td)
        ],
        [
            Paragraph("<b>5. What are your project metrics?</b>", style_td_code),
            Paragraph("<i>'On our array sum test program, total dynamic steps: 91. PIM in-situ steps: 21 (23.1%). CPU fallback steps: 70 (76.9%). Offload verification: PASS. Unit and integration tests passing: 73 out of 73 (100%).'</i>", style_td)
        ]
    ]

    cheat_table = Table(cheat_data, colWidths=[150, 354])
    cheat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_navy),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(cheat_table)
    elements.append(Spacer(1, 14))

    final_box = [
        [Paragraph("<b>Ready for Review:</b> Everything documented in this handbook corresponds 1:1 with the code in <code>backend/</code> and <code>frontend/</code>. All 73 tests are passing, and the interactive simulator is live at <code>http://localhost:5173</code>.", style_callout)]
    ]
    final_table = Table(final_box, colWidths=[504])
    final_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_bg_callout),
        ('BOX', (0, 0), (-1, -1), 1, c_callout_border),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(final_table)

    # Build the document
    doc.build(elements, canvasmaker=NumberedCanvas)
    print(f"Report successfully generated at: {filename}")


if __name__ == "__main__":
    output_pdf = sys.argv[1] if len(sys.argv) > 1 else "Compiler_PIM_Project_Review_Handbook.pdf"
    build_pdf(output_pdf)
