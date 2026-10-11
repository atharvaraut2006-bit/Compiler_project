import React, { useState, useEffect } from 'react';
import { checkHealth, compileCode } from './api/client';
import CodeEditor from './components/CodeEditor';
import ExampleSelector from './components/ExampleSelector';
import StageStatusPanel from './components/StageStatusPanel';
import TokenTable from './components/TokenTable';
import ASTViewer from './components/ASTViewer';
import SemanticViewer from './components/SemanticViewer';
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
  const [backendOnline, setBackendOnline] = useState(null);
  const [showSpec, setShowSpec] = useState(false);

  // Check backend health on mount
  useEffect(() => {
    checkHealth()
      .then((res) => {
        if (res && res.status === 'ok') {
          setBackendOnline(true);
        } else {
          setBackendOnline(false);
        }
      })
      .catch(() => setBackendOnline(false));
  }, []);

  const handleCompile = async () => {
    if (!sourceCode.trim()) {
      alert('Source code cannot be empty.');
      return;
    }

    setIsCompiling(true);
    try {
      const result = await compileCode(sourceCode);
      setCompilationResult(result);
      // Auto-switch to semantic tab if there is a semantic error, or AST if success
      if (result.stages && result.stages.semantic && result.stages.semantic.status === 'error') {
        setActiveTab('semantic');
      } else if (result.stages && result.stages.syntax && result.stages.syntax.status === 'error') {
        setActiveTab('tokens');
      }
    } catch (err) {
      console.error('Compilation failed:', err);
      setCompilationResult({
        success: false,
        error: err.response?.data?.detail || err.message || 'Network error connecting to backend.',
        stages: {
          lexical: { status: 'error', message: 'API connection failed' },
          syntax: { status: 'skipped', message: 'Skipped' },
          semantic: { status: 'skipped', message: 'Skipped' }
        },
        tokens: [],
        ast: null,
        symbol_table: {},
        diagnostics: [{ severity: 'error', message: 'Failed to communicate with compiler backend API.', line: 1, column: 1 }]
      });
    } finally {
      setIsCompiling(false);
    }
  };

  const handleExampleSelect = (code) => {
    setSourceCode(code);
    setCompilationResult(null);
  };

  const handleReset = () => {
    setSourceCode(DEFAULT_CODE);
    setCompilationResult(null);
  };

  return (
    <div className="app-container">
      {/* Top Navigation / Header */}
      <header className="app-header">
        <div className="header-left">
          <div className="header-title-group">
            <h1 className="header-title">Compiler for Processing in Memory (PIM)</h1>
            <span className="phase-pill">Phase 1: C Compiler Front End</span>
          </div>
          <p className="header-subtitle">
            Lexical Analysis, Recursive Descent Parsing, AST Generation, and Semantic Validation
          </p>
        </div>

        <div className="header-right">
          <div className={`status-pill ${backendOnline === true ? 'pill-online' : backendOnline === false ? 'pill-offline' : 'pill-checking'}`}>
            <span className="status-dot"></span>
            Backend: {backendOnline === true ? 'FastAPI Connected (Port 8000)' : backendOnline === false ? 'Offline' : 'Connecting...'}
          </div>
          <button
            className="btn btn-outline btn-sm"
            onClick={() => setShowSpec(!showSpec)}
          >
            {showSpec ? 'Hide C Spec' : 'View C Spec'}
          </button>
        </div>
      </header>

      {/* Collapsible Language Specification */}
      {showSpec && (
        <section className="spec-section">
          <LanguageSpec />
        </section>
      )}

      {/* Main Two-Column Workspace */}
      <main className="workspace-main">
        {/* Left Column: Code Editor & Controls */}
        <section className="editor-column">
          <div className="panel editor-panel">
            <div className="panel-header">
              <span className="panel-title">C Source Code Input</span>
              <span className="text-muted text-sm">Target: Supported C Subset</span>
            </div>

            <ExampleSelector onSelect={handleExampleSelect} />

            <div className="editor-wrapper">
              <CodeEditor
                value={sourceCode}
                onChange={(val) => setSourceCode(val)}
                height="460px"
              />
            </div>

            <div className="editor-actions">
              <button
                className="btn btn-primary btn-compile"
                onClick={handleCompile}
                disabled={isCompiling}
              >
                {isCompiling ? (
                  <>
                    <span className="spinner"></span> Compiling & Analyzing...
                  </>
                ) : (
                  <>▶ Compile & Analyze</>
                )}
              </button>
              <button
                className="btn btn-outline"
                onClick={handleReset}
                disabled={isCompiling}
              >
                Reset Code
              </button>
            </div>
          </div>
        </section>

        {/* Right Column: Stage Pipeline & Inspection Tabs */}
        <section className="output-column">
          {/* Stage Status Panel */}
          <div className="panel stages-panel">
            <div className="panel-header">
              <span className="panel-title">Compiler Front End Pipeline</span>
              {compilationResult && (
                <span className={`badge ${compilationResult.success ? 'badge-success' : 'badge-danger'}`}>
                  {compilationResult.success ? '✓ Compilation Succeeded' : '✗ Compilation Error'}
                </span>
              )}
            </div>
            <StageStatusPanel
              stages={compilationResult ? compilationResult.stages : null}
              error={compilationResult ? compilationResult.error : null}
            />
          </div>

          {/* Error Banner if Top-Level Error */}
          {compilationResult && !compilationResult.success && compilationResult.error && (
            <div className="alert alert-danger error-banner">
              <strong>Compiler Diagnostic: </strong> {compilationResult.error}
            </div>
          )}

          {/* Results Tabbed Inspector */}
          <div className="panel results-panel">
            <div className="tab-navigation">
              <button
                className={`tab-btn ${activeTab === 'tokens' ? 'active' : ''}`}
                onClick={() => setActiveTab('tokens')}
              >
                Tokens
                {compilationResult && compilationResult.tokens && (
                  <span className="tab-count-badge">{compilationResult.tokens.length}</span>
                )}
              </button>
              <button
                className={`tab-btn ${activeTab === 'ast' ? 'active' : ''}`}
                onClick={() => setActiveTab('ast')}
              >
                AST Hierarchy
                {compilationResult && compilationResult.ast && (
                  <span className="tab-count-badge">Ready</span>
                )}
              </button>
              <button
                className={`tab-btn ${activeTab === 'semantic' ? 'active' : ''}`}
                onClick={() => setActiveTab('semantic')}
              >
                Semantic & Symbol Table
                {compilationResult && compilationResult.symbol_table && (
                  <span className="tab-count-badge">
                    {Object.keys(compilationResult.symbol_table).length} symbols
                  </span>
                )}
              </button>
            </div>

            <div className="tab-content-area">
              {!compilationResult ? (
                <div className="empty-tab-state">
                  <div className="empty-icon">⚙</div>
                  <h3>No Compilation Output Yet</h3>
                  <p>Select an example program or type your C code, then click <strong>Compile & Analyze</strong>.</p>
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
