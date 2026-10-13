import React from 'react';

export const LanguageSpec = () => {
  return (
    <div className="language-spec-card">
      <div className="d-flex justify-content-between align-items-center mb-2">
        <h4 className="spec-heading m-0">C Language Specification & PIM/CPU Mapping Architecture</h4>
        <span className="badge bg-success-subtle text-success border border-success-subtle px-2 py-1">
          Full C Subset + Preprocessor Enabled
        </span>
      </div>

      <div className="spec-grid">
        <div className="spec-column">
          <h5 className="spec-subheading text-success">✓ PIM-Accelerated Core (Near-Memory)</h5>
          <ul className="spec-list">
            <li><strong>Array Arithmetic:</strong> <code>ADD</code>, <code>SUB</code>, <code>MUL</code> directly in DRAM bank row buffers</li>
            <li><strong>In-Situ Array Memory:</strong> <code>arr[i]</code> mapped to <code>PIM_LOAD</code> / <code>PIM_STORE</code> without bus roundtrip</li>
            <li><strong>Hardware Comparators:</strong> <code>&lt;</code>, <code>&lt;=</code>, <code>&gt;</code>, <code>&gt;=</code>, <code>==</code>, <code>!=</code> evaluated in memory bank</li>
            <li><strong>Loop Reductions:</strong> Dense array loops, vector scaling, summation accelerated at memory level</li>
            <li><strong>Zero Bus Bottleneck:</strong> Eliminates Von Neumann bandwidth bottleneck for memory-bound array kernels</li>
          </ul>
        </div>

        <div className="spec-column">
          <h5 className="spec-subheading text-primary">✓ Extended C Constructs (Host CPU Fallback)</h5>
          <ul className="spec-list">
            <li><strong>Preprocessor & Modules:</strong> <code>#include &lt;stdio.h&gt;</code>, <code>#define</code>, <code>#pragma</code>, <code>import</code> modules</li>
            <li><strong>Modular Functions:</strong> Custom functions, helper definitions, custom return types & parameters</li>
            <li><strong>Standard Library & I/O:</strong> <code>printf(...)</code>, <code>scanf(...)</code>, <code>malloc(...)</code>, <code>free(...)</code></li>
            <li><strong>Pointers & Address-Of:</strong> <code>*ptr</code>, <code>&amp;var</code>, pointer variables & indirect dereferencing</li>
            <li><strong>Floating-Point:</strong> <code>float</code>, <code>double</code> literals and calculations</li>
            <li><strong>Composite Structures:</strong> <code>struct</code> and <code>union</code> declarations with member access (<code>.</code>, <code>-&gt;</code>)</li>
            <li><strong>Bitwise & Shifts:</strong> <code>&amp;</code>, <code>|</code>, <code>^</code>, <code>~</code>, <code>&lt;&lt;</code>, <code>&gt;&gt;</code></li>
          </ul>
        </div>
      </div>

      <div className="mt-3 p-2 bg-dark-subtle rounded border border-secondary-subtle small text-muted">
        <strong className="text-light">Architecture Policy:</strong> Dense array operations execute inside simulated PIM bank row buffers for maximum memory bandwidth savings. Complex language features (system I/O, stack activations, pointer dereferencing, struct layouts) transparently route to Host CPU fallback with complete semantic correctness.
      </div>
    </div>
  );
};

export default LanguageSpec;
