import React from 'react';

export const SemanticViewer = ({ symbolTable = {}, diagnostics = [] }) => {
  const symbols = Object.values(symbolTable || {});
  const errorDiagnostics = diagnostics.filter((d) => d.severity === 'error');
  const warningDiagnostics = diagnostics.filter((d) => d.severity === 'warning');

  return (
    <div className="semantic-viewer-container">
      {/* Diagnostics Section */}
      <div className="diagnostics-section">
        <div className="section-title-row">
          <h4 className="section-heading">Compiler Diagnostics</h4>
          <div className="diagnostics-counters">
            <span className={`badge ${errorDiagnostics.length > 0 ? 'badge-danger' : 'badge-success'}`}>
              {errorDiagnostics.length} Errors
            </span>
            <span className="badge badge-warning">
              {warningDiagnostics.length} Warnings
            </span>
          </div>
        </div>

        {diagnostics.length === 0 ? (
          <div className="alert alert-success">
            ✓ No semantic errors or warnings detected. Program passes semantic validation!
          </div>
        ) : (
          <div className="diagnostics-list">
            {diagnostics.map((diag, idx) => (
              <div
                key={idx}
                className={`diagnostic-card diag-${diag.severity}`}
              >
                <div className="diag-header">
                  <span className={`badge badge-${diag.severity === 'error' ? 'danger' : 'warning'}`}>
                    {diag.severity.toUpperCase()}
                  </span>
                  <span className="diag-location">
                    Line {diag.line}, Column {diag.column}
                  </span>
                </div>
                <div className="diag-message">{diag.message}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Symbol Table Section */}
      <div className="symbol-table-section">
        <h4 className="section-heading">Scoped Symbol Table ({symbols.length} Symbols)</h4>
        {symbols.length === 0 ? (
          <div className="empty-tab-state">No symbols defined in the current program.</div>
        ) : (
          <div className="table-wrapper symbol-table-wrapper">
            <table className="data-table symbol-table">
              <thead>
                <tr>
                  <th className="col-sym-name">Symbol Name</th>
                  <th className="col-sym-type">Type</th>
                  <th className="col-sym-kind">Kind</th>
                  <th className="col-sym-size">Size</th>
                  <th className="col-sym-scope">Scope</th>
                  <th className="col-sym-loc">Location</th>
                </tr>
              </thead>
              <tbody>
                {symbols.map((sym, idx) => (
                  <tr key={idx}>
                    <td className="col-sym-name">
                      <strong className="symbol-name">{sym.name}</strong>
                    </td>
                    <td className="col-sym-type">
                      <span className="type-badge">{sym.type_name}</span>
                    </td>
                    <td className="col-sym-kind">
                      {sym.is_array ? (
                        <span className="kind-badge kind-array">Array</span>
                      ) : (
                        <span className="kind-badge kind-scalar">Scalar</span>
                      )}
                    </td>
                    <td className="col-sym-size">
                      {sym.size !== undefined && sym.size !== null ? sym.size : '—'}
                    </td>
                    <td className="col-sym-scope">
                      <span className={`scope-badge scope-${sym.scope_level === 0 ? 'global' : 'local'}`}>
                        {sym.scope_level === 0 ? 'Global' : 'Local'}
                      </span>
                    </td>
                    <td className="col-sym-loc text-muted">
                      L{sym.line}:C{sym.column}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default SemanticViewer;
