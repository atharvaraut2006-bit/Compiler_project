import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  FaPlay,
  FaPause,
  FaForwardStep,
  FaBackwardStep,
  FaRotateLeft,
  FaRotateRight,
  FaMicrochip,
  FaServer,
  FaCircleCheck,
  FaCircleXmark,
  FaTriangleExclamation,
  FaBolt,
  FaRightLeft,
  FaMagnifyingGlass,
  FaListOl,
  FaCodeCompare,
  FaDatabase
} from 'react-icons/fa6';

export const SimulationViewer = ({ simulation, onReRunSimulation, isCompiling }) => {
  // Playback & Animation State
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState('normal'); // 'slow' (1200ms), 'normal' (600ms), 'fast' (220ms)

  // Filters & Tabs
  const [activeTraceTab, setActiveTraceTab] = useState('pim'); // 'pim' or 'cpu'
  const [processorFilter, setProcessorFilter] = useState('all'); // 'all', 'PIM', 'CPU'
  const [searchTerm, setSearchTerm] = useState('');
  const [stateTab, setStateTab] = useState('variables'); // 'variables', 'arrays', 'output'

  // Ref for auto-scrolling active trace row
  const activeRowRef = useRef(null);

  const { cpu, pim, comparison } = simulation || {};
  const verdict = comparison?.verdict || 'UNKNOWN';
  const isMatch = comparison?.is_match;
  const summary = comparison?.summary || {};
  const discrepancies = comparison?.discrepancies || [];

  // Active trace selection
  const rawTrace = useMemo(() => {
    return activeTraceTab === 'pim' ? (pim?.execution_trace || []) : (cpu?.execution_trace || []);
  }, [activeTraceTab, pim, cpu]);

  const totalSteps = rawTrace.length;

  // Reset playback when simulation data or trace tab changes
  useEffect(() => {
    setIsPlaying(false);
    setCurrentStepIndex(0);
  }, [simulation, activeTraceTab]);

  // Animation Playback Timer
  useEffect(() => {
    if (!isPlaying) return;

    if (currentStepIndex >= totalSteps - 1) {
      setIsPlaying(false);
      return;
    }

    const intervalMs = speed === 'slow' ? 1200 : speed === 'fast' ? 220 : 600;
    const timerId = setInterval(() => {
      setCurrentStepIndex((prev) => {
        if (prev >= totalSteps - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, intervalMs);

    return () => clearInterval(timerId);
  }, [isPlaying, currentStepIndex, totalSteps, speed]);

  // Current Step Data
  const currentStep = rawTrace[currentStepIndex] || null;
  const isCpuActive = currentStep?.processor === 'CPU';
  const isPimActive = currentStep?.processor === 'PIM';
  const isCompleted = totalSteps > 0 && currentStepIndex === totalSteps - 1;

  // Filtered trace for table
  const filteredTrace = useMemo(() => {
    return rawTrace.filter((step) => {
      if (activeTraceTab === 'pim') {
        if (processorFilter === 'PIM' && step.processor !== 'PIM') return false;
        if (processorFilter === 'CPU' && step.processor !== 'CPU') return false;
      }
      if (searchTerm.trim()) {
        const term = searchTerm.toLowerCase();
        const text = `${step.step} ${step.processor || ''} ${step.mapped_instruction || step.opcode || ''} ${step.dest || ''} ${step.arg1 || ''} ${step.arg2 || ''} ${step.operation_desc || ''} ${step.result_value ?? ''} ${step.fallback_reason || ''}`.toLowerCase();
        return text.includes(term);
      }
      return true;
    });
  }, [rawTrace, activeTraceTab, processorFilter, searchTerm]);

  // Completed operations history for CPU and PIM panels
  const completedCpuOps = useMemo(() => {
    return rawTrace
      .slice(0, currentStepIndex + 1)
      .filter((s) => s.processor === 'CPU')
      .slice(-4)
      .reverse();
  }, [rawTrace, currentStepIndex]);

  const completedPimOps = useMemo(() => {
    return rawTrace
      .slice(0, currentStepIndex + 1)
      .filter((s) => s.processor === 'PIM')
      .slice(-4)
      .reverse();
  }, [rawTrace, currentStepIndex]);

  // Variable & Array snapshots at current step
  const currentVariables = currentStep?.variables_snapshot || {};
  const currentArrays = currentStep?.arrays_snapshot || {};

  // Handlers for playback controls
  const handlePlayPause = () => {
    if (totalSteps === 0) return;
    if (currentStepIndex >= totalSteps - 1) {
      setCurrentStepIndex(0);
      setIsPlaying(true);
    } else {
      setIsPlaying(!isPlaying);
    }
  };

  const handleNextStep = () => {
    setIsPlaying(false);
    if (currentStepIndex < totalSteps - 1) {
      setCurrentStepIndex(currentStepIndex + 1);
    }
  };

  const handlePrevStep = () => {
    setIsPlaying(false);
    if (currentStepIndex > 0) {
      setCurrentStepIndex(currentStepIndex - 1);
    }
  };

  const handleRestart = () => {
    setIsPlaying(false);
    setCurrentStepIndex(0);
  };

  const handleJumpToStep = (stepNumber) => {
    setIsPlaying(false);
    const idx = rawTrace.findIndex((s) => s.step === stepNumber);
    if (idx !== -1) {
      setCurrentStepIndex(idx);
    }
  };

  if (!simulation || !simulation.comparison) {
    return (
      <div className="empty-tab-state">
        <p>No simulation results available. Click <strong>Compile & Analyze</strong> to execute CPU and PIM simulators.</p>
      </div>
    );
  }

  // PIM In-situ vs Fallback calculation
  const pimSteps = pim?.pim_steps || 0;
  const pimCpuFallback = pim?.cpu_steps || 0;
  const pimTotalSteps = pim?.total_steps || 0;
  const insituPercentage = pimTotalSteps > 0 ? ((pimSteps / pimTotalSteps) * 100).toFixed(1) : 0;

  // Comparison keys
  const cpuVars = cpu?.final_variables || {};
  const pimVars = pim?.final_variables || {};
  const allVarNames = Array.from(new Set([...Object.keys(cpuVars), ...Object.keys(pimVars)])).sort();

  const cpuArrs = cpu?.final_arrays || {};
  const pimArrs = pim?.final_arrays || {};
  const allArrNames = Array.from(new Set([...Object.keys(cpuArrs), ...Object.keys(pimArrs)])).sort();

  const progressPercent = totalSteps > 0 ? Math.round(((currentStepIndex + 1) / totalSteps) * 100) : 0;

  return (
    <div className="simulation-viewer-container">
      {/* 1. Header & Interactive Simulation Controls */}
      <div className="sim-panel sim-controls-card">
        <div className="sim-controls-header">
          <div>
            <h2 className="sim-main-title">CPU vs PIM Execution Simulator</h2>
            <p className="sim-subtitle">
              Visualize how your compiled program executes across CPU and Processing-in-Memory operations.
            </p>
          </div>
          <div className="sim-header-actions">
            {onReRunSimulation && (
              <button
                className="btn btn-secondary btn-sm"
                onClick={onReRunSimulation}
                disabled={isCompiling}
                title="Re-run simulation through backend"
              >
                <FaRotateRight className={isCompiling ? 'spin' : ''} /> Run Simulation
              </button>
            )}
          </div>
        </div>

        {/* Playback Controls Toolbar */}
        <div className="sim-toolbar-row">
          <div className="sim-playback-btn-group">
            <button
              className="ctrl-btn"
              onClick={handleRestart}
              disabled={totalSteps === 0 || currentStepIndex === 0}
              title="Restart Simulation (Step 1)"
            >
              <FaRotateLeft />
              <span>Restart</span>
            </button>
            <button
              className="ctrl-btn"
              onClick={handlePrevStep}
              disabled={totalSteps === 0 || currentStepIndex === 0}
              title="Previous Step"
            >
              <FaBackwardStep />
              <span>Prev</span>
            </button>
            <button
              className={`ctrl-btn ctrl-btn-primary ${isPlaying ? 'btn-playing' : ''}`}
              onClick={handlePlayPause}
              disabled={totalSteps === 0}
              title={isPlaying ? 'Pause Animation' : 'Play Step-by-Step Animation'}
            >
              {isPlaying ? <FaPause /> : <FaPlay />}
              <span>{isPlaying ? 'Pause' : isCompleted ? 'Replay' : 'Play'}</span>
            </button>
            <button
              className="ctrl-btn"
              onClick={handleNextStep}
              disabled={totalSteps === 0 || currentStepIndex >= totalSteps - 1}
              title="Next Step"
            >
              <FaForwardStep />
              <span>Next</span>
            </button>
          </div>

          {/* Speed Selector */}
          <div className="sim-speed-selector">
            <span className="speed-label">Speed:</span>
            <div className="speed-btn-group">
              <button
                className={`speed-btn ${speed === 'slow' ? 'active' : ''}`}
                onClick={() => setSpeed('slow')}
              >
                Slow
              </button>
              <button
                className={`speed-btn ${speed === 'normal' ? 'active' : ''}`}
                onClick={() => setSpeed('normal')}
              >
                Normal
              </button>
              <button
                className={`speed-btn ${speed === 'fast' ? 'active' : ''}`}
                onClick={() => setSpeed('fast')}
              >
                Fast
              </button>
            </div>
          </div>

          {/* Step Counter Indicator */}
          <div className="sim-step-indicator">
            <span className="step-counter-text">
              Step <strong>{totalSteps > 0 ? currentStepIndex + 1 : 0}</strong> of <strong>{totalSteps}</strong>
            </span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="sim-progress-track">
          <div
            className="sim-progress-bar"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* 2. Current Instruction Details Card */}
      {currentStep && (
        <div className="sim-panel current-instruction-card">
          <div className="instruction-card-header">
            <div className="instruction-title-group">
              <span className="step-num-pill font-mono">Step #{currentStep.step}</span>
              <span className={`processor-pill ${isPimActive ? 'pill-pim' : 'pill-cpu'}`}>
                {isPimActive ? (
                  <><FaMicrochip className="ico" /> PIM ALU (In-Situ)</>
                ) : (
                  <><FaServer className="ico" /> CPU Core (Host)</>
                )}
              </span>
              <span className="status-pill status-success">
                <FaCircleCheck className="ico" /> {currentStep.status || 'SUCCESS'}
              </span>
            </div>
            <div className="raw-ir-code font-mono">
              {currentStep.formatted_instruction || currentStep.mapped_instruction}
            </div>
          </div>

          <div className="instruction-card-body">
            <div className="inst-meta-grid">
              <div className="inst-meta-item">
                <span className="inst-meta-label">Operation Description</span>
                <span className="inst-meta-val font-mono">{currentStep.operation_desc}</span>
              </div>
              <div className="inst-meta-item">
                <span className="inst-meta-label">Input Operands</span>
                <span className="inst-meta-val font-mono">
                  {currentStep.arg1 !== undefined && currentStep.arg1 !== null ? (
                    <span>
                      {currentStep.arg1}
                      {currentStep.arg1_val !== undefined && currentStep.arg1_val !== null ? ` = ${currentStep.arg1_val}` : ''}
                    </span>
                  ) : '—'}
                  {currentStep.arg2 !== undefined && currentStep.arg2 !== null ? (
                    <span>
                      {', '}
                      {currentStep.arg2}
                      {currentStep.arg2_val !== undefined && currentStep.arg2_val !== null ? ` = ${currentStep.arg2_val}` : ''}
                    </span>
                  ) : ''}
                </span>
              </div>
              <div className="inst-meta-item">
                <span className="inst-meta-label">Result Produced</span>
                <span className="inst-meta-val font-mono font-bold text-primary">
                  {currentStep.result_value !== undefined && currentStep.result_value !== null ? currentStep.result_value : '—'}
                </span>
              </div>
              <div className="inst-meta-item">
                <span className="inst-meta-label">State Update</span>
                <span className="inst-meta-val font-mono">
                  {currentStep.updated_var ? (
                    <span className="update-var-highlight">Variable '{currentStep.updated_var}' = {currentStep.result_value}</span>
                  ) : currentStep.read_array ? (
                    <span className="update-arr-read">Read {currentStep.read_array.name}[{currentStep.read_array.index}] = {currentStep.read_array.value}</span>
                  ) : currentStep.updated_array ? (
                    <span className="update-arr-write">Write {currentStep.updated_array.name}[{currentStep.updated_array.index}] = {currentStep.updated_array.value}</span>
                  ) : (
                    <span className="text-muted">Control-flow / No state write</span>
                  )}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 3. Inter-Processor Event Callout (Fallback or Data Movement) */}
      {currentStep?.is_fallback && (
        <div className="sim-event-callout callout-fallback">
          <div className="event-badge">
            <FaBolt className="ico" /> CPU Fallback Event
          </div>
          <div className="event-message">
            {currentStep.fallback_reason || 'Instruction executed on host CPU core according to mapping policy.'}
          </div>
        </div>
      )}
      {currentStep?.is_transfer && (
        <div className="sim-event-callout callout-transfer">
          <div className="event-badge">
            <FaRightLeft className="ico" /> Near-Memory In-Situ Access
          </div>
          <div className="event-message">
            {currentStep.transfer_desc || 'Direct near-memory row buffer access without traversing system bus.'}
          </div>
        </div>
      )}

      {/* 4. Dual Processor Panels: CPU vs PIM (Side-by-Side) */}
      <div className="sim-processors-split">
        {/* CPU Simulator Panel */}
        <div className={`sim-unit-card ${isCpuActive ? 'unit-card-active active-cpu' : 'unit-card-idle'}`}>
          <div className="unit-header">
            <div className="unit-title-row">
              <FaServer className="unit-icon icon-cpu" />
              <div>
                <h3 className="unit-title">CPU Simulator</h3>
                <span className="unit-arch-badge">Host Processor (von Neumann Core)</span>
              </div>
            </div>
            <div className="unit-status-indicator">
              {isCompleted ? (
                <span className="status-badge status-completed">✓ COMPLETED</span>
              ) : isCpuActive ? (
                <span className="status-badge status-executing-cpu">● EXECUTING</span>
              ) : (
                <span className="status-badge status-idle">○ IDLE (PIM Active)</span>
              )}
            </div>
          </div>

          <div className="unit-body">
            {/* Host Stack Variables View */}
            <div className="unit-section">
              <div className="unit-section-title">Host Stack Variables</div>
              <div className="variable-tiles-grid">
                {Object.keys(currentVariables).length === 0 ? (
                  <div className="text-muted text-sm">No variables allocated yet.</div>
                ) : (
                  Object.entries(currentVariables).map(([name, val]) => {
                    const isUpdatedNow = currentStep?.updated_var === name;
                    return (
                      <div
                        key={name}
                        className={`var-tile ${isUpdatedNow ? 'var-tile-updated' : ''}`}
                      >
                        <span className="var-name font-mono">{name}</span>
                        <span className="var-value font-mono font-bold">{val}</span>
                        {isUpdatedNow && <span className="var-badge">Updated</span>}
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Completed Operations Trace for CPU */}
            <div className="unit-section">
              <div className="unit-section-title">Completed CPU Operations</div>
              <div className="unit-ops-list font-mono">
                {completedCpuOps.length === 0 ? (
                  <div className="text-muted text-sm">No CPU operations executed yet.</div>
                ) : (
                  completedCpuOps.map((op) => (
                    <div
                      key={op.step}
                      className={`unit-op-row ${op.step === currentStep?.step ? 'op-current' : ''}`}
                    >
                      <span className="op-step text-muted">#{op.step}</span>
                      <span className="op-instr">{op.mapped_instruction || op.opcode}</span>
                      <span className="op-summary text-truncate">{op.operation_desc}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>

        {/* PIM Simulator Panel */}
        <div className={`sim-unit-card ${isPimActive ? 'unit-card-active active-pim' : 'unit-card-idle'}`}>
          <div className="unit-header">
            <div className="unit-title-row">
              <FaMicrochip className="unit-icon icon-pim" />
              <div>
                <h3 className="unit-title">PIM Simulator</h3>
                <span className="unit-arch-badge">Near-Memory Accelerator (DRAM Bank ALU)</span>
              </div>
            </div>
            <div className="unit-status-indicator">
              {isCompleted ? (
                <span className="status-badge status-completed">✓ COMPLETED</span>
              ) : isPimActive ? (
                <span className="status-badge status-executing-pim">● IN-SITU PROCESSING</span>
              ) : (
                <span className="status-badge status-idle">○ IDLE (CPU Active)</span>
              )}
            </div>
          </div>

          <div className="unit-body">
            {/* DRAM Bank Arrays View */}
            <div className="unit-section">
              <div className="unit-section-title">
                <FaDatabase className="sec-ico" /> DRAM Bank Array Partitions
              </div>
              {Object.keys(currentArrays).length === 0 ? (
                <div className="text-muted text-sm">No DRAM arrays initialized.</div>
              ) : (
                Object.entries(currentArrays).map(([arrName, arrElements]) => (
                  <div key={arrName} className="dram-array-container">
                    <div className="dram-array-name font-mono">
                      <strong>{arrName}</strong> [{arrElements.length}]
                    </div>
                    <div className="dram-cells-wrapper">
                      <table className="dram-memory-table">
                        <thead>
                          <tr>
                            <th>Index</th>
                            <th style={{ textAlign: 'right' }}>Array Value</th>
                            <th>Bank Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {arrElements.map((elem, idx) => {
                            const isBeingRead =
                              currentStep?.read_array?.name === arrName &&
                              currentStep?.read_array?.index === idx;
                            const isBeingWritten =
                              currentStep?.updated_array?.name === arrName &&
                              currentStep?.updated_array?.index === idx;

                            return (
                              <tr
                                key={idx}
                                className={isBeingRead ? 'row-dram-read' : isBeingWritten ? 'row-dram-write' : ''}
                              >
                                <td className="font-mono text-muted">[{idx}]</td>
                                <td className="font-mono font-bold" style={{ textAlign: 'right' }}>
                                  {elem}
                                </td>
                                <td>
                                  {isBeingRead ? (
                                    <span className="dram-status-badge badge-read">● In-situ Read</span>
                                  ) : isBeingWritten ? (
                                    <span className="dram-status-badge badge-write">● Bank Write</span>
                                  ) : (
                                    <span className="text-muted text-xs">Resident</span>
                                  )}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Completed Operations Trace for PIM */}
            <div className="unit-section">
              <div className="unit-section-title">Completed PIM Operations</div>
              <div className="unit-ops-list font-mono">
                {completedPimOps.length === 0 ? (
                  <div className="text-muted text-sm">No PIM in-situ operations executed yet.</div>
                ) : (
                  completedPimOps.map((op) => (
                    <div
                      key={op.step}
                      className={`unit-op-row ${op.step === currentStep?.step ? 'op-current' : ''}`}
                    >
                      <span className="op-step text-muted">#{op.step}</span>
                      <span className="op-instr text-pim font-bold">{op.mapped_instruction}</span>
                      <span className="op-summary text-truncate">{op.operation_desc}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 5. Dynamic Execution Trace Table (Interactive Timeline) */}
      <div className="sim-panel trace-panel">
        <div className="sim-panel-header">
          <div className="panel-title-with-pill">
            <span className="sim-panel-title">Dynamic Execution Trace Timeline</span>
            <span className="badge-pill pill-neutral">{filteredTrace.length} Steps</span>
          </div>

          <div className="trace-controls">
            {/* Trace Switcher */}
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

            {/* Filter chips */}
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

            {/* Search */}
            <div className="trace-search-box">
              <FaMagnifyingGlass className="search-icon" />
              <input
                type="text"
                placeholder="Search trace steps..."
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
                  <th style={{ width: '13%' }}>Processor</th>
                  <th style={{ width: '22%' }}>Instruction</th>
                  <th style={{ width: '37%' }}>Operation & Execution Semantics</th>
                  <th style={{ width: '10%' }}>Result</th>
                  <th style={{ width: '10%' }}>Action</th>
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
                    const isCurrent = step.step === currentStep?.step;

                    return (
                      <tr
                        key={step.step}
                        ref={isCurrent ? activeRowRef : null}
                        className={`${isCurrent ? 'active-step-row' : ''} ${isPim ? 'trace-row-pim' : 'trace-row-cpu'}`}
                        onClick={() => handleJumpToStep(step.step)}
                        style={{ cursor: 'pointer' }}
                        title="Click to jump animation to this step"
                      >
                        <td className="font-mono text-muted">
                          {isCurrent ? <strong className="text-primary">▶ #{step.step}</strong> : `#${step.step}`}
                        </td>
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
                          <button
                            className="btn btn-ghost btn-xs"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleJumpToStep(step.step);
                            }}
                          >
                            Jump
                          </button>
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

      {/* 6. Final State Equivalence Inspector & Verdict Banner */}
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
                ? 'CPU Host Execution and Mixed PIM Execution produced 100% semantically identical final states.'
                : verdict === 'FAIL'
                ? 'Semantic divergence detected between CPU and PIM simulators.'
                : 'Execution halted due to a runtime fault or boundary violation.'}
            </span>
          </div>
          <div className="verdict-reason">{comparison.reason}</div>
        </div>
      </div>

      {/* Key Metrics Row */}
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

      {/* Discrepancies Callout if any */}
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

      {/* Final State Equivalence Inspector Panel */}
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
    </div>
  );
};

export default SimulationViewer;
