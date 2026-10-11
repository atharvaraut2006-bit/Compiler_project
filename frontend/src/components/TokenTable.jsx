import React, { useState } from 'react';

export const TokenTable = ({ tokens = [] }) => {
  const [filter, setFilter] = useState('');

  if (!tokens || tokens.length === 0) {
    return <div className="empty-tab-state">No tokens generated.</div>;
  }

  const filteredTokens = tokens.filter((token) => {
    if (!filter) return true;
    const typeStr = String(token.type || token.token_type || '').toLowerCase();
    const valStr = String(token.value || '').toLowerCase();
    return typeStr.includes(filter.toLowerCase()) || valStr.includes(filter.toLowerCase());
  });

  return (
    <div className="token-table-container">
      <div className="table-controls">
        <span className="token-count">Total Tokens: {tokens.length}</span>
        <input
          type="text"
          placeholder="Filter tokens by type or value..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="table-filter-input"
        />
      </div>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: '60px' }}>#</th>
              <th>Token Type</th>
              <th>Value</th>
              <th style={{ width: '80px' }}>Line</th>
              <th style={{ width: '80px' }}>Column</th>
            </tr>
          </thead>
          <tbody>
            {filteredTokens.map((tok, idx) => {
              const type = tok.type || tok.token_type || 'UNKNOWN';
              const value = tok.value !== undefined ? String(tok.value) : '';
              const line = tok.line !== undefined ? tok.line : tok.lineno ?? '-';
              const col = tok.column !== undefined ? tok.column : tok.col ?? '-';

              return (
                <tr key={idx}>
                  <td className="text-muted">{idx + 1}</td>
                  <td>
                    <span className="token-badge">{type}</span>
                  </td>
                  <td>
                    <code className="token-value">{value}</code>
                  </td>
                  <td>{line}</td>
                  <td>{col}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TokenTable;
