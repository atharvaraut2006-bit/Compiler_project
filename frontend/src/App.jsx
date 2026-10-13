import React, { useState, useEffect, useCallback } from 'react';
import { compileCode, checkHealth, API_BASE } from './api/client';
import CodeEditor from './components/CodeEditor';
import ExampleSelector from './components/ExampleSelector';
import StageStatusPanel from './components/StageStatusPanel';
import TokenTable from './components/TokenTable';
import ASTViewer from './components/ASTViewer';
import SemanticViewer from './components/SemanticViewer';
import IRViewer from './components/IRViewer';
import PIMMappingViewer from './components/PIMMappingViewer';
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
  const [backendStatus, setBackendStatus] = useState({
    online: null,
    checking: true,
    service: '',
    version: '',
    apiUrl: API_BASE,
    errorHint: ''
  });

  const checkBackend = useCallback(async () => {
    try {
      const health = await checkHealth();
      setBackendStatus({
        online: health.online,
        checking: false,
        service: health.service || '',
        version: health.version || '',
        apiUrl: health.apiUrl || API_BASE,
        errorHint: health.errorHint || ''
      });
      return health.online;
    } catch {
      setBackendStatus({
        online: false,
        checking: false,
        service: '',
        version: '',
        apiUrl: API_BASE,
        errorHint: 'Offline'
      });
      return false;
    }
  }, []);

  const handleCompile = useCallback(async () => {
    if (!sourceCode.trim()) {
      alert('Source code cannot be empty.');
      return;
    }

    setIsCompiling(true);
    try {
      const result = await compileCode(sourceCode);
      setCompilationResult(result);
      if (result.is_backend_error) {
        setBackendStatus(prev => ({ ...prev, online: false, checking: false, errorHint: 'Unreachable' }));
      } else {
        setBackendStatus(prev => ({ ...prev, online: true, checking: false }));
        if (result.stages?.semantic?.status === 'error') {
          setActiveTab('semantic');
        } else if (result.stages?.syntax?.status === 'error') {
          setActiveTab('tokens');
        }
      }
    } catch (err) {
      console.error('Compilation failed:', err);
      setBackendStatus(prev => ({ ...prev, online: false, checking: false, errorHint: 'Unreachable' }));
      setCompilationResult({
        success: false,
        error: `Cannot connect to compiler backend at ${API_BASE}. ${err.message}`,
        is_backend_error: true,
        stages: {
          lexical: { status: 'error', message: 'Backend unreachable' },
          syntax: { status: 'skipped', message: 'Backend unreachable' },
          semantic: { status: 'skipped', message: 'Backend unreachable' },
          ir: { status: 'skipped', message: 'Backend unreachable' },
          pim_mapping: { status: 'skipped', message: 'Backend unreachable' }
        },
        tokens: [],
        ast: null,
        symbol_table: {},
        diagnostics: [{
          severity: 'error',
          message: `Cannot reach Python backend server at ${API_BASE}. Start it with 'python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000'.`,
          line: 1,
          column: 1
        }]
      });
    } finally {
      setIsCompiling(false);
    }
  }, [sourceCode]);

  // Check backend connection on mount and every 30 seconds
  useEffect(() => {
    checkBackend();
    const interval = setInterval(checkBackend, 30000);
    return () => clearInterval(interval);
  }, [checkBackend]);

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
      pim_mapping: 'mapping'
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
          <div
            className={`backend-pill backend-${backendStatus.checking ? 'checking' : (backendStatus.online ? 'online' : 'offline')}`}
            title={`Compiler API: ${backendStatus.apiUrl}`}
          >
            <span className="backend-dot"></span>
            <span className="backend-label font-mono">
              {backendStatus.checking
                ? 'Backend: Connecting...'
                : (backendStatus.online
                    ? `Backend: Online (${backendStatus.service || 'FastAPI'})`
                    : `Backend: Offline (${backendStatus.apiUrl})`)}
            </span>
            {!backendStatus.online && !backendStatus.checking && (
              <button
                className="backend-retry-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  setBackendStatus(p => ({ ...p, checking: true }));
                  checkBackend();
                }}
                title="Retry connecting to Python compiler backend"
              >
                ↻ Retry
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Backend Alert Banner if Offline */}
      {!backendStatus.online && !backendStatus.checking && (
        <div className="backend-alert-banner">
          <div className="backend-alert-content">
            <strong>⚠️ Compiler Backend Disconnected:</strong> Cannot reach the Python compiler at <code>{backendStatus.apiUrl}</code>.
            <div className="backend-alert-hint">
              To compile code, please start the Python FastAPI service: <code>python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000</code>
            </div>
          </div>
          <button
            className="btn btn-sm btn-retry-banner"
            onClick={() => {
              setBackendStatus(p => ({ ...p, checking: true }));
              checkBackend();
            }}
          >
            Reconnect
          </button>
        </div>
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
                PIM Mapping & Performance
                {compilationResult?.mapping && (
                  <span className="tab-pill">
                    {compilationResult.mapping.pim_count} PIM / {compilationResult.mapping.cpu_count} CPU
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
                    Enter C code or select a sample, then click <strong>Compile & Analyze</strong> to inspect tokens, the abstract syntax tree, 3AC intermediate representation, and PIM hardware mapping & performance analysis.
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
                    <PIMMappingViewer
                      mapping={compilationResult.mapping}
                      performance={compilationResult.performance}
                      sourceCode={sourceCode}
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
