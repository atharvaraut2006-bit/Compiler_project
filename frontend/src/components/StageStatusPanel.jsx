import React from 'react';

export const StageStatusPanel = ({ stages, error }) => {
  if (!stages) {
    return (
      <div className="stage-panel-empty">
        <span className="text-muted">Click <strong>Compile & Analyze</strong> to view compiler pipeline stages.</span>
      </div>
    );
  }

  const stageList = [
    {
      id: 'lexical',
      name: '1. Lexical Analysis',
      desc: 'Tokenization & location tracking',
      data: stages.lexical
    },
    {
      id: 'syntax',
      name: '2. Syntax Analysis',
      desc: 'Recursive descent & AST generation',
      data: stages.syntax
    },
    {
      id: 'semantic',
      name: '3. Semantic Analysis',
      desc: 'Type check & symbol table validation',
      data: stages.semantic
    }
  ];

  const getStatusBadge = (status) => {
    switch (status) {
      case 'success':
        return <span className="status-badge badge-success">✓ Succeeded</span>;
      case 'error':
        return <span className="status-badge badge-danger">✗ Failed</span>;
      case 'skipped':
        return <span className="status-badge badge-muted">○ Skipped</span>;
      default:
        return <span className="status-badge badge-muted">⏳ Pending</span>;
    }
  };

  return (
    <div className="stage-status-panel">
      <div className="stage-status-grid">
        {stageList.map((stage) => {
          const status = stage.data ? stage.data.status : 'pending';
          return (
            <div key={stage.id} className={`stage-card stage-${status}`}>
              <div className="stage-card-header">
                <span className="stage-card-title">{stage.name}</span>
                {getStatusBadge(status)}
              </div>
              <p className="stage-card-desc">{stage.desc}</p>
              {stage.data && stage.data.message && (
                <div className="stage-card-msg">{stage.data.message}</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default StageStatusPanel;
