import React, { useState, useMemo } from 'react';
import {
  FaCircleCheck,
  FaCircleXmark,
  FaTriangleExclamation,
  FaMicrochip,
  FaServer,
  FaPlay,
  FaListOl,
  FaCodeCompare,
  FaMagnifyingGlass,
  FaArrowsRotate
} from 'react-icons/fa6';

export const SimulationViewer = ({ simulation }) => {
  const [activeTraceTab, setActiveTraceTab] = useState('pim'); // 'pim' or 'cpu'
  const [processorFilter, setProcessorFilter] = useState('all'); // 'all', 'PIM', 'CPU'
  const [searchTerm, setSearchTerm] = useState('');
  const [stateTab, setStateTab] = useState('variables'); // 'variables', 'arrays', 'output'

  if (!simulation || !simulation.comparison) {
    return (
      <div className="empty-tab-state">
        <p>No simulation results available. Click <strong>Compile & Analyze</strong> to execute CPU and PIM simulators.</p>
      </div>
    );
  }

  const { cpu, pim, comparison } = simulation;
  const verdict = comparison.verdict || 'UNKNOWN';
  const isMatch = comparison.is_match;
  const summary = comparison.summary || {};
  const discrepancies = comparison.discrepancies || [];

  // PIM In-situ vs Fallback calculation
  const pimSteps = pim?.pim_steps || 0;
  const pimCpuFallback = pim?.cpu_steps || 0;
  const pimTotalSteps = pim?.total_steps || 0;
  const insituPercentage = pimTotalSteps > 0 ? ((pimSteps / pimTotalSteps) * 100).toFixed(1) : 0;

  // Active trace selection
  const rawTrace = activeTraceTab === 'pim' ? (pim?.execution_trace || []) : (cpu?.execution_trace || []);

  const filteredTrace = useMemo(() => {
    return rawTrace.filter((step) => {
      // Processor filter (for PIM trace)
      if (activeTraceTab === 'pim') {
        if (processorFilter === 'PIM' && step.processor !== 'PIM') return false;
        if (processorFilter === 'CPU' && step.processor !== 'CPU') return false;
      }

      // Search term
      if (searchTerm.trim()) {
        const term = searchTerm.toLowerCase();
        const text = `${step.step} ${step.processor || ''} ${step.mapped_instruction || step.opcode || ''} ${step.dest || ''} ${step.arg1 || ''} ${step.arg2 || ''} ${step.operation_desc || ''} ${step.result_value ?? ''} ${step.fallback_reason || ''}`.toLowerCase();
        return text.includes(term);
      }
      return true;
    });
  }, [rawTrace, activeTraceTab, processorFilter, searchTerm]);

  // Variables comparison keys
  const cpuVars = cpu?.final_variables || {};
  const pimVars = pim?.final_variables || {};
  const allVarNames = Array.from(new Set([...Object.keys(cpuVars), ...Object.keys(pimVars)])).sort();

  // Arrays comparison keys
  const cpuArrs = cpu?.final_arrays || {};
  const pimArrs = pim?.final_arrays || {};
  const allArrNames = Array.from(new Set([...Object.keys(cpuArrs), ...Object.keys(pimArrs)])).sort();

  return (
    <div className="simulation-viewer-container">
      {/* 1. Hero Verdict & Executive Summary */}
      <div className={`sim-verdict-banner ${verdict === 'PASS' ? 'banner-pass' : verdict === 'FAIL' ? 'banner-fail' : 'banner-error'}`}>
        <div className="verdict-icon-column">
          {verdict === 'PASS' ? (
            <FaCircleCheck className="verdict-icon icon-pass" />
          ) : verdict === 'FAIL' ? (
            <FaCircleXmark className="verdict-icon icon-fail" />
          ) : (
            <FaTriangleExclamation className="verdict-icon icon-error" />
          )}
        </div>
        <div className="verdict-details-column">
          <div className="verdict-title-row">
            <span className={`sim-verdict-badge badge-${verdict.toLowerCase()}`}>
              {verdict === 'PASS' ? '✓ VERIFIED: PASS' : verdict === 'FAIL' ? '✗ DIVERGENCE: FAIL' : '⚠ FAULT: ERROR'}
            </span>
            <span className="verdict-subtitle">
              {verdict === 'PASS'
                ? 'CPU Host Execution and Mixed PIM Execution produced 100% semantically identical states.'
                : verdict === 'FAIL'
                ? 'Semantic divergence detected between CPU and PIM simulators.'
                : 'Execution halted due to a runtime fault or boundary violation.'}
            </span>
          </div>
          <div className="verdict-reason">{comparison.reason}</div>
        </div>
      </div>

      {/* 2. Key Metrics Row */}
      <div className="sim-metrics-grid">
        <div className="sim-metric-card">
          <div className="metric-header">
            <span className="metric-label">Return Value Equivalence</span>
            <FaCodeCompare className="metric-icon" />
          </div>
          <div className="metric-val-row">
            <div className="val-block">
              <span className="val-sub">CPU</span>
              <span className="val-number">{cpu?.return_value ?? 'N/A'}</span>
            </div>
            <div className="val-vs">vs</div>
            <div className="val-block">
              <span className="val-sub">PIM</span>
              <span className="val-number">{pim?.return_value ?? 'N/A'}</span>
            </div>
          </div>
          <div className="metric-footer">
            {summary.return_value_match ? (
              <span className="text-success">✓ Return values identical</span>
            ) : (
              <span className="text-danger">✗ Return value mismatch</span>
            )}
          </div>
        </div>

        <div className="sim-metric-card">
          <div className="metric-header">
            <span className="metric-label">PIM Offloading Ratio</span>
            <FaMicrochip className="metric-icon" />
          </div>
          <div className="metric-val-row">
            <div className="val-block">
              <span className="val-sub">In-Situ ALU</span>
              <span className="val-number text-pim">{pimSteps}</span>
            </div>
            <div className="val-vs">/</div>
            <div className="val-block">
              <span className="val-sub">CPU Fallback</span>
              <span className="val-number text-cpu">{pimCpuFallback}</span>
            </div>
          </div>
          <div className="metric-footer">
            <span className="text-muted">{insituPercentage}% of dynamic operations executed in-memory</span>
          </div>
        </div>

        <div className="sim-metric-card">
          <div className="metric-header">
            <span className="metric-label">Simulated Dynamic Steps</span>
            <FaListOl className="metric-icon" />
          </div>
          <div className="metric-val-row">
            <div className="val-block">
              <span className="val-sub">CPU Simulator</span>
              <span className="val-number">{cpu?.total_steps ?? 0}</span>
            </div>
            <div className="val-vs">vs</div>
            <div className="val-block">
              <span className="val-sub">PIM Simulator</span>
              <span className="val-number">{pimTotalSteps}</span>
            </div>
          </div>
          <div className="metric-footer">
            <span className="text-muted">Total instruction cycles executed</span>
          </div>
        </div>
      </div>

      {/* 3. Discrepancies Callout if any */}
      {discrepancies.length > 0 && (
        <div className="sim-discrepancy-box">
          <div className="discrepancy-title">Detected Discrepancies ({discrepancies.length}):</div>
          <ul className="discrepancy-list">
            {discrepancies.map((d, i) => (
              <li key={i}>{d}</li>
            ))}
          </ul>
        </div>
      )}

      {/* 4. Semantic State Equivalence Inspector */}
      <div className="sim-panel state-comparison-panel">
        <div className="sim-panel-header">
          <div className="panel-title-with-pill">
            <span className="sim-panel-title">Final State Equivalence Inspector</span>
            <span className={`badge-pill ${isMatch ? 'pill-success' : 'pill-error'}`}>
              {isMatch ? 'All States Match' : 'Differences Found'}
            </span>
          </div>
          <div className="state-tab-pills">
            <button
              className={`pill-btn ${stateTab === 'variables' ? 'active' : ''}`}
              onClick={() => setStateTab('variables')}
            >
              Scalar Variables ({allVarNames.length})
            </button>
            <button
              className={`pill-btn ${stateTab === 'arrays' ? 'active' : ''}`}
              onClick={() => setStateTab('arrays')}
            >
              DRAM Arrays ({allArrNames.length})
            </button>
            <button
              className={`pill-btn ${stateTab === 'output' ? 'active' : ''}`}
              onClick={() => setStateTab('output')}
            >
              Standard Output ({(cpu?.output || []).length})
            </button>
          </div>
        </div>

        <div className="sim-panel-body">
          {stateTab === 'variables' && (
            <div className="table-responsive-wrapper">
              <table className="sim-table">
                <thead>
                  <tr>
                    <th style={{ width: '25%' }}>Variable Name</th>
                    <th style={{ width: '30%' }}>CPU Final Value</th>
                    <th style={{ width: '30%' }}>PIM Final Value</th>
                    <th style={{ width: '15%' }}>Equivalence</th>
                  </tr>
                </thead>
                <tbody>
                  {allVarNames.length === 0 ? (
                    <tr>
                      <td colSpan="4" className="text-center text-muted">No scalar variables tracked.</td>
                    </tr>
                  ) : (
                    allVarNames.map((name) => {
                      const cv = cpuVars[name];
                      const pv = pimVars[name];
                      const match = cv === pv;
                      return (
                        <tr key={name} className={match ? '' : 'row-diverged'}>
                          <td className="code-cell font-bold">{name}</td>
                          <td className="code-cell">{cv !== undefined ? String(cv) : '<undefined>'}</td>
                          <td className="code-cell">{pv !== undefined ? String(pv) : '<undefined>'}</td>
                          <td>
                            {match ? (
                              <span className="sim-match-badge match-yes">✓ Match</span>
                            ) : (
                              <span className="sim-match-badge match-no">✗ Diff</span>
                            )}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          )}

          {stateTab === 'arrays' && (
            <div className="table-responsive-wrapper">
              <table className="sim-table">
                <thead>
                  <tr>
                    <th style={{ width: '20%' }}>Array Identifier</th>
                    <th style={{ width: '35%' }}>CPU Host Memory Buffer</th>
                    <th style={{ width: '35%' }}>PIM DRAM Bank Contents</th>
                    <th style={{ width: '10%' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {allArrNames.length === 0 ? (
                    <tr>
                      <td colSpan="4" className="text-center text-muted">No array buffers allocated in DRAM.</td>
                    </tr>
                  ) : (
                    allArrNames.map((name) => {
                      const ca = cpuArrs[name] || [];
                      const pa = pimArrs[name] || [];
                      const match = JSON.stringify(ca) === JSON.stringify(pa);
                      return (
                        <tr key={name} className={match ? '' : 'row-diverged'}>
                          <td className="code-cell font-bold">{name}</td>
                          <td className="code-cell font-mono">[{ca.join(', ')}]</td>
                          <td className="code-cell font-mono">[{pa.join(', ')}]</td>
                          <td>
                            {match ? (
                              <span className="sim-match-badge match-yes">✓ Match</span>
                            ) : (
                              <span className="sim-match-badge match-no">✗ Diff</span>
                            )}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          )}

          {stateTab === 'output' && (
            <div className="sim-output-grid">
              <div className="sim-output-column">
                <div className="sim-sub-header">CPU Standard Output</div>
                <div className="sim-console-view">
                  {(cpu?.output || []).length === 0 ? (
                    <div className="console-empty">No output emitted.</div>
                  ) : (
                    cpu.output.map((line, idx) => (
                      <div key={idx} className="console-line">{line}</div>
                    ))
                  )}
                </div>
              </div>
              <div className="sim-output-column">
                <div className="sim-sub-header">PIM Execution Output</div>
                <div className="sim-console-view">
                  {(pim?.output || []).length === 0 ? (
                    <div className="console-empty">No output emitted.</div>
                  ) : (
                    pim.output.map((line, idx) => (
                      <div key={idx} className="console-line">{line}</div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 5. Dynamic Execution Trace Viewer */}
      <div className="sim-panel trace-panel">
        <div className="sim-panel-header">
          <div className="panel-title-with-pill">
            <span className="sim-panel-title">Dynamic Execution Trace</span>
            <span className="badge-pill pill-neutral">{filteredTrace.length} Steps</span>
          </div>

          <div className="trace-controls">
            {/* Trace Source Switcher */}
            <div className="tab-pill-toggle">
              <button
                className={`pill-toggle-btn ${activeTraceTab === 'pim' ? 'active' : ''}`}
                onClick={() => { setActiveTraceTab('pim'); setProcessorFilter('all'); }}
              >
                <FaMicrochip className="btn-icon" /> Mixed PIM Trace ({pim?.total_steps || 0})
              </button>
              <button
                className={`pill-toggle-btn ${activeTraceTab === 'cpu' ? 'active' : ''}`}
                onClick={() => { setActiveTraceTab('cpu'); setProcessorFilter('all'); }}
              >
                <FaServer className="btn-icon" /> Pure CPU Trace ({cpu?.total_steps || 0})
              </button>
            </div>

            {/* Processor Filter (for Mixed Trace) */}
            {activeTraceTab === 'pim' && (
              <div className="filter-chip-group">
                <button
                  className={`chip ${processorFilter === 'all' ? 'active' : ''}`}
                  onClick={() => setProcessorFilter('all')}
                >
                  All ({pimTotalSteps})
                </button>
                <button
                  className={`chip chip-pim ${processorFilter === 'PIM' ? 'active' : ''}`}
                  onClick={() => setProcessorFilter('PIM')}
                >
                  PIM In-Situ ({pimSteps})
                </button>
                <button
                  className={`chip chip-cpu ${processorFilter === 'CPU' ? 'active' : ''}`}
                  onClick={() => setProcessorFilter('CPU')}
                >
                  CPU Fallback ({pimCpuFallback})
                </button>
              </div>
            )}

            {/* Search Input */}
            <div className="trace-search-box">
              <FaMagnifyingGlass className="search-icon" />
              <input
                type="text"
                placeholder="Search trace steps, opcodes, operands..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
        </div>

        <div className="sim-panel-body trace-table-body">
          <div className="table-responsive-wrapper">
            <table className="sim-table trace-table">
              <thead>
                <tr>
                  <th style={{ width: '8%' }}>Step</th>
                  <th style={{ width: '12%' }}>Processor</th>
                  <th style={{ width: '22%' }}>Instruction</th>
                  <th style={{ width: '38%' }}>Operation & Execution Semantics</th>
                  <th style={{ width: '10%' }}>Result</th>
                  <th style={{ width: '10%' }}>Snapshot</th>
                </tr>
              </thead>
              <tbody>
                {filteredTrace.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="text-center text-muted">
                      No trace steps match current filters.
                    </td>
                  </tr>
                ) : (
                  filteredTrace.map((step) => {
                    const isPim = step.processor === 'PIM';
                    return (
                      <tr key={step.step} className={isPim ? 'trace-row-pim' : 'trace-row-cpu'}>
                        <td className="font-mono text-muted">#{step.step}</td>
                        <td>
                          {isPim ? (
                            <span className="proc-badge proc-pim">
                              <FaMicrochip className="badge-ico" /> PIM ALU
                            </span>
                          ) : (
                            <span className="proc-badge proc-cpu">
                              <FaServer className="badge-ico" /> CPU Core
                            </span>
                          )}
                        </td>
                        <td className="code-cell font-mono">
                          <span className="op-highlight">{step.mapped_instruction || step.opcode}</span>{' '}
                          {[step.dest, step.arg1, step.arg2].filter(Boolean).join(', ')}
                        </td>
                        <td className="desc-cell">
                          <div className="op-desc-text">{step.operation_desc}</div>
                          {step.fallback_reason && (
                            <div className="fallback-note" title={step.fallback_reason}>
                              Fallback: {step.fallback_reason}
                            </div>
                          )}
                        </td>
                        <td className="code-cell font-mono">
                          {step.result_value !== undefined && step.result_value !== null ? (
                            <span className="result-val">{step.result_value}</span>
                          ) : (
                            <span className="text-muted">-</span>
                          )}
                        </td>
                        <td>
                          {step.variables_snapshot && Object.keys(step.variables_snapshot).length > 0 ? (
                            <span
                              className="snapshot-pill"
                              title={Object.entries(step.variables_snapshot)
                                .map(([k, v]) => `${k}=${v}`)
                                .join(', ')}
                            >
                              {Object.entries(step.variables_snapshot)
                                .slice(0, 2)
                                .map(([k, v]) => `${k}:${v}`)
                                .join(' ')}
                            </span>
                          ) : (
                            <span className="text-muted">-</span>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimulationViewer;
