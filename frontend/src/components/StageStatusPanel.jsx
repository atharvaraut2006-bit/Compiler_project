import React from 'react';

export const StageStatusPanel = ({ stages, isCompiling }) => {
  const stageList = [
    {
      id: 'lexical',
      step: '01',
      name: 'Lexical Analysis',
      desc: 'Tokenization & Scanners',
      data: stages ? stages.lexical : null
    },
    {
      id: 'syntax',
      step: '02',
      name: 'Syntax Analysis',
      desc: 'Recursive Descent & AST',
      data: stages ? stages.syntax : null
    },
    {
      id: 'semantic',
      step: '03',
      name: 'Semantic Analysis',
      desc: 'Type & Symbol Validation',
      data: stages ? stages.semantic : null
    }
  ];

  const getStatusIndicator = (status) => {
    switch (status) {
      case 'success':
        return (
          <span className="stage-pill pill-success">
            <span className="dot dot-success"></span> Success
          </span>
        );
      case 'error':
        return (
          <span className="stage-pill pill-error">
            <span className="dot dot-error"></span> Failed
          </span>
        );
      case 'skipped':
        return (
          <span className="stage-pill pill-skipped">
            <span className="dot dot-skipped"></span> Skipped
          </span>
        );
      default:
        return (
          <span className="stage-pill pill-idle">
            <span className="dot dot-idle"></span> Idle
          </span>
        );
    }
  };

  return (
    <div className="stage-pipeline-wrapper">
      <div className="stage-pipeline-container">
        {stageList.map((stage, idx) => {
          const status = stage.data ? stage.data.status : (isCompiling ? 'pending' : 'idle');
          return (
            <React.Fragment key={stage.id}>
              <div className={`pipeline-step-card step-${status}`}>
                <div className="step-top-row">
                  <span className="step-number">{stage.step}</span>
                  {getStatusIndicator(status)}
                </div>
                <div className="step-name">{stage.name}</div>
                <div className="step-desc">{stage.desc}</div>
                {stage.data && stage.data.message && (
                  <div className="step-meta" title={stage.data.message}>
                    {stage.data.message}
                  </div>
                )}
              </div>
              {idx < stageList.length - 1 && (
                <div className={`pipeline-connector ${stages ? 'active' : ''}`}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

export default StageStatusPanel;
