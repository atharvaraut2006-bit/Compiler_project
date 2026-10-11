import React, { useState, useMemo } from 'react';
import {
  FaMicrochip,
  FaServer,
  FaListCheck,
  FaBolt,
  FaScaleBalanced,
  FaChevronDown,
  FaChevronUp,
  FaCircleInfo,
  FaShuffle,
  FaFilePdf
} from 'react-icons/fa6';

export const PIMMappingViewer = ({ mapping }) => {
  const [filterType, setFilterType] = useState('all'); // 'all', 'pim', 'cpu'
  const [searchTerm, setSearchTerm] = useState('');
  const [showAssumptions, setShowAssumptions] = useState(false);

  const instructions = mapping?.instructions || [];
  const pimCount = mapping?.pim_count || 0;
  const cpuCount = mapping?.cpu_count || 0;
  const totalCount = mapping?.total_instructions || instructions.length;

  const optimization = mapping?.optimization || {};
  const workload = optimization?.workload_profile || {};
  const candidates = optimization?.candidates || {};
  const selectedStrategy = optimization?.selected_strategy || 'CPU_ONLY';
  const speedupEstimate = optimization?.speedup_estimate ?? 1.0;
  const rationale = optimization?.decision_rationale || '';
  const parameters = optimization?.parameters || {};

  const filteredInstructions = useMemo(() => {
    return instructions.filter((instr) => {
      // Target filter
      if (filterType === 'pim' && instr.target !== 'PIM') return false;
      if (filterType === 'cpu' && instr.target !== 'CPU') return false;

      // Search term
      if (searchTerm.trim()) {
        const lower = searchTerm.toLowerCase();
        const text = `${instr.ir_opcode} ${instr.mapped_instruction} ${instr.reason} ${instr.formatted} ${instr.optimal_target || ''}`.toLowerCase();
        return text.includes(lower);
      }
      return true;
    });
  }, [instructions, filterType, searchTerm]);

  if (!mapping || instructions.length === 0) {
    return (
      <div className="empty-tab-state">
        <p>No PIM instruction mapping available.</p>
      </div>
    );
  }

  const getStrategyBadgeClass = (strat) => {
    if (strat === 'DIRECT_PIM') return 'badge-strategy-pim';
    if (strat === 'TRANSFORMED_PIM') return 'badge-strategy-transformed';
    return 'badge-strategy-cpu';
  };

  return (
    <div className="pim-mapping-container">
      {/* 1. Summary Metrics Header */}
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
            {speedupEstimate > 1.0 ? `${speedupEstimate}×` : '1.0×'}
          </div>
          <div className="metric-desc">
            {optimization?.offload_beneficial
              ? 'Analytical speedup vs host CPU'
              : 'Host CPU execution preferred'}
          </div>
        </div>
      </div>

      {/* 2. Analytical Cost Model & Strategy Selection Card */}
      <div className="cost-model-section">
        <div className="cost-model-header">
          <div className="cost-header-title">
            <FaScaleBalanced size={16} className="text-accent" />
            <h4 className="cost-section-heading">
              Analytical Cost Model & Candidate Evaluation
            </h4>
            <span className={`strategy-pill ${getStrategyBadgeClass(selectedStrategy)}`}>
              Optimal: {selectedStrategy}
            </span>
          </div>
          <div className="cost-header-actions" style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <a
              href="http://127.0.0.1:8000/api/cost-model-pdf"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-ghost btn-sm btn-assumptions"
              title="Download publication-quality Cost Model Formulas & Specifications PDF"
              style={{ textDecoration: 'none' }}
            >
              <FaFilePdf size={13} color="#dc2626" />
              <span>Formulas PDF</span>
            </a>
            <button
              className="btn btn-ghost btn-sm btn-assumptions"
              onClick={() => setShowAssumptions(!showAssumptions)}
            >
              <FaCircleInfo size={13} />
              <span>Simulation Assumptions</span>
              {showAssumptions ? <FaChevronUp size={11} /> : <FaChevronDown size={11} />}
            </button>
          </div>
        </div>

        {/* Explainable Decision Rationale Banner */}
        <div className="decision-callout">
          <div className="decision-callout-icon">
            <FaBolt size={15} />
          </div>
          <div className="decision-callout-body">
            <div className="decision-callout-title">Optimization Decision Rationale</div>
            <div className="decision-callout-text">{rationale}</div>
          </div>
        </div>

        {/* Workload Profile Quick Specs */}
        <div className="workload-summary-bar">
          <div className="workload-pill">
            <span className="workload-label">Compute Ops:</span>
            <strong>{workload.total_computational_ops ?? (workload.arithmetic_op_count + workload.comparison_op_count)}</strong>
          </div>
          <div className="workload-pill">
            <span className="workload-label">Memory Footprint:</span>
            <strong>{workload.total_memory_bytes ?? 0} bytes</strong>
          </div>
          <div className="workload-pill">
            <span className="workload-label">Loop Iterations:</span>
            <strong>
              {workload.loop_iterations !== null && workload.loop_iterations !== undefined
                ? `${workload.loop_iterations} (Static)`
                : 'Undetermined (Dynamic)'}
            </strong>
          </div>
          <div className="workload-pill">
            <span className="workload-label">Access Pattern:</span>
            <strong className="capitalize">{workload.access_pattern || 'scalar'}</strong>
          </div>
          <div className="workload-pill">
            <span className="workload-label">Layout Status:</span>
            <strong>
              {workload.requires_layout_transform
                ? 'Layout Transform Evaluated'
                : 'Standard Preserved'}
            </strong>
          </div>
        </div>

        {/* Four-Term Candidate Comparison Table */}
        <div className="table-wrapper candidate-table-wrapper">
          <table className="data-table candidate-table">
            <thead>
              <tr>
                <th style={{ width: '150px' }}>Strategy Candidate</th>
                <th style={{ width: '90px', textAlign: 'center' }}>Status</th>
                <th style={{ width: '100px', textAlign: 'right' }}>Compute</th>
                <th style={{ width: '100px', textAlign: 'right' }}>Transfer</th>
                <th style={{ width: '90px', textAlign: 'right' }}>Layout</th>
                <th style={{ width: '95px', textAlign: 'right' }}>Sync O/H</th>
                <th style={{ width: '115px', textAlign: 'right' }}>Total (Cycles)</th>
                <th>Candidate Evaluation & Constraints</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(candidates).map(([name, cand]) => {
                const isSelected = name === selectedStrategy;
                return (
                  <tr
                    key={name}
                    className={`candidate-row ${
                      isSelected ? 'candidate-row-selected' : ''
                    } ${!cand.is_valid ? 'candidate-row-invalid' : ''}`}
                  >
                    <td>
                      <strong className="font-mono">{name}</strong>
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      {isSelected ? (
                        <span className="badge badge-success">Selected</span>
                      ) : cand.is_valid ? (
                        <span className="badge badge-secondary">Alternative</span>
                      ) : (
                        <span className="badge badge-danger">Rejected</span>
                      )}
                    </td>
                    <td style={{ textAlign: 'right' }} className="font-mono">
                      {cand.is_valid ? `${cand.compute_cost} cyc` : '—'}
                    </td>
                    <td style={{ textAlign: 'right' }} className="font-mono">
                      {cand.is_valid ? `${cand.transfer_cost} cyc` : '—'}
                    </td>
                    <td style={{ textAlign: 'right' }} className="font-mono">
                      {cand.is_valid ? `${cand.layout_cost} cyc` : '—'}
                    </td>
                    <td style={{ textAlign: 'right' }} className="font-mono">
                      {cand.is_valid ? `${cand.synchronization_cost} cyc` : '—'}
                    </td>
                    <td style={{ textAlign: 'right' }} className="font-mono">
                      {cand.is_valid ? (
                        <strong className={isSelected ? 'text-accent' : ''}>
                          {cand.total_cost} cyc
                        </strong>
                      ) : (
                        <span className="text-muted">Infeasible</span>
                      )}
                    </td>
                    <td className="text-secondary text-sm">
                      {cand.rejection_reason || cand.notes}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Expandable Simulation Assumptions Legend */}
        {showAssumptions && (
          <div className="assumptions-drawer">
            <div className="assumptions-heading">
              Configurable Simulation Parameters & Mathematical Definitions
            </div>
            <p className="assumptions-subheading">
              Modeled according to Near-Memory Computing optimization (NMC-Opt) literature:
              <br />
              <code className="font-mono">
                Total Cost = Compute Cost + Transfer Cost + Layout Cost + Synchronization Cost
              </code>
            </p>
            <div className="assumptions-grid">
              <div className="assumption-item">
                <span className="assumption-term">CPU Compute Speed:</span>
                <span className="assumption-val">
                  {parameters.cpu_cycles_per_arithmetic_op ?? 1.0} cycles / op
                </span>
                <span className="assumption-desc">Superscalar pipelined core</span>
              </div>
              <div className="assumption-item">
                <span className="assumption-term">PIM Compute Speed:</span>
                <span className="assumption-val">
                  {parameters.pim_cycles_per_arithmetic_op ?? 1.2} cycles / op
                </span>
                <span className="assumption-desc">In-memory ALU within DRAM power envelope</span>
              </div>
              <div className="assumption-item">
                <span className="assumption-term">Host Bus Bandwidth:</span>
                <span className="assumption-val">
                  {parameters.bus_bandwidth_bytes_per_cycle ?? 2.0} bytes / cycle
                </span>
                <span className="assumption-desc">Off-chip DDR memory bus channel</span>
              </div>
              <div className="assumption-item">
                <span className="assumption-term">PIM Bank Bandwidth:</span>
                <span className="assumption-val">
                  {parameters.pim_internal_bandwidth_bytes_per_cycle ?? 32.0} bytes / cycle
                </span>
                <span className="assumption-desc">Internal TSV / row buffer bandwidth</span>
              </div>
              <div className="assumption-item">
                <span className="assumption-term">Launch & Sync Overhead:</span>
                <span className="assumption-val">
                  {parameters.pim_launch_sync_overhead_cycles ?? 60.0} cycles
                </span>
                <span className="assumption-desc">Host dispatch & completion barrier</span>
              </div>
              <div className="assumption-item">
                <span className="assumption-term">Layout Transform Penalty:</span>
                <span className="assumption-val">
                  {parameters.layout_transform_cycles_per_byte ?? 0.25} cycles / byte
                </span>
                <span className="assumption-desc">Strided coalescing reorganization</span>
              </div>
            </div>
            <div className="assumptions-disclaimer">
              Notice: These parameters are simulation assumptions for comparative cost evaluation,
              not measured physical hardware values.
            </div>
          </div>
        )}
      </div>

      {/* 3. Filter and Search Bar for Mapped Instructions */}
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
          placeholder="Filter mapping decisions..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* 4. Detailed Instruction-Level Mapping Table */}
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
    </div>
  );
};

export default PIMMappingViewer;
