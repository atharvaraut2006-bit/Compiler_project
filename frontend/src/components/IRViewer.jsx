import React, { useState, useMemo } from 'react';
import { FaCopy, FaCheck, FaCode, FaTableList } from 'react-icons/fa6';

export const IRViewer = ({ ir }) => {
  const [viewMode, setViewMode] = useState('formatted'); // 'formatted' or 'table'
  const [filterText, setFilterText] = useState('');
  const [copied, setCopied] = useState(false);

  const instructions = ir?.instructions || [];
  const formattedText = ir?.formatted || '';

  const filteredInstructions = useMemo(() => {
    if (!filterText.trim()) return instructions;
    const lower = filterText.toLowerCase();
    return instructions.filter(
      (instr) =>
        instr.opcode?.toLowerCase().includes(lower) ||
        instr.dest?.toLowerCase().includes(lower) ||
        instr.arg1?.toLowerCase().includes(lower) ||
        instr.arg2?.toLowerCase().includes(lower) ||
        instr.formatted?.toLowerCase().includes(lower)
    );
  }, [instructions, filterText]);

  const handleCopy = () => {
    navigator.clipboard.writeText(formattedText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getOpcodeBadgeClass = (opcode) => {
    if (['ADD', 'SUB', 'MUL', 'DIV', 'MOD'].includes(opcode)) return 'badge-op-arithmetic';
    if (opcode.startsWith('COMPARE_')) return 'badge-op-compare';
    if (['LOAD', 'STORE', 'LOAD_INDEXED', 'STORE_INDEXED'].includes(opcode)) return 'badge-op-mem';
    if (['JUMP', 'BRANCH', 'LABEL'].includes(opcode)) return 'badge-op-control';
    if (opcode === 'DECLARE') return 'badge-op-decl';
    return 'badge-op-default';
  };

  if (!ir || instructions.length === 0) {
    return (
      <div className="empty-tab-state">
        <p>No Intermediate Representation generated.</p>
      </div>
    );
  }

  return (
    <div className="ir-viewer-container">
      {/* Top Action Toolbar */}
      <div className="ir-toolbar">
        <div className="ir-toolbar-left">
          <input
            type="text"
            className="table-filter-input"
            placeholder="Filter IR instructions..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
          />
          <span className="ir-count-badge">
            {filteredInstructions.length} instruction{filteredInstructions.length === 1 ? '' : 's'}
          </span>
        </div>

        <div className="ir-toolbar-right">
          <button
            className="btn btn-outline btn-sm"
            onClick={handleCopy}
            title="Copy 3AC IR to Clipboard"
          >
            {copied ? (
              <>
                <FaCheck size={12} color="#10b981" />
                <span>Copied</span>
              </>
            ) : (
              <>
                <FaCopy size={12} />
                <span>Copy IR</span>
              </>
            )}
          </button>

          <div className="ast-view-toggle">
            <button
              className={`view-toggle-btn ${viewMode === 'formatted' ? 'active' : ''}`}
              onClick={() => setViewMode('formatted')}
            >
              <FaCode size={12} />
              <span>Formatted</span>
            </button>
            <button
              className={`view-toggle-btn ${viewMode === 'table' ? 'active' : ''}`}
              onClick={() => setViewMode('table')}
            >
              <FaTableList size={12} />
              <span>Table</span>
            </button>
          </div>
        </div>
      </div>

      {/* Viewport: Formatted vs Structured Table */}
      {viewMode === 'formatted' ? (
        <div className="ir-code-display">
          <div className="code-line-numbers">
            {formattedText.split('\n').map((_, idx) => (
              <span key={idx} className="line-num">
                {idx + 1}
              </span>
            ))}
          </div>
          <pre className="code-content-pre">{formattedText}</pre>
        </div>
      ) : (
        <div className="table-wrapper ir-table-wrapper">
          <table className="data-table ir-table">
            <thead>
              <tr>
                <th className="col-ir-idx">#</th>
                <th className="col-ir-op">Opcode</th>
                <th className="col-ir-dest">Dest</th>
                <th className="col-ir-arg1">Arg 1</th>
                <th className="col-ir-arg2">Arg 2</th>
                <th className="col-ir-line">Line</th>
              </tr>
            </thead>
            <tbody>
              {filteredInstructions.map((instr, idx) => (
                <tr key={instr.id || idx}>
                  <td className="col-ir-idx text-muted font-mono">{idx + 1}</td>
                  <td className="col-ir-op">
                    <span className={`ir-opcode-pill ${getOpcodeBadgeClass(instr.opcode)}`}>
                      {instr.opcode}
                    </span>
                  </td>
                  <td className="col-ir-dest ir-operand-dest font-mono">{instr.dest || '—'}</td>
                  <td className="col-ir-arg1 font-mono">{instr.arg1 || '—'}</td>
                  <td className="col-ir-arg2 font-mono">{instr.arg2 || '—'}</td>
                  <td className="col-ir-line text-muted">{instr.line || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default IRViewer;
