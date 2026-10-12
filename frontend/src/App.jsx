import React, { useState, useEffect, useCallback } from 'react';
import { compileCode } from './api/client';
import CodeEditor from './components/CodeEditor';
import ExampleSelector from './components/ExampleSelector';
import StageStatusPanel from './components/StageStatusPanel';
import TokenTable from './components/TokenTable';
import ASTViewer from './components/ASTViewer';
import SemanticViewer from './components/SemanticViewer';
import IRViewer from './components/IRViewer';
import PIMMappingViewer from './components/PIMMappingViewer';
import SimulationViewer from './components/SimulationViewer';
import LanguageSpec from './components/LanguageSpec';
import './styles/variables.css';
import './App.css';

const DEFAULT_CODE = `int main() {
    int arr[4] = {10, 20, 30, 40};
    int sum = 0;

    for (int i = 0; i < 4; i++) {
        sum = sum + arr[i];
    }

    return 0;
}`;

export const App = () => {
  const [sourceCode, setSourceCode] = useState(DEFAULT_CODE);
  const [isCompiling, setIsCompiling] = useState(false);
  const [compilationResult, setCompilationResult] = useState(null);
  const [activeTab, setActiveTab] = useState('tokens'); // 'tokens', 'ast', 'semantic'
  const [showSpec, setShowSpec] = useState(false);

  const handleCompile = useCallback(async () => {
    if (!sourceCode.trim()) {
      alert('Source code cannot be empty.');
      return;
    }

    setIsCompiling(true);
    try {
      const result = await compileCode(sourceCode);
      setCompilationResult(result);
      if (result.stages?.semantic?.status === 'error') {
        setActiveTab('semantic');
      } else if (result.stages?.syntax?.status === 'error') {
        setActiveTab('tokens');
      }
    } catch (err) {
      console.error('Compilation failed:', err);
      setCompilationResult({
        success: false,
        error: err.response?.data?.detail || err.message || 'Error connecting to compiler service.',
        stages: {
          lexical: { status: 'error', message: 'Connection failed' },
          syntax: { status: 'skipped', message: 'Skipped' },
          semantic: { status: 'skipped', message: 'Skipped' }
        },
        tokens: [],
        ast: null,
        symbol_table: {},
        diagnostics: [{ severity: 'error', message: 'Failed to communicate with compiler engine.', line: 1, column: 1 }]
      });
    } finally {
      setIsCompiling(false);
    }
  }, [sourceCode]);

  // Auto-compile default program on initial mount so all stages & simulation are loaded
  useEffect(() => {
    handleCompile();
  }, []);

  // Support Ctrl+Enter / Cmd+Enter shortcut
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        handleCompile();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleCompile]);

  const handleSelectStage = (stageId) => {
    const map = {
      lexical: 'tokens',
      syntax: 'ast',
      semantic: 'semantic',
      ir: 'ir',
      pim_mapping: 'mapping',
      simulation: 'simulation'
    };
    if (map[stageId]) {
      setActiveTab(map[stageId]);
    }
  };

  const handleExampleSelect = async (code) => {
    setSourceCode(code);
    setIsCompiling(true);
    try {
      const result = await compileCode(code);
      setCompilationResult(result);
    } catch (err) {
      console.error('Example compilation error:', err);
    } finally {
      setIsCompiling(false);
    }
  };

  const handleReset = () => {
    setSourceCode(DEFAULT_CODE);
    setCompilationResult(null);
  };

  const lineCount = sourceCode.split('\n').length;
  const charCount = sourceCode.length;

  return (
    <div className="app-container">
      {/* Sleek Modern Navigation Header */}
      <header className="app-header">
        <div className="header-brand">
          <div className="brand-logo-badge">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="4" y="4" width="16" height="16" rx="2" />
              <rect x="9" y="9" width="6" height="6" />
              <line x1="9" y1="1" x2="9" y2="4" />
              <line x1="15" y1="1" x2="15" y2="4" />
              <line x1="9" y1="20" x2="9" y2="23" />
              <line x1="15" y1="20" x2="15" y2="23" />
              <line x1="20" y1="9" x2="23" y2="9" />
              <line x1="20" y1="14" x2="23" y2="14" />
              <line x1="1" y1="9" x2="4" y2="9" />
              <line x1="1" y1="14" x2="4" y2="14" />
            </svg>
          </div>
          <div className="brand-text">
            <h1 className="brand-title">Compiler for Processing in Memory</h1>
          </div>
        </div>

        <div className="header-actions">
          <button
            className={`btn btn-ghost btn-sm ${showSpec ? 'active' : ''}`}
            onClick={() => setShowSpec(!showSpec)}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
            {showSpec ? 'Close Spec' : 'Language Spec'}
          </button>
        </div>
      </header>

      {/* Language Specification Drawer / Card */}
      {showSpec && (
        <section className="spec-drawer">
          <LanguageSpec />
        </section>
      )}

      {/* Main Vertical Workspace Layout */}
      <main className="workspace-main">
        {/* Top: Code Editor Section */}
        <section className="editor-column">
          <div className="panel editor-card">
            <div className="editor-toolbar">
              <div className="file-tab">
                <span className="file-icon">C</span>
                <span className="file-name">main.c</span>
              </div>
              <div className="toolbar-controls">
                <ExampleSelector onSelect={handleExampleSelect} />
              </div>
            </div>

            <div className="editor-body">
              <CodeEditor
                value={sourceCode}
                onChange={(val) => setSourceCode(val)}
                height="320px"
              />
            </div>

            <div className="editor-statusbar">
              <div className="statusbar-left">
                <span className="status-item">{lineCount} lines</span>
                <span className="status-divider">•</span>
                <span className="status-item">{charCount} characters</span>
              </div>

              <div className="statusbar-actions">
                <button
                  className="btn btn-primary btn-run"
                  onClick={handleCompile}
                  disabled={isCompiling}
                  title="Shortcut: Ctrl+Enter"
                >
                  {isCompiling ? (
                    <>
                      <span className="spinner"></span>
                      <span>Compiling...</span>
                    </>
                  ) : (
                    <>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                        <polygon points="5 3 19 12 5 21 5 3" />
                      </svg>
                      <span>Compile & Analyze</span>
                      <kbd className="kbd-shortcut">Ctrl+↵</kbd>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Right Column: Pipeline & Inspection */}
        <section className="output-column">
          {/* Pipeline Stepper */}
          <div className="panel pipeline-panel">
            <div className="panel-header-simple">
              <span className="section-title">Compilation Pipeline</span>
              {compilationResult && (
                <span className={`badge-pill ${compilationResult.success ? 'pill-success' : 'pill-error'}`}>
                  {compilationResult.success ? '✓ Build Passed' : '✗ Build Failed'}
                </span>
              )}
            </div>
            <StageStatusPanel
              stages={compilationResult ? compilationResult.stages : null}
              isCompiling={isCompiling}
              onSelectStage={handleSelectStage}
            />
          </div>

          {/* Diagnostic Banner if Error */}
          {compilationResult && !compilationResult.success && compilationResult.error && (
            <div className="error-callout">
              <div className="error-callout-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
              </div>
              <div className="error-callout-content">
                <div className="error-callout-title">Diagnostics Encountered</div>
                <div className="error-callout-message">{compilationResult.error}</div>
              </div>
            </div>
          )}

          {/* Inspection Tabs */}
          <div className="panel results-panel">
            <div className="segmented-tab-bar">
              <button
                className={`segmented-tab ${activeTab === 'tokens' ? 'active' : ''}`}
                onClick={() => setActiveTab('tokens')}
              >
                Tokens
                {compilationResult?.tokens && (
                  <span className="tab-pill">{compilationResult.tokens.length}</span>
                )}
              </button>
              <button
                className={`segmented-tab ${activeTab === 'ast' ? 'active' : ''}`}
                onClick={() => setActiveTab('ast')}
              >
                AST Hierarchy
                {compilationResult?.ast && (
                  <span className="tab-pill">Tree</span>
                )}
              </button>
              <button
                className={`segmented-tab ${activeTab === 'semantic' ? 'active' : ''}`}
                onClick={() => setActiveTab('semantic')}
              >
                Symbol Table
                {compilationResult?.symbol_table && (
                  <span className="tab-pill">
                    {Object.keys(compilationResult.symbol_table).length}
                  </span>
                )}
              </button>
              <button
                className={`segmented-tab ${activeTab === 'ir' ? 'active' : ''}`}
                onClick={() => setActiveTab('ir')}
              >
                Intermediate Representation
                {compilationResult?.ir?.instructions && (
                  <span className="tab-pill">{compilationResult.ir.instructions.length}</span>
                )}
              </button>
              <button
                className={`segmented-tab ${activeTab === 'mapping' ? 'active' : ''}`}
                onClick={() => setActiveTab('mapping')}
              >
                PIM Mapping
                {compilationResult?.mapping && (
                  <span className="tab-pill">
                    {compilationResult.mapping.pim_count} PIM / {compilationResult.mapping.cpu_count} CPU
                  </span>
                )}
              </button>
              <button
                className={`segmented-tab ${activeTab === 'simulation' ? 'active' : ''}`}
                onClick={() => setActiveTab('simulation')}
              >
                Execution Simulation
                {compilationResult?.simulation?.comparison?.verdict && (
                  <span className={`tab-pill ${compilationResult.simulation.comparison.verdict === 'PASS' ? 'tab-pill-success' : 'tab-pill-warning'}`}>
                    {compilationResult.simulation.comparison.verdict}
                  </span>
                )}
              </button>
            </div>

            <div className="tab-viewport">
              {!compilationResult ? (
                <div className="placeholder-state">
                  <div className="placeholder-icon">
                    <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <polygon points="12 2 2 7 12 12 22 7 12 2" />
                      <polyline points="2 17 12 22 22 17" />
                      <polyline points="2 12 12 17 22 12" />
                    </svg>
                  </div>
                  <h3 className="placeholder-title">Ready to Compile</h3>
                  <p className="placeholder-desc">
                    Enter C code or select a sample, then click <strong>Compile & Analyze</strong> to inspect tokens, the abstract syntax tree, 3AC intermediate representation, PIM hardware mapping, and dual execution simulation.
                  </p>
                </div>
              ) : (
                <>
                  {activeTab === 'tokens' && (
                    <TokenTable tokens={compilationResult.tokens} />
                  )}
                  {activeTab === 'ast' && (
                    <ASTViewer ast={compilationResult.ast} />
                  )}
                  {activeTab === 'semantic' && (
                    <SemanticViewer
                      symbolTable={compilationResult.symbol_table}
                      diagnostics={compilationResult.diagnostics}
                    />
                  )}
                  {activeTab === 'ir' && (
                    <IRViewer ir={compilationResult.ir} />
                  )}
                  {activeTab === 'mapping' && (
                    <PIMMappingViewer mapping={compilationResult.mapping} />
                  )}
                  {activeTab === 'simulation' && (
                    <SimulationViewer
                      simulation={compilationResult.simulation}
                      onReRunSimulation={() => handleCompile(false)}
                      isCompiling={isCompiling}
                    />
                  )}
                </>
              )}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default App;
