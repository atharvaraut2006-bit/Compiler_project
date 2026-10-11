import React, { useState, useMemo } from 'react';
import { FaMicrochip, FaServer, FaListCheck } from 'react-icons/fa6';

export const PIMMappingViewer = ({ mapping }) => {
  const [filterType, setFilterType] = useState('all'); // 'all', 'pim', 'cpu'
  const [searchTerm, setSearchTerm] = useState('');

  const instructions = mapping?.instructions || [];
  const pimCount = mapping?.pim_count || 0;
  const cpuCount = mapping?.cpu_count || 0;
  const totalCount = mapping?.total_instructions || instructions.length;

  const filteredInstructions = useMemo(() => {
    return instructions.filter((instr) => {
      // Target filter
      if (filterType === 'pim' && instr.target !== 'PIM') return false;
      if (filterType === 'cpu' && instr.target !== 'CPU') return false;

      // Search term
      if (searchTerm.trim()) {
        const lower = searchTerm.toLowerCase();
        const text = `${instr.ir_opcode} ${instr.mapped_instruction} ${instr.reason} ${instr.formatted}`.toLowerCase();
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

  return (
    <div className="pim-mapping-container">
      {/* Summary Metrics Cards */}
      <div className="pim-metrics-grid">
        <div className="pim-metric-card">
          <div className="metric-header">
            <span className="metric-icon icon-total">
              <FaListCheck size={16} />
            </span>
            <span className="metric-label">Total IR Instructions</span>
          </div>
          <div className="metric-value">{totalCount}</div>
          <div className="metric-desc">Three-address-code operations analyzed</div>
        </div>

        <div className="pim-metric-card metric-card-pim">
          <div className="metric-header">
            <span className="metric-icon icon-pim">
              <FaMicrochip size={16} />
            </span>
            <span className="metric-label">In-Memory (PIM) Target</span>
          </div>
          <div className="metric-value text-success">{pimCount}</div>
          <div className="metric-desc">Operations mapped to simulated PIM units</div>
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
      </div>

      {/* Filter and Search Bar */}
      <div className="pim-filter-bar">
        <div className="btn-group">
          <button
            className={`btn btn-sm ${filterType === 'all' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setFilterType('all')}
          >
            All ({totalCount})
          </button>
          <button
            className={`btn btn-sm ${filterType === 'pim' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setFilterType('pim')}
          >
            PIM Target ({pimCount})
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

      {/* Mapping Detailed Table */}
      <div className="table-wrapper">
        <table className="data-table mapping-table">
          <thead>
            <tr>
              <th style={{ width: '45px' }}>#</th>
              <th style={{ width: '80px' }}>Target</th>
              <th style={{ width: '170px' }}>Original IR</th>
              <th style={{ width: '180px' }}>Mapped Instruction</th>
              <th>Mapping Rationale & Hardware Execution</th>
              <th style={{ width: '110px' }}>Data Region</th>
            </tr>
          </thead>
          <tbody>
            {filteredInstructions.map((instr, idx) => (
              <tr key={instr.ir_id || idx} className={`mapping-row-${instr.target.toLowerCase()}`}>
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
