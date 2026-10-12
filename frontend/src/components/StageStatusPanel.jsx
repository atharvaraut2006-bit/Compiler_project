import React from 'react';

export const StageStatusPanel = ({ stages, isCompiling, onSelectStage }) => {
  const stageList = [
    {
      id: 'lexical',
      step: '01',
      name: 'Lexical',
      desc: 'Tokens & Scanner',
      data: stages ? stages.lexical : null
    },
    {
      id: 'syntax',
      step: '02',
      name: 'Syntax',
      desc: 'AST Parsing',
      data: stages ? stages.syntax : null
    },
    {
      id: 'semantic',
      step: '03',
      name: 'Semantic',
      desc: 'Symbol Scope',
      data: stages ? stages.semantic : null
    },
    {
      id: 'ir',
      step: '04',
      name: 'IR Generation',
      desc: '3AC Instructions',
      data: stages ? stages.ir : null
    },
    {
      id: 'pim_mapping',
      step: '05',
      name: 'PIM Mapping',
      desc: 'Hardware Target',
      data: stages ? stages.pim_mapping : null
    },
    {
      id: 'simulation',
      step: '06',
      name: 'Simulation',
      desc: 'CPU & PIM Dual Run',
      data: stages ? stages.simulation : null
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
      <div className="stage-pipeline-container stage-pipeline-6">
        {stageList.map((stage) => {
          const status = stage.data ? stage.data.status : (isCompiling ? 'pending' : 'idle');
          return (
            <div
              key={stage.id}
              className={`pipeline-step-card step-${status}`}
              onClick={() => onSelectStage && onSelectStage(stage.id)}
              style={{ cursor: onSelectStage ? 'pointer' : 'default' }}
              title={`Click to inspect Stage ${stage.step}: ${stage.name}`}
            >
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
          );
        })}
      </div>
    </div>
  );
};

export default StageStatusPanel;
