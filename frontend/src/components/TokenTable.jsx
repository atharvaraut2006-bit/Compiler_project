import React, { useState } from 'react';

/**
 * Returns explicit classification for each token:
 * identifier | keyword | operator | delimeter | numeric literal
 */
export const getTokenCategory = (tok) => {
  if (tok.category) {
    const c = String(tok.category).toLowerCase();
    if (c === 'delimiter') return 'delimeter';
    return c;
  }

  const type = String(tok.type || tok.token_type || '').toUpperCase();
  const val = String(tok.value !== undefined ? tok.value : '');

  // 1. Keyword
  if (
    ['INT', 'RETURN', 'FOR', 'WHILE', 'IF', 'ELSE', 'PRINT', 'KEYWORD'].includes(type) ||
    ['int', 'return', 'for', 'while', 'if', 'else', 'print', 'void', 'char'].includes(val)
  ) {
    return 'keyword';
  }

  // 2. Numeric Literal
  if (
    ['INT_LITERAL', 'FLOAT_LITERAL', 'NUMBER', 'NUMERIC_LITERAL', 'NUMERIC LITERAL'].includes(type) ||
    /^[0-9]+$/.test(val)
  ) {
    return 'numeric literal';
  }

  // 3. Identifier
  if (type === 'IDENTIFIER') {
    return 'identifier';
  }

  // 4. Operator
  if (
    [
      'ASSIGN', 'PLUS', 'MINUS', 'STAR', 'SLASH', 'PERCENT',
      'INCREMENT', 'DECREMENT', 'PLUS_ASSIGN', 'MINUS_ASSIGN',
      'STAR_ASSIGN', 'SLASH_ASSIGN', 'PERCENT_ASSIGN',
      'LT', 'LE', 'GT', 'GE', 'EQ', 'NE',
      'LOGICAL_AND', 'LOGICAL_OR', 'LOGICAL_NOT', 'OPERATOR'
    ].includes(type) ||
    ['+', '-', '*', '/', '%', '=', '+=', '-=', '*=', '/=', '==', '!=', '<', '<=', '>', '>=', '&&', '||', '!', '++', '--'].includes(val)
  ) {
    return 'operator';
  }

  // 5. Delimiter
  if (
    [
      'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE',
      'LBRACKET', 'RBRACKET', 'SEMICOLON', 'COMMA',
      'DELIMITER', 'DELIMETER', 'PUNCTUATION', 'EOF'
    ].includes(type) ||
    ['(', ')', '{', '}', '[', ']', ';', ','].includes(val)
  ) {
    return 'delimeter';
  }

  if (/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(val)) {
    return 'identifier';
  }

  return 'delimeter';
};

export const TokenTable = ({ tokens = [] }) => {
  const [filter, setFilter] = useState('');

  if (!tokens || tokens.length === 0) {
    return <div className="empty-tab-state">No tokens generated.</div>;
  }

  const filteredTokens = tokens.filter((token) => {
    if (!filter) return true;
    const query = filter.toLowerCase().trim();
    const typeStr = String(token.type || token.token_type || '').toLowerCase();
    const valStr = String(token.value !== undefined ? token.value : '').toLowerCase();

    return typeStr.includes(query) || valStr.includes(query);
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
