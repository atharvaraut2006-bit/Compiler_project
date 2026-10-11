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

      <div className="table-wrapper token-table-wrapper">
        <table className="data-table token-table">
          <thead>
            <tr>
              <th className="col-idx">#</th>
              <th className="col-type">Token Type</th>
              <th className="col-val">Value</th>
              <th className="col-line">Line</th>
              <th className="col-col">Column</th>
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
                  <td className="text-muted col-idx">{idx + 1}</td>
                  <td className="col-type">
                    <span className="token-badge">{type}</span>
                  </td>
                  <td className="col-val">
                    <code className="token-value">{value}</code>
                  </td>
                  <td className="col-line">{line}</td>
                  <td className="col-col">{col}</td>
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
