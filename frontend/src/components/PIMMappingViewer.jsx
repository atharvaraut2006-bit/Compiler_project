import React, { useState, useEffect, useMemo } from 'react';
import {
  FaMicrochip,
  FaServer,
  FaListCheck,
  FaBolt,
  FaScaleBalanced,
  FaChevronDown,
  FaChevronUp,
  FaCircleInfo,
  FaCircleCheck,
  FaCircleXmark,
  FaTriangleExclamation,
  FaRotateLeft,
  FaTable,
  FaChartColumn,
  FaChartPie,
  FaArrowTrendUp,
  FaMemory,
  FaSliders
} from 'react-icons/fa6';
import { evaluatePerformance } from '../api/client';

/**
 * Interactive SVG Donut / Pie Chart for Cost Component Breakdown
 * Clearly displays Compute (Blue), Transfer (Orange), Layout (Purple), and Sync (Green)
 * with precise 1-decimal float values and exact percentages.
 */
const DonutCostChart = ({ item }) => {
  const [hoveredSlice, setHoveredSlice] = useState(null);
  const total = item.total || 1.0;
  const slices = [
    { key: 'compute', label: 'Compute', value: item.compute, color: '#2563eb' },
    { key: 'transfer', label: 'Bus Transfer', value: item.transfer, color: '#f59e0b' },
    { key: 'layout', label: 'Layout Reorg', value: item.layout, color: '#8b5cf6' },
    { key: 'sync', label: 'Sync Overhead', value: item.synchronization, color: '#10b981' }
  ].filter(s => s.value > 0);

  const cx = 90;
  const cy = 90;
  const R = 72;
  const r = 44;

  let currentAngle = -Math.PI / 2;

  const paths = slices.map(s => {
    const fraction = s.value / total;
    const angleSpan = fraction * 2 * Math.PI;
    const startAngle = currentAngle;
    const endAngle = startAngle + angleSpan;
    currentAngle = endAngle;

    if (slices.length === 1 || fraction >= 0.999) {
      return {
        ...s,
        fraction,
        isFullCircle: true,
        pct: (fraction * 100).toFixed(1)
      };
    }

    const x1 = cx + R * Math.cos(startAngle);
    const y1 = cy + R * Math.sin(startAngle);
    const x2 = cx + R * Math.cos(endAngle);
    const y2 = cy + R * Math.sin(endAngle);
    const x3 = cx + r * Math.cos(endAngle);
    const y3 = cy + r * Math.sin(endAngle);
    const x4 = cx + r * Math.cos(startAngle);
    const y4 = cy + r * Math.sin(startAngle);
    const largeArc = angleSpan > Math.PI ? 1 : 0;

    const d = `M ${x1.toFixed(2)} ${y1.toFixed(2)} A ${R} ${R} 0 ${largeArc} 1 ${x2.toFixed(2)} ${y2.toFixed(2)} L ${x3.toFixed(2)} ${y3.toFixed(2)} A ${r} ${r} 0 ${largeArc} 0 ${x4.toFixed(2)} ${y4.toFixed(2)} Z`;

    return {
      ...s,
      fraction,
      isFullCircle: false,
      d,
      pct: (fraction * 100).toFixed(1)
    };
  });

  const activeHoverData = hoveredSlice ? paths.find(p => p.key === hoveredSlice) : null;

  return (
    <div className="donut-chart-card">
      <div className="donut-card-header">
        <span className="donut-strategy-title font-mono">
          {item.strategy}
          {item.is_selected && <span className="pill-active-small">Selected</span>}
        </span>
        <span className="donut-total-badge font-mono">{item.total.toFixed(1)} cyc</span>
      </div>

      <div className="donut-svg-wrapper">
        <svg viewBox="0 0 180 180" className="donut-svg" width="165" height="165">
          <g>
            {paths.map((p) => {
              if (p.isFullCircle) {
                return (
                  <circle
                    key={p.key}
                    cx={cx}
                    cy={cy}
                    r={(R + r) / 2}
                    fill="none"
                    stroke={p.color}
                    strokeWidth={R - r}
                    className={`donut-slice ${hoveredSlice === p.key ? 'slice-hovered' : ''}`}
                    onMouseEnter={() => setHoveredSlice(p.key)}
                    onMouseLeave={() => setHoveredSlice(null)}
                  >
                    <title>{`${p.label}: ${p.value.toFixed(1)} cycles (${p.pct}%)`}</title>
                  </circle>
                );
              }
              return (
                <path
                  key={p.key}
                  d={p.d}
                  fill={p.color}
                  stroke="#ffffff"
                  strokeWidth="1.5"
                  className={`donut-slice ${hoveredSlice === p.key ? 'slice-hovered' : ''}`}
                  onMouseEnter={() => setHoveredSlice(p.key)}
                  onMouseLeave={() => setHoveredSlice(null)}
                >
                  <title>{`${p.label}: ${p.value.toFixed(1)} cycles (${p.pct}%)`}</title>
                </path>
              );
            })}
          </g>

          {/* Donut Center Display */}
          <text x={cx} y={cy - 4} textAnchor="middle" className="donut-center-cycles">
            {activeHoverData ? activeHoverData.value.toFixed(1) : item.total.toFixed(1)}
          </text>
          <text x={cx} y={cy + 10} textAnchor="middle" className="donut-center-unit">
            {activeHoverData ? activeHoverData.label : 'cycles'}
          </text>
          {activeHoverData && (
            <text x={cx} y={cy + 22} textAnchor="middle" className="donut-center-pct font-mono">
              {activeHoverData.pct}%
            </text>
          )}
        </svg>
      </div>

      {/* Component Breakdown List with Exact Floats */}
      <div className="donut-breakdown-list">
        {paths.map((p) => (
          <div
            key={p.key}
            className={`donut-stat-row ${hoveredSlice === p.key ? 'stat-row-active' : ''}`}
            onMouseEnter={() => setHoveredSlice(p.key)}
            onMouseLeave={() => setHoveredSlice(null)}
          >
            <div className="donut-stat-left">
              <span className="donut-legend-dot" style={{ backgroundColor: p.color }}></span>
              <span className="donut-stat-label">{p.label}:</span>
            </div>
            <div className="donut-stat-right">
              <span className="donut-stat-val font-mono">{p.value.toFixed(1)} cyc</span>
              <span className="donut-stat-pct font-mono">({p.pct}%)</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export const PIMMappingViewer = ({ mapping, performance, sourceCode }) => {
  // 1. Mapping table filters & search
  const [filterType, setFilterType] = useState('all'); // 'all', 'pim', 'cpu'
  const [searchTerm, setSearchTerm] = useState('');

  // 1b. Cost component chart view: 'both', 'stacked', or 'pie'
  const [costViewMode, setCostViewMode] = useState('both');

  // 2. Cost Model Assumptions Collapsible Drawer
  const [showAssumptionsDrawer, setShowAssumptionsDrawer] = useState(false);

  // Default parameters from backend
  const defaultParams = useMemo(() => {
    const params = performance?.parameters || mapping?.optimization?.parameters || {};
    return {
      pim_launch_sync_overhead_cycles: params.pim_launch_sync_overhead_cycles ?? 60.0,
      cpu_cycles_per_arithmetic_op: params.cpu_cycles_per_arithmetic_op ?? 1.0,
      pim_cycles_per_arithmetic_op: params.pim_cycles_per_arithmetic_op ?? 1.2,
      bus_bandwidth_bytes_per_cycle: params.bus_bandwidth_bytes_per_cycle ?? 2.0,
      layout_transform_cycles_per_byte: params.layout_transform_cycles_per_byte ?? 0.25
    };
  }, [performance, mapping]);

  // Sensitivity / custom assumptions state
  const [assumptionInputs, setAssumptionInputs] = useState(defaultParams);
  const [sensitivityResult, setSensitivityResult] = useState(null);
  const [isApplyingAssumptions, setIsApplyingAssumptions] = useState(false);
  const [assumptionError, setAssumptionError] = useState(null);

  // Sync inputs whenever the default configuration updates
  useEffect(() => {
    setAssumptionInputs(defaultParams);
    setSensitivityResult(null);
    setAssumptionError(null);
  }, [defaultParams]);

  const instructions = mapping?.instructions || [];
  const pimCount = mapping?.pim_count || 0;
  const cpuCount = mapping?.cpu_count || 0;
  const totalCount = mapping?.total_instructions || instructions.length;

  // Filtered instruction table rows
  const filteredInstructions = useMemo(() => {
    return instructions.filter((instr) => {
      if (filterType === 'pim' && instr.target !== 'PIM') return false;
      if (filterType === 'cpu' && instr.target !== 'CPU') return false;

      if (searchTerm.trim()) {
        const lower = searchTerm.toLowerCase();
        const text = `${instr.ir_opcode} ${instr.mapped_instruction} ${instr.reason} ${instr.formatted} ${instr.optimal_target || ''} ${instr.memory_metadata?.memory_region || ''}`.toLowerCase();
        return text.includes(lower);
      }
      return true;
    });
  }, [instructions, filterType, searchTerm]);

  // Active dataset: either custom sensitivity result or default baseline
  const activeData = useMemo(() => {
    if (sensitivityResult && sensitivityResult.valid) {
      return {
        selected_strategy: sensitivityResult.hypothetical_strategy,
        selected_cost: sensitivityResult.hypothetical_cost,
        speedup_estimate: sensitivityResult.hypothetical_speedup,
        strategies: sensitivityResult.strategies,
        cost_breakdown: sensitivityResult.cost_breakdown,
        decision_explanation: sensitivityResult.decision_explanation || sensitivityResult.impact_summary,
        is_hypothetical: true,
        impact_summary: sensitivityResult.impact_summary,
        strategy_changed: sensitivityResult.strategy_changed,
        baseline_strategy: sensitivityResult.baseline_strategy,
        comparison_table: sensitivityResult.comparison_table || []
      };
    }

    const baselineStrategies = performance?.strategies || [
      {
        strategy: 'CPU_ONLY',
        is_valid: true,
        is_selected: mapping?.optimization?.selected_strategy === 'CPU_ONLY',
        compute_cost: mapping?.optimization?.candidates?.CPU_ONLY?.compute_cost ?? 12.0,
        transfer_cost: mapping?.optimization?.candidates?.CPU_ONLY?.transfer_cost ?? 16.0,
        layout_cost: 0.0,
        synchronization_cost: 0.0,
        total_cost: mapping?.optimization?.candidates?.CPU_ONLY?.total_cost ?? 28.0,
        speedup_vs_cpu: 1.0,
        rejection_reason: null
      },
      {
        strategy: 'DIRECT_PIM',
        is_valid: mapping?.optimization?.candidates?.DIRECT_PIM?.is_valid ?? true,
        is_selected: mapping?.optimization?.selected_strategy === 'DIRECT_PIM',
        compute_cost: mapping?.optimization?.candidates?.DIRECT_PIM?.compute_cost ?? 14.4,
        transfer_cost: mapping?.optimization?.candidates?.DIRECT_PIM?.transfer_cost ?? 4.0,
        layout_cost: 0.0,
        synchronization_cost: mapping?.optimization?.candidates?.DIRECT_PIM?.synchronization_cost ?? 60.0,
        total_cost: mapping?.optimization?.candidates?.DIRECT_PIM?.total_cost ?? 78.4,
        speedup_vs_cpu: mapping?.optimization?.candidates?.DIRECT_PIM?.speedup ?? 1.0,
        rejection_reason: mapping?.optimization?.candidates?.DIRECT_PIM?.rejection_reason
      },
      {
        strategy: 'TRANSFORMED_PIM',
        is_valid: false,
        is_selected: false,
        compute_cost: null,
        transfer_cost: null,
        layout_cost: null,
        synchronization_cost: null,
        total_cost: null,
        speedup_vs_cpu: null,
        rejection_reason: 'Array access pattern is already contiguous/sequential. Data transformation not required.'
      }
    ];

    const baselineCostBreakdown = performance?.cost_breakdown || baselineStrategies
      .filter(s => s.is_valid)
      .map(s => ({
        strategy: s.strategy,
        is_selected: s.is_selected,
        compute: s.compute_cost,
        transfer: s.transfer_cost,
        layout: s.layout_cost,
        synchronization: s.synchronization_cost,
        total: s.total_cost,
        unit: 'cycles'
      }));

    return {
      selected_strategy: performance?.selected_strategy || mapping?.optimization?.selected_strategy || 'CPU_ONLY',
      selected_cost: performance?.selected_cost ?? mapping?.optimization?.selected_cost ?? 16.0,
      speedup_estimate: performance?.speedup_estimate ?? mapping?.optimization?.speedup_estimate ?? 1.0,
      strategies: baselineStrategies,
      cost_breakdown: baselineCostBreakdown,
      decision_explanation: performance?.decision_explanation || mapping?.optimization?.decision_rationale || 'Optimal strategy selected based on minimum analytical cost.',
      is_hypothetical: false,
      impact_summary: null,
      strategy_changed: false,
      baseline_strategy: performance?.selected_strategy || mapping?.optimization?.selected_strategy || 'CPU_ONLY',
      comparison_table: []
    };
  }, [performance, mapping, sensitivityResult]);

  // Handle input changes with validation
  const handleInputChange = (field, val) => {
    setAssumptionInputs(prev => ({
      ...prev,
      [field]: parseFloat(val) || 0
    }));
  };

  // Check if an input differs from default
  const isModified = (field) => {
    return Math.abs(assumptionInputs[field] - defaultParams[field]) > 0.001;
  };

  // Apply custom assumptions
  const handleApplyAssumptions = async () => {
    // Client-side validation
    if (assumptionInputs.bus_bandwidth_bytes_per_cycle <= 0) {
      setAssumptionError('Memory-transfer bandwidth must be greater than zero.');
      return;
    }
    if (assumptionInputs.pim_launch_sync_overhead_cycles < 0 ||
        assumptionInputs.cpu_cycles_per_arithmetic_op < 0 ||
        assumptionInputs.pim_cycles_per_arithmetic_op < 0 ||
        assumptionInputs.layout_transform_cycles_per_byte < 0) {
      setAssumptionError('Costs and overheads cannot be negative.');
      return;
    }

    setIsApplyingAssumptions(true);
    setAssumptionError(null);
    try {
      const res = await evaluatePerformance(sourceCode, assumptionInputs);
      if (res && res.sensitivity) {
        setSensitivityResult(res.sensitivity);
      } else if (res && res.strategies) {
        setSensitivityResult({
          valid: true,
          baseline_strategy: performance?.selected_strategy || 'CPU_ONLY',
          hypothetical_strategy: res.selected_strategy,
          strategy_changed: res.selected_strategy !== (performance?.selected_strategy || 'CPU_ONLY'),
          impact_summary: `Hypothetical evaluation complete. Selected strategy: ${res.selected_strategy} (${res.speedup_estimate}x speedup).`,
          decision_explanation: res.decision_explanation,
          hypothetical_cost: res.selected_cost,
          hypothetical_speedup: res.speedup_estimate,
          strategies: res.strategies,
          cost_breakdown: res.cost_breakdown,
          comparison_table: res.comparison_table || []
        });
      }
    } catch (err) {
      setAssumptionError(err.message || 'Error recalculating with custom assumptions.');
    } finally {
      setIsApplyingAssumptions(false);
    }
  };

  // Reset to defaults
  const handleResetDefaults = () => {
    setAssumptionInputs(defaultParams);
    setSensitivityResult(null);
    setAssumptionError(null);
  };

  if (!mapping || instructions.length === 0) {
    return (
      <div className="empty-tab-state">
        <FaMicrochip className="empty-state-icon" style={{ fontSize: '2.5rem', color: 'var(--text-muted)' }} />
        <h3>No PIM Instruction Mapping Available</h3>
        <p>Enter a C program and click <strong>Compile & Analyze</strong> to inspect hardware instruction mapping and cost performance.</p>
      </div>
    );
  }

  // Max total cost for chart scale
  const maxTotalCost = Math.max(
    ...activeData.cost_breakdown.map(c => c.total || 0),
    10.0
  );

  const transfer = performance?.transfer_metrics || {};
  const execStats = performance?.execution_stats || {};
  const dynamicStats = execStats.dynamic || {};
  const staticStats = execStats.static || {};

  return (
    <div className="pim-mapping-container">
      {/* =========================================================================
          1. IR AND PIM MAPPING RESULTS
          ========================================================================= */}
      {/* 1A. Summary KPI Cards */}
      <div className="pim-metrics-grid">
        <div className="pim-metric-card">
          <div className="metric-header">
            <span className="metric-icon icon-total">
              <FaListCheck size={16} />
            </span>
            <span className="metric-label">Total IR Operations</span>
          </div>
          <div className="metric-value">{totalCount}</div>
          <div className="metric-desc">Three-address-code operations analyzed</div>
        </div>

        <div className="pim-metric-card metric-card-pim">
          <div className="metric-header">
            <span className="metric-icon icon-pim">
              <FaMicrochip size={16} />
            </span>
            <span className="metric-label">In-Memory Eligible (PIM)</span>
          </div>
          <div className="metric-value text-success">{pimCount}</div>
          <div className="metric-desc">Eligible for near-memory execution</div>
        </div>

        <div className="pim-metric-card metric-card-cpu">
          <div className="metric-header">
            <span className="metric-icon icon-cpu">
              <FaServer size={16} />
            </span>
            <span className="metric-label">Host CPU Fallback</span>
          </div>
          <div className="metric-value text-accent">{cpuCount}</div>
          <div className="metric-desc">Control flow and unaccelerated operations</div>
        </div>

        <div className="pim-metric-card metric-card-speedup">
          <div className="metric-header">
            <span className="metric-icon icon-speedup">
              <FaBolt size={16} />
            </span>
            <span className="metric-label">Estimated Speedup</span>
          </div>
          <div className="metric-value text-speedup">
            {activeData.speedup_estimate ? `${activeData.speedup_estimate.toFixed(2)}×` : '1.00×'}
          </div>
          <div className="metric-desc">
            {activeData.speedup_estimate > 1.0
              ? 'Analytical speedup vs host CPU'
              : 'Host CPU execution baseline'}
          </div>
        </div>
      </div>

      {/* 1B. Filter and Search Bar for Mapped Instructions */}
      <div className="pim-filter-bar">
        <div className="btn-group">
          <button
            className={`btn btn-sm ${filterType === 'all' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setFilterType('all')}
          >
            All Instructions ({totalCount})
          </button>
          <button
            className={`btn btn-sm ${filterType === 'pim' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setFilterType('pim')}
          >
            PIM Eligible ({pimCount})
          </button>
          <button
            className={`btn btn-sm ${filterType === 'cpu' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setFilterType('cpu')}
          >
            CPU Fallback ({cpuCount})
          </button>
        </div>

        <input
          type="text"
          className="table-filter-input"
          placeholder="Filter mapping decisions by opcode, target, or rationale..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* 1C. Detailed Instruction-Level Mapping Table */}
      <div className="table-wrapper mapping-table-wrapper">
        <table className="data-table mapping-table">
          <thead>
            <tr>
              <th style={{ width: '45px' }}>#</th>
              <th style={{ width: '80px' }}>Target</th>
              <th style={{ width: '95px' }}>Assignment</th>
              <th style={{ width: '165px' }}>Original IR</th>
              <th style={{ width: '175px' }}>Mapped Instruction</th>
              <th>Mapping Rationale & Hardware Execution</th>
              <th style={{ width: '110px' }}>Data Region</th>
            </tr>
          </thead>
          <tbody>
            {filteredInstructions.map((instr, idx) => (
              <tr
                key={instr.ir_id || idx}
                className={`mapping-row-${instr.target.toLowerCase()}`}
              >
                <td className="text-muted font-mono">{idx + 1}</td>
                <td>
                  <span
                    className={`target-pill ${
                      instr.target === 'PIM' ? 'pill-pim' : 'pill-cpu'
                    }`}
                  >
                    {instr.target}
                  </span>
                </td>
                <td>
                  <span
                    className={`target-pill ${
                      instr.optimal_target === 'PIM' ? 'pill-pim' : 'pill-cpu'
                    }`}
                  >
                    {instr.optimal_target || instr.target}
                  </span>
                </td>
                <td className="font-mono text-secondary">
                  <strong>{instr.ir_opcode}</strong>{' '}
                  {[instr.dest, instr.arg1, instr.arg2].filter(Boolean).join(', ')}
                </td>
                <td className="font-mono">
                  <span
                    className={
                      instr.target === 'PIM' ? 'mapped-op-pim' : 'mapped-op-cpu'
                    }
                  >
                    {instr.formatted || instr.mapped_instruction}
                  </span>
                </td>
                <td className="mapping-reason-cell">
                  <span className="mapping-reason-text">{instr.reason}</span>
                  {instr.cost_justification && (
                    <div className="mapping-cost-note">
                      {instr.cost_justification}
                    </div>
                  )}
                </td>
                <td>
                  <span className="ir-region-tag">
                    {instr.memory_metadata?.memory_region || 'register'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* =========================================================================
          2. SELECTED STRATEGY & DECISION EXPLANATION ("Why Was This Strategy Selected?")
          ========================================================================= */}
      <div className="perf-section-card decision-explanation-box">
        <div className="card-title-row">
          <div className="title-with-icon">
            <FaBolt className="section-title-icon" style={{ color: 'var(--accent)' }} />
            <h3 className="section-title">Why Was This Strategy Selected?</h3>
          </div>
          <div className="decision-header-badges">
            <span className={`strategy-pill pill-${activeData.selected_strategy.toLowerCase()}`}>
              Selected: {activeData.selected_strategy}
            </span>
            <span className={`kpi-tag ${activeData.speedup_estimate > 1.0 ? 'tag-faster' : 'tag-equal'}`}>
              {activeData.speedup_estimate > 1.0
                ? `${activeData.speedup_estimate.toFixed(2)}x Speedup`
                : 'CPU Baseline (1.00x)'}
            </span>
            <span className="badge-static">{activeData.selected_cost.toFixed(1)} cycles</span>
            {activeData.is_hypothetical && (
              <span className="badge-hypothetical">Custom Assumptions</span>
            )}
          </div>
        </div>

        {activeData.is_hypothetical && activeData.strategy_changed && (
          <div className="decision-shift-callout">
            <FaTriangleExclamation />
            <span>
              <strong>Decision Changed:</strong> Strategy changed from <strong>{activeData.baseline_strategy}</strong> to <strong>{activeData.selected_strategy}</strong> due to modified cost-model assumptions.
            </span>
          </div>
        )}

        <p className="explanation-paragraph">
          {activeData.decision_explanation}
        </p>
      </div>

      {/* =========================================================================
          3. STRATEGY COST COMPARISON TABLE
          ========================================================================= */}
      <div className="perf-section-card">
        <div className="card-title-row">
          <div className="title-with-icon">
            <FaTable className="section-title-icon" style={{ color: '#475569' }} />
            <h3 className="section-title">Strategy Cost Comparison Table</h3>
          </div>
          <span className="section-subtitle-note">
            Total Cost = Compute Cost + Transfer Cost + Layout Cost + Synchronization Overhead
          </span>
        </div>

        <div className="perf-table-wrapper">
          <table className="perf-table">
            <thead>
              <tr>
                <th>Strategy Candidate</th>
                <th>Status / Feasibility</th>
                <th>Compute Cost</th>
                <th>Transfer Cost</th>
                <th>Layout Cost</th>
                <th>Sync Overhead</th>
                <th>Total Cost</th>
                <th>Speedup vs CPU</th>
              </tr>
            </thead>
            <tbody>
              {activeData.strategies.map((strat) => {
                const isSelected = (strat.strategy === activeData.selected_strategy);
                const isValid = strat.is_valid;
                return (
                  <tr
                    key={strat.strategy}
                    className={`strat-row ${isSelected ? 'row-selected' : ''} ${!isValid ? 'row-infeasible' : ''}`}
                  >
                    <td>
                      <div className="strat-name-col">
                        <span className={`strategy-pill pill-${strat.strategy.toLowerCase()}`}>
                          {strat.strategy}
                        </span>
                        {isSelected && (
                          <span className="selected-indicator-tag">Selected</span>
                        )}
                      </div>
                    </td>
                    <td>
                      {isValid ? (
                        <span className="status-badge badge-feasible">
                          <FaCircleCheck className="icon-success" /> Feasible
                        </span>
                      ) : (
                        <div className="infeasible-container" title={strat.rejection_reason || 'Infeasible'}>
                          <span className="status-badge badge-infeasible">
                            <FaCircleXmark className="icon-error" /> Infeasible
                          </span>
                          <span className="infeasible-reason-text">
                            {strat.rejection_reason}
                          </span>
                        </div>
                      )}
                    </td>
                    <td className="num-col">
                      {isValid ? `${strat.compute_cost?.toFixed(1)} cyc` : '—'}
                    </td>
                    <td className="num-col">
                      {isValid ? `${strat.transfer_cost?.toFixed(1)} cyc` : '—'}
                    </td>
                    <td className="num-col">
                      {isValid ? `${strat.layout_cost?.toFixed(1)} cyc` : '—'}
                    </td>
                    <td className="num-col">
                      {isValid ? `${strat.synchronization_cost?.toFixed(1)} cyc` : '—'}
                    </td>
                    <td className="num-col bold-col">
                      {isValid ? (
                        <span className="total-cost-val">
                          {strat.total_cost?.toFixed(1)} cyc
                        </span>
                      ) : (
                        <span className="text-muted">—</span>
                      )}
                    </td>
                    <td className="num-col">
                      {isValid && strat.speedup_vs_cpu !== null ? (
                        <span className={`speedup-cell ${strat.speedup_vs_cpu > 1.0 ? 'speedup-pos' : strat.speedup_vs_cpu === 1.0 ? 'speedup-baseline' : 'speedup-neg'}`}>
                          {strat.speedup_vs_cpu.toFixed(2)}x
                        </span>
                      ) : (
                        <span className="text-muted">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* =========================================================================
          4. TOTAL-COST AND COST-BREAKDOWN GRAPHS
          ========================================================================= */}
      <div className="perf-grid-two-col">
        {/* 4A. Stacked Bar & Pie Cost Breakdown Chart */}
        <div className="perf-section-card">
          <div className="card-title-row">
            <div className="title-with-icon">
              <FaChartColumn className="section-title-icon" style={{ color: 'var(--accent)' }} />
              <h3 className="section-title">Cost Component Breakdown</h3>
            </div>
            <div className="chart-view-toggle">
              <button
                type="button"
                className={`view-toggle-btn ${costViewMode === 'both' ? 'active' : ''}`}
                onClick={() => setCostViewMode('both')}
                title="Show both stacked bar and pie chart"
              >
                All Views
              </button>
              <button
                type="button"
                className={`view-toggle-btn ${costViewMode === 'stacked' ? 'active' : ''}`}
                onClick={() => setCostViewMode('stacked')}
                title="Show stacked horizontal bar chart"
              >
                <FaChartColumn size={11} /> Bar
              </button>
              <button
                type="button"
                className={`view-toggle-btn ${costViewMode === 'pie' ? 'active' : ''}`}
                onClick={() => setCostViewMode('pie')}
                title="Show pie / donut component chart"
              >
                <FaChartPie size={11} /> Pie
              </button>
            </div>
          </div>
          <p className="chart-description">
            Analytical breakdown of execution latency across Compute, Transfer, Layout, and Synchronization.
          </p>

          {(costViewMode === 'stacked' || costViewMode === 'both') && (
            <>
              <div className="stacked-bars-container">
                {activeData.cost_breakdown.map((item) => {
                  const total = item.total || 1.0;
                  const computePct = (item.compute / total) * 100;
                  const transferPct = (item.transfer / total) * 100;
                  const layoutPct = (item.layout / total) * 100;
                  const syncPct = (item.synchronization / total) * 100;
                  const barWidthPct = (total / maxTotalCost) * 100;

                  return (
                    <div key={item.strategy} className="stacked-bar-row">
                      <div className="stacked-bar-header">
                        <span className="stacked-bar-name">
                          {item.strategy}
                          {item.is_selected && <span className="pill-active-small">Selected</span>}
                        </span>
                        <span className="stacked-bar-total">{item.total.toFixed(1)} cycles</span>
                      </div>

                      <div className="stacked-bar-track-wrapper">
                        <div className="stacked-bar-track" style={{ width: `${Math.max(barWidthPct, 15)}%` }}>
                          {computePct > 0 && (
                            <div
                              className="bar-seg seg-compute"
                              style={{ width: `${computePct}%` }}
                              title={`Compute: ${item.compute.toFixed(1)} cyc (${computePct.toFixed(1)}%)`}
                            >
                              <span>{item.compute.toFixed(1)}</span>
                            </div>
                          )}
                          {transferPct > 0 && (
                            <div
                              className="bar-seg seg-transfer"
                              style={{ width: `${transferPct}%` }}
                              title={`Transfer: ${item.transfer.toFixed(1)} cyc (${transferPct.toFixed(1)}%)`}
                            >
                              <span>{item.transfer.toFixed(1)}</span>
                            </div>
                          )}
                          {layoutPct > 0 && (
                            <div
                              className="bar-seg seg-layout"
                              style={{ width: `${layoutPct}%` }}
                              title={`Layout: ${item.layout.toFixed(1)} cyc (${layoutPct.toFixed(1)}%)`}
                            >
                              <span>{item.layout.toFixed(1)}</span>
                            </div>
                          )}
                          {syncPct > 0 && (
                            <div
                              className="bar-seg seg-sync"
                              style={{ width: `${syncPct}%` }}
                              title={`Sync Overhead: ${item.synchronization.toFixed(1)} cyc (${syncPct.toFixed(1)}%)`}
                            >
                              <span>{item.synchronization.toFixed(1)}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Chart Legend */}
              <div className="chart-legend">
                <div className="legend-item">
                  <span className="legend-box seg-compute"></span>
                  <span>Compute</span>
                </div>
                <div className="legend-item">
                  <span className="legend-box seg-transfer"></span>
                  <span>Bus Transfer</span>
                </div>
                <div className="legend-item">
                  <span className="legend-box seg-layout"></span>
                  <span>Layout Reorganization</span>
                </div>
                <div className="legend-item">
                  <span className="legend-box seg-sync"></span>
                  <span>Sync Overhead</span>
                </div>
              </div>
            </>
          )}

          {/* 4A2. Pie / Donut Chart Component Breakdown */}
          {(costViewMode === 'pie' || costViewMode === 'both') && (
            <div className={`pie-charts-wrapper ${costViewMode === 'pie' ? 'pie-only' : ''}`}>
              {costViewMode === 'both' && (
                <div className="pie-charts-heading">
                  <FaChartPie style={{ color: '#f59e0b' }} />
                  <span>Proportional Breakdown (Pie Chart)</span>
                </div>
              )}
              <div className="pie-charts-grid">
                {activeData.cost_breakdown.map((item) => (
                  <DonutCostChart key={item.strategy} item={item} />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 4B. Total Cost & Speedup Meter */}
        <div className="perf-section-card">
          <div className="card-title-row">
            <div className="title-with-icon">
              <FaArrowTrendUp className="section-title-icon" style={{ color: '#10b981' }} />
              <h3 className="section-title">Speedup & Relative Latency</h3>
            </div>
            <span className="unit-label">Normalized to CPU</span>
          </div>
          <p className="chart-description">
            Total latency comparison normalized to host CPU execution baseline (1.00x).
          </p>

          <div className="speedup-comparison-bars">
            {activeData.strategies.filter(s => s.is_valid).map((strat) => {
              const speedup = strat.speedup_vs_cpu ?? 1.0;
              const isFaster = speedup > 1.0;
              const isSelected = strat.strategy === activeData.selected_strategy;

              return (
                <div key={strat.strategy} className={`speedup-row ${isSelected ? 'speedup-row-selected' : ''}`}>
                  <div className="speedup-label-row">
                    <span className="speedup-strat-title">
                      {strat.strategy}
                      {isSelected && <span className="pill-active-small">Optimal</span>}
                    </span>
                    <span className="speedup-strat-val">
                      {speedup.toFixed(2)}x
                      <span className="speedup-cycle-hint">({strat.total_cost.toFixed(1)} cyc)</span>
                    </span>
                  </div>

                  <div className="speedup-progress-bg">
                    <div
                      className={`speedup-progress-fill ${isFaster ? 'fill-faster' : 'fill-baseline'}`}
                      style={{ width: `${Math.min(Math.max((speedup / 2.0) * 100, 10), 100)}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="academic-disclaimer-box">
            <FaCircleInfo className="disclaimer-icon" />
            <div className="disclaimer-text">
              Estimates are derived from the analytical compiler cost model using instruction cycle counts and memory-bus bandwidth, rather than physical silicon benchmarking.
            </div>
          </div>
        </div>
      </div>

      {/* 4C. Workload Profile & Memory Traffic Modeling */}
      <div className="perf-section-card">
        <div className="card-title-row">
          <div className="title-with-icon">
            <FaMemory className="section-title-icon" style={{ color: '#0284c7' }} />
            <h3 className="section-title">Data Movement & Memory Traffic Modeling</h3>
          </div>
          <span className="badge-academic">Bus Bandwidth & Traffic Model</span>
        </div>
        <p className="chart-description">
          Static analytical breakdown of declared memory footprint, memory bus transfer overheads, and offload savings for the selected strategy.
        </p>

        <div className="perf-grid-two-col">
          {/* Data Movement & Transfer Latency */}
          <div className="stats-subpanel">
            <div className="subpanel-header">
              <span className="subpanel-title">Host Bus Transfer & Savings</span>
              <span className="status-badge badge-feasible">Analytical Model</span>
            </div>

            <div className="stats-list">
              <div className="stats-row">
                <span className="stat-row-label">Modeled Bus Bytes (CPU Baseline):</span>
                <span className="stat-row-value">{transfer.cpu_bytes_transferred ?? 0} bytes</span>
              </div>
              <div className="stats-row">
                <span className="stat-row-label">Modeled Bus Bytes (Selected Strategy):</span>
                <span className="stat-row-value font-bold text-accent">{transfer.selected_bytes_transferred ?? 8} bytes</span>
              </div>
              <div className="stats-row">
                <span className="stat-row-label">Bus Bytes Saved:</span>
                <span className="stat-row-value text-success font-bold">{transfer.bytes_saved ?? 0} bytes</span>
              </div>
              <div className="stats-row">
                <span className="stat-row-label">Bus Traffic Reduction:</span>
                <span className="stat-row-value text-success font-bold">
                  {transfer.bandwidth_reduction_pct ? `-${transfer.bandwidth_reduction_pct}%` : '0%'}
                </span>
              </div>
              <div className="stats-row">
                <span className="stat-row-label">Transfer Latency Saved:</span>
                <span className="stat-row-value text-success font-bold">
                  {transfer.transfer_cost_savings_cycles ?? 0} cycles
                </span>
              </div>
              <div className="stats-row">
                <span className="stat-row-label">Memory Bus Bandwidth:</span>
                <span className="stat-row-value">{transfer.bus_bandwidth_bytes_per_cycle ?? 2.0} B/cycle</span>
              </div>
            </div>
          </div>

          {/* Static Workload Profile */}
          <div className="stats-subpanel">
            <div className="subpanel-header">
              <span className="subpanel-title">Static Workload Profile (Compiler AST / IR)</span>
              <span className="badge-static">Static Profile</span>
            </div>

            <div className="stats-list">
              <div className="stats-row">
                <span className="stat-row-label">3AC IR Instruction Count:</span>
                <span className="stat-row-value">{staticStats.total_ir_instructions ?? totalCount}</span>
              </div>
              <div className="stats-row">
                <span className="stat-row-label">Static Computational Ops:</span>
                <span className="stat-row-value">{staticStats.static_computational_ops ?? '—'}</span>
              </div>
              <div className="stats-row">
                <span className="stat-row-label">Declared Memory Storage:</span>
                <span className="stat-row-value">{transfer.declared_footprint_bytes ?? 16} bytes</span>
              </div>
              <div className="stats-row">
                <span className="stat-row-label">Estimated Loop Iterations:</span>
                <span className="stat-row-value">{staticStats.estimated_loop_iterations ?? '—'}</span>
              </div>
              <div className="stats-row">
                <span className="stat-row-label">Access Pattern:</span>
                <span className="stat-row-value">{staticStats.access_pattern || 'Unit-stride sequential'}</span>
              </div>
              <div className="stats-row">
                <span className="stat-row-label">Offload Profitability:</span>
                <span className="stat-row-value font-bold text-accent">
                  {performance?.offload_beneficial ? 'Beneficial (Net Speedup)' : 'Not Beneficial (CPU Faster)'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* =========================================================================
          5. COST MODEL ASSUMPTIONS PANEL (COLLAPSIBLE)
          ========================================================================= */}
      <div className="perf-section-card sensitivity-sandbox-panel">
        <div
          className="card-title-row clickable-title-row"
          onClick={() => setShowAssumptionsDrawer(!showAssumptionsDrawer)}
          style={{ cursor: 'pointer' }}
        >
          <div className="title-with-icon">
            <FaSliders className="section-title-icon" style={{ color: '#8b5cf6' }} />
            <h3 className="section-title">Cost Model Assumptions</h3>
          </div>
          <div className="drawer-toggle-actions">
            <span className="badge-hypothetical">
              {showAssumptionsDrawer ? 'Click to Collapse' : 'Click to Configure Assumptions'}
            </span>
            <button className="btn btn-ghost btn-sm" aria-label="Toggle Drawer">
              {showAssumptionsDrawer ? <FaChevronUp size={13} /> : <FaChevronDown size={13} />}
            </button>
          </div>
        </div>

        {showAssumptionsDrawer && (
          <div className="assumptions-expanded-content">
            <p className="chart-description">
              Experiment with hypothetical hardware values. Recalculates strategy costs via the backend cost model without modifying project default configurations.
            </p>

            {assumptionError && (
              <div className="sensitivity-error-message">
                <FaTriangleExclamation /> {assumptionError}
              </div>
            )}

            <div className="sensitivity-controls-grid">
              {/* 1. CPU Op Cost */}
              <div className="control-item">
                <div className="control-label-row">
                  <label htmlFor="cpu-cost">CPU Computation Cost</label>
                  <span className="control-val-display">
                    {assumptionInputs.cpu_cycles_per_arithmetic_op} cyc/op
                    {isModified('cpu_cycles_per_arithmetic_op') && (
                      <span className="modified-pill">Modified</span>
                    )}
                  </span>
                </div>
                <input
                  id="cpu-cost"
                  type="range"
                  min="0.2"
                  max="5.0"
                  step="0.1"
                  value={assumptionInputs.cpu_cycles_per_arithmetic_op}
                  onChange={(e) => handleInputChange('cpu_cycles_per_arithmetic_op', e.target.value)}
                  className="slider-input"
                />
                <span className="control-hint">
                  Default: {defaultParams.cpu_cycles_per_arithmetic_op} cycles/op. Superscalar host processor execution cost.
                </span>
              </div>

              {/* 2. PIM Op Cost */}
              <div className="control-item">
                <div className="control-label-row">
                  <label htmlFor="pim-cost">PIM Computation Cost</label>
                  <span className="control-val-display">
                    {assumptionInputs.pim_cycles_per_arithmetic_op} cyc/op
                    {isModified('pim_cycles_per_arithmetic_op') && (
                      <span className="modified-pill">Modified</span>
                    )}
                  </span>
                </div>
                <input
                  id="pim-cost"
                  type="range"
                  min="0.2"
                  max="5.0"
                  step="0.1"
                  value={assumptionInputs.pim_cycles_per_arithmetic_op}
                  onChange={(e) => handleInputChange('pim_cycles_per_arithmetic_op', e.target.value)}
                  className="slider-input"
                />
                <span className="control-hint">
                  Default: {defaultParams.pim_cycles_per_arithmetic_op} cycles/op. Near-memory ALUs typically run at conservative clock rates.
                </span>
              </div>

              {/* 3. Memory Bus Bandwidth */}
              <div className="control-item">
                <div className="control-label-row">
                  <label htmlFor="bus-bw">Memory-Transfer Bandwidth</label>
                  <span className="control-val-display">
                    {assumptionInputs.bus_bandwidth_bytes_per_cycle} B/cycle
                    {isModified('bus_bandwidth_bytes_per_cycle') && (
                      <span className="modified-pill">Modified</span>
                    )}
                  </span>
                </div>
                <input
                  id="bus-bw"
                  type="range"
                  min="0.5"
                  max="8.0"
                  step="0.5"
                  value={assumptionInputs.bus_bandwidth_bytes_per_cycle}
                  onChange={(e) => handleInputChange('bus_bandwidth_bytes_per_cycle', e.target.value)}
                  className="slider-input"
                />
                <span className="control-hint">
                  Default: {defaultParams.bus_bandwidth_bytes_per_cycle} Bytes/cycle. Lower bus bandwidth increases CPU streaming penalty.
                </span>
              </div>

              {/* 4. PIM Launch & Sync Overhead */}
              <div className="control-item">
                <div className="control-label-row">
                  <label htmlFor="launch-overhead">PIM Launch & Sync Overhead</label>
                  <span className="control-val-display">
                    {assumptionInputs.pim_launch_sync_overhead_cycles} cycles
                    {isModified('pim_launch_sync_overhead_cycles') && (
                      <span className="modified-pill">Modified</span>
                    )}
                  </span>
                </div>
                <input
                  id="launch-overhead"
                  type="range"
                  min="0"
                  max="150"
                  step="5"
                  value={assumptionInputs.pim_launch_sync_overhead_cycles}
                  onChange={(e) => handleInputChange('pim_launch_sync_overhead_cycles', e.target.value)}
                  className="slider-input"
                />
                <span className="control-hint">
                  Default: {defaultParams.pim_launch_sync_overhead_cycles} cycles. MMIO kernel descriptor dispatch and barrier completion overhead.
                </span>
              </div>

              {/* 5. Layout Transformation Cost */}
              <div className="control-item">
                <div className="control-label-row">
                  <label htmlFor="layout-cost">Layout Transformation Cost</label>
                  <span className="control-val-display">
                    {assumptionInputs.layout_transform_cycles_per_byte} cyc/byte
                    {isModified('layout_transform_cycles_per_byte') && (
                      <span className="modified-pill">Modified</span>
                    )}
                  </span>
                </div>
                <input
                  id="layout-cost"
                  type="range"
                  min="0.0"
                  max="2.0"
                  step="0.1"
                  value={assumptionInputs.layout_transform_cycles_per_byte}
                  onChange={(e) => handleInputChange('layout_transform_cycles_per_byte', e.target.value)}
                  className="slider-input"
                />
                <span className="control-hint">
                  Default: {defaultParams.layout_transform_cycles_per_byte} cycles/byte. In-memory data layout reorganization penalty.
                </span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="sensitivity-actions-row">
              <button
                className="btn btn-primary"
                onClick={handleApplyAssumptions}
                disabled={isApplyingAssumptions}
              >
                {isApplyingAssumptions ? (
                  <>
                    <span className="spinner"></span>
                    <span>Applying Assumptions...</span>
                  </>
                ) : (
                  <>
                    <FaBolt />
                    <span>Apply Assumptions</span>
                  </>
                )}
              </button>

              <button
                className="btn btn-secondary"
                onClick={handleResetDefaults}
                disabled={isApplyingAssumptions}
              >
                <FaRotateLeft />
                <span>Reset to Defaults</span>
              </button>
            </div>

            {/* =========================================================================
                6. DEFAULT-VERSUS-CUSTOM COMPARISON TABLE (Visible when custom applied)
                ========================================================================= */}
            {activeData.is_hypothetical && activeData.comparison_table.length > 0 && (
              <div className="default-vs-custom-section">
                <div className="comparison-heading">
                  <strong>Default vs. Custom Assumptions Comparison</strong>
                </div>
                <div className="perf-table-wrapper">
                  <table className="perf-table comparison-compact-table">
                    <thead>
                      <tr>
                        <th>Metric</th>
                        <th>Default Assumptions</th>
                        <th>Custom Assumptions</th>
                        <th>Comparison Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {activeData.comparison_table.map((row) => (
                        <tr key={row.metric} className={row.changed ? 'row-changed-highlight' : ''}>
                          <td><strong>{row.metric}</strong></td>
                          <td className="font-mono">{row.default_value}</td>
                          <td className="font-mono font-bold text-accent">{row.custom_value}</td>
                          <td>
                            {row.changed ? (
                              <span className="status-badge badge-infeasible">
                                Changed
                              </span>
                            ) : (
                              <span className="status-badge badge-feasible">
                                Identical
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PIMMappingViewer;
