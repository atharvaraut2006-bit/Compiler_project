import React from 'react';

export const LanguageSpec = () => {
  return (
    <div className="language-spec-card">
      <h4 className="spec-heading">Supported C Subset Specification</h4>
      <div className="spec-grid">
        <div className="spec-column">
          <h5 className="spec-subheading text-success">✓ Supported Constructs</h5>
          <ul className="spec-list">
            <li><strong>Types:</strong> <code>int</code> (32-bit scalar & 1D fixed-size arrays)</li>
            <li><strong>Declarations:</strong> <code>int x = 10;</code>, <code>int arr[4] = &#123;10, 20, 30, 40&#125;;</code></li>
            <li><strong>Arithmetic:</strong> <code>+</code>, <code>-</code>, <code>*</code>, <code>/</code>, <code>%</code> (with div-by-zero check)</li>
            <li><strong>Assignment:</strong> <code>=</code>, <code>+=</code>, <code>-=</code>, <code>*=</code>, <code>/=</code>, <code>++</code>, <code>--</code></li>
            <li><strong>Relational & Logic:</strong> <code>&lt;</code>, <code>&lt;=</code>, <code>&gt;</code>, <code>&gt;=</code>, <code>==</code>, <code>!=</code>, <code>&amp;&amp;</code>, <code>||</code>, <code>!</code></li>
            <li><strong>Control Flow:</strong> <code>for (...)</code>, <code>while (...)</code>, <code>if (...) else</code>, <code>return</code></li>
            <li><strong>Functions:</strong> <code>int main() &#123; ... &#125;</code> and block scoping <code>&#123; ... &#125;</code></li>
            <li><strong>Comments:</strong> <code>// single-line</code> and <code>/* multi-line */</code></li>
          </ul>
        </div>
        <div className="spec-column">
          <h5 className="spec-subheading text-danger">✗ Explicitly Unsupported</h5>
          <ul className="spec-list text-muted">
            <li>Pointers and pointer arithmetic (<code>*ptr</code>, <code>&amp;var</code>)</li>
            <li>Dynamic memory allocation (<code>malloc</code>, <code>free</code>)</li>
            <li>Structures and unions (<code>struct</code>, <code>union</code>)</li>
            <li>Preprocessor directives (<code>#include</code>, <code>#define</code>)</li>
            <li>Multi-dimensional arrays (<code>int m[2][2]</code>)</li>
            <li>Floating-point numbers (<code>float</code>, <code>double</code>)</li>
            <li>Arbitrary standard library calls (only built-in <code>print()</code> supported)</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default LanguageSpec;
