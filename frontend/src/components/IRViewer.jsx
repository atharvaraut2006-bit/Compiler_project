import React, { useState, useMemo } from 'react';
import { FaCopy, FaCheck, FaCode, FaTableList } from 'react-icons/fa6';

export const IRViewer = ({ ir }) => {
  const [viewMode, setViewMode] = useState('formatted'); // 'formatted' or 'table'
  const [filterText, setFilterText] = useState('');
  const [copied, setCopied] = useState(false);

  // Normalize instructions with guaranteed 1-based index and standard 3AC fields:
  // (operator, arg1, arg2, result)
  const allInstructions = useMemo(() => {
    const raw = ir?.instructions || [];
    if (raw.length > 0) {
      return raw.map((instr, idx) => {
        const opcode = String(instr.opcode || instr.operator || '').trim();
        const formatted = String(instr.formatted || '').trim();
        const isLabel = opcode === 'LABEL' || formatted.endsWith(':');
        let operands = '';

        if (!isLabel) {
          if (opcode && formatted.startsWith(opcode)) {
            operands = formatted.slice(opcode.length).trim();
          } else {
            const firstSpace = formatted.indexOf(' ');
            if (firstSpace !== -1) {
              operands = formatted.slice(firstSpace + 1).trim();
            }
          }
        }

        const resultVal = instr.result !== undefined && instr.result !== null
          ? instr.result
          : (instr.dest !== undefined ? instr.dest : null);

        return {
          id: instr.id || `ir_${idx + 1}`,
          origIndex: idx + 1,
          operator: opcode || (isLabel ? 'LABEL' : 'OP'),
          opcode: opcode || (isLabel ? 'LABEL' : 'OP'),
          formatted: formatted || (isLabel ? `${instr.arg1}:` : `${opcode} ${operands}`.trim()),
          operands,
          isLabel,
          result: resultVal,
          dest: resultVal,
          arg1: instr.arg1,
          arg2: instr.arg2,
          arg3: instr.arg3,
          line: instr.line,
          column: instr.column,
          metadata: instr.metadata || {}
        };
      });
    }

    // Fallback if ir.instructions is not present but formatted string is
    const fmtText = String(ir?.formatted || '').trim();
    if (fmtText) {
      return fmtText.split('\n').filter(l => l.trim().length > 0).map((line, idx) => {
        const trimmed = line.trim();
        const isLabel = trimmed.endsWith(':');
        let opcode = '';
        let operands = '';

        if (isLabel) {
          opcode = 'LABEL';
        } else {
          const firstSpace = trimmed.indexOf(' ');
          if (firstSpace !== -1) {
            opcode = trimmed.slice(0, firstSpace);
            operands = trimmed.slice(firstSpace + 1).trim();
          } else {
            opcode = trimmed;
          }
        }

        return {
          id: `ir_${idx + 1}`,
          origIndex: idx + 1,
          operator: opcode || 'OP',
          opcode: opcode || 'OP',
          formatted: trimmed,
          operands,
          isLabel,
          result: null,
          dest: null,
          arg1: operands,
          arg2: null,
          arg3: null,
          line: idx + 1,
          column: 1,
          metadata: {}
        };
      });
    }

    return [];
  }, [ir]);

  const filteredInstructions = useMemo(() => {
    if (!filterText || !filterText.trim()) return allInstructions;
    const lower = filterText.toLowerCase().trim();
    return allInstructions.filter((instr) => {
      const op = String(instr.operator ?? instr.opcode ?? '').toLowerCase();
      const res = String(instr.result ?? instr.dest ?? '').toLowerCase();
      const a1 = String(instr.arg1 ?? '').toLowerCase();
      const a2 = String(instr.arg2 ?? '').toLowerCase();
      const a3 = String(instr.arg3 ?? '').toLowerCase();
      const fmt = String(instr.formatted ?? '').toLowerCase();
      const ops = String(instr.operands ?? '').toLowerCase();
      const idxStr = String(instr.origIndex);
      return (
        op.includes(lower) ||
        res.includes(lower) ||
        a1.includes(lower) ||
        a2.includes(lower) ||
        a3.includes(lower) ||
        fmt.includes(lower) ||
        ops.includes(lower) ||
        idxStr === lower
      );
    });
  }, [allInstructions, filterText]);

  const handleCopy = () => {
    const textToCopy = filterText.trim()
      ? filteredInstructions.map((i) => i.formatted).join('\n')
      : (ir?.formatted || allInstructions.map((i) => i.formatted).join('\n'));
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getOpcodeBadgeClass = (opcode) => {
    if (['ADD', 'SUB', 'MUL', 'DIV', 'MOD'].includes(opcode)) return 'badge-op-arithmetic';
    if (opcode && String(opcode).startsWith('COMPARE_')) return 'badge-op-compare';
    if (['LOAD', 'STORE', 'LOAD_INDEXED', 'STORE_INDEXED'].includes(opcode)) return 'badge-op-mem';
    if (['JUMP', 'BRANCH', 'LABEL'].includes(opcode)) return 'badge-op-control';
    if (opcode === 'DECLARE') return 'badge-op-decl';
    return 'badge-op-default';
  };

  if (!ir || allInstructions.length === 0) {
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
            onKeyDown={(e) => {
              if (e.key === 'Enter') e.preventDefault();
            }}
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
              title="Formatted 3-Address Code list"
            >
              <FaCode size={12} />
              <span>Structured IR</span>
            </button>
            <button
              className={`view-toggle-btn ${viewMode === 'table' ? 'active' : ''}`}
              onClick={() => setViewMode('table')}
              title="Classical 3-Address Code Quadruples (Operator, Arg 1, Arg 2, Result)"
            >
              <FaTableList size={12} />
              <span>Quadruples Table</span>
            </button>
          </div>
        </div>
      </div>

      {/* Viewport: Structured 3AC Table vs Quadruples Table (Operator, Arg1, Arg2, Result) */}
      {viewMode === 'formatted' ? (
        <div className="table-wrapper ir-formatted-table-wrapper">
          <table className="data-table ir-formatted-table">
            <thead>
              <tr>
                <th className="col-ir-idx">#</th>
                <th className="col-ir-op">Operator</th>
                <th className="col-ir-operands">Operands / Arguments</th>
              </tr>
            </thead>
            <tbody>
              {filteredInstructions.map((instr) => (
                <tr
                  key={instr.id || instr.origIndex}
                  className={`ir-code-row ${instr.isLabel ? 'ir-label-row' : ''}`}
                >
                  <td className="col-ir-idx text-muted font-mono">{instr.origIndex}</td>
                  {instr.isLabel ? (
                    <td colSpan={2} className="col-ir-label-cell">
                      <span className="ir-label-tag">{instr.formatted}</span>
                    </td>
                  ) : (
                    <>
                      <td className="col-ir-op">
                        <span className={`ir-opcode-pill ${getOpcodeBadgeClass(instr.operator || instr.opcode)}`}>
                          {instr.operator || instr.opcode}
                        </span>
                      </td>
                      <td className="col-ir-operands font-mono">
                        {instr.operands || '—'}
                      </td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="table-wrapper ir-table-wrapper">
          <table className="data-table ir-table">
            <thead>
              <tr>
                <th className="col-ir-idx">#</th>
                <th className="col-ir-op">Operator</th>
                <th className="col-ir-arg1">Arg 1</th>
                <th className="col-ir-arg2">Arg 2</th>
                <th className="col-ir-result">Result</th>
                <th className="col-ir-line">Line</th>
              </tr>
            </thead>
            <tbody>
              {filteredInstructions.map((instr) => (
                <tr key={instr.id || instr.origIndex}>
                  <td className="col-ir-idx text-muted font-mono">{instr.origIndex}</td>
                  <td className="col-ir-op">
                    <span className={`ir-opcode-pill ${getOpcodeBadgeClass(instr.operator || instr.opcode)}`}>
                      {instr.operator || instr.opcode}
                    </span>
                  </td>
                  <td className="col-ir-arg1 font-mono">{instr.arg1 || '—'}</td>
                  <td className="col-ir-arg2 font-mono">
                    {instr.arg3 ? `${instr.arg2}, ${instr.arg3}` : (instr.arg2 || '—')}
                  </td>
                  <td className="col-ir-result ir-operand-result font-mono">{instr.result || instr.dest || '—'}</td>
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
