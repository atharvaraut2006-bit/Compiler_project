import React, { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import { FaPlus, FaMinus, FaArrowsRotate, FaTree, FaCode, FaSun, FaMoon } from 'react-icons/fa6';

const CARD_W = 126;
const CARD_H = 58;
const GAP_X = 28;
const GAP_Y = 56;

// Helper to convert raw AST nodes into display nodes
function convertASTNode(node, badge = '', index = 0) {
  if (!node) return null;
  const type = node.node_type || node.type || 'Node';

  switch (type) {
    case 'Program': {
      const stmts = [];
      const func = node.body?.find((b) => b.node_type === 'FunctionDef');
      if (func && func.body?.statements) {
        func.body.statements.forEach((s, idx) => {
          stmts.push(convertASTNode(s, `stmt ${idx + 1}`, idx));
        });
      } else if (node.body) {
        node.body.forEach((s, idx) => {
          stmts.push(convertASTNode(s, `stmt ${idx + 1}`, idx));
        });
      }
      return {
        id: 'prog_root',
        badge: badge || '',
        title: 'PROGRAM',
        value: `${stmts.length} statement(s)`,
        category: 'purple',
        children: stmts.filter(Boolean),
        raw: node
      };
    }

    case 'FunctionDef': {
      const children = [];
      if (node.body?.statements) {
        node.body.statements.forEach((s, idx) => {
          children.push(convertASTNode(s, `stmt ${idx + 1}`, idx));
        });
      }
      return {
        id: `fn_${node.name || 'main'}`,
        badge: badge || 'func',
        title: 'FUNCTIONDEF',
        value: `${node.return_type || 'int'} ${node.name}()`,
        category: 'purple',
        children: children.filter(Boolean),
        raw: node
      };
    }

    case 'VarDecl': {
      const children = [];
      if (node.initializer) {
        children.push(convertASTNode(node.initializer, 'value'));
      }
      return {
        id: `decl_${node.name}_${Math.random().toString(36).substr(2, 6)}`,
        badge: badge || 'decl',
        title: 'VARDECL',
        value: `${node.type_name || 'int'} ${node.name} =`,
        category: 'purple',
        children,
        raw: node
      };
    }

    case 'ArrayDecl': {
      const children = [];
      if (node.initializers && node.initializers.length > 0) {
        node.initializers.forEach((init, idx) => {
          children.push(convertASTNode(init, `[${idx}]`, idx));
        });
      }
      return {
        id: `arrdecl_${node.name}_${Math.random().toString(36).substr(2, 6)}`,
        badge: badge || 'decl',
        title: 'ARRAYDECL',
        value: `${node.type_name || 'int'} ${node.name}[${node.size}]`,
        category: 'purple',
        children,
        raw: node
      };
    }

    case 'Assignment': {
      const children = [];
      if (node.target?.node_type === 'ArrayAccess') {
        children.push(convertASTNode(node.target, 'target'));
      }
      if (node.value) {
        children.push(convertASTNode(node.value, 'value'));
      }
      const targetName = node.target?.node_type === 'ArrayAccess'
        ? `${node.target.array_name}[ ]`
        : (node.target?.name || 'target');
      return {
        id: `assign_${Math.random().toString(36).substr(2, 6)}`,
        badge: badge || 'assign',
        title: 'ASSIGNMENT',
        value: `${targetName} =`,
        category: 'purple',
        children,
        raw: node
      };
    }

    case 'CompoundAssignment': {
      const children = [];
      if (node.target?.node_type === 'ArrayAccess') {
        children.push(convertASTNode(node.target, 'target'));
      }
      if (node.value) {
        children.push(convertASTNode(node.value, 'value'));
      }
      const targetName = node.target?.node_type === 'ArrayAccess'
        ? `${node.target.array_name}[ ]`
        : (node.target?.name || 'target');
      return {
        id: `casn_${Math.random().toString(36).substr(2, 6)}`,
        badge: badge || 'assign',
        title: 'COMPOUNDASSIGN',
        value: `${targetName} ${node.op || '+='}`,
        category: 'purple',
        children,
        raw: node
      };
    }

    case 'ForLoop': {
      const children = [];
      if (node.init) children.push(convertASTNode(node.init, 'init'));
      if (node.condition) children.push(convertASTNode(node.condition, 'condition'));
      if (node.update) children.push(convertASTNode(node.update, 'update'));
      if (node.body) children.push(convertASTNode(node.body, 'body'));
      return {
        id: `for_${Math.random().toString(36).substr(2, 6)}`,
        badge: badge || 'loop',
        title: 'FORLOOP',
        value: 'for ( ; ; )',
        category: 'purple',
        children,
        raw: node
      };
    }

    case 'WhileLoop': {
      const children = [];
      if (node.condition) children.push(convertASTNode(node.condition, 'condition'));
      if (node.body) children.push(convertASTNode(node.body, 'body'));
      return {
        id: `while_${Math.random().toString(36).substr(2, 6)}`,
        badge: badge || 'loop',
        title: 'WHILELOOP',
        value: 'while ( )',
        category: 'purple',
        children,
        raw: node
      };
    }

    case 'IfStatement': {
      const children = [];
      if (node.condition) children.push(convertASTNode(node.condition, 'condition'));
      if (node.then_branch) children.push(convertASTNode(node.then_branch, 'then'));
      if (node.else_branch) children.push(convertASTNode(node.else_branch, 'else'));
      return {
        id: `if_${Math.random().toString(36).substr(2, 6)}`,
        badge: badge || 'cond',
        title: 'IFSTATEMENT',
        value: 'if ( ... )',
        category: 'purple',
        children,
        raw: node
      };
    }

    case 'Block': {
      const children = [];
      if (node.statements) {
        node.statements.forEach((s, idx) => {
          children.push(convertASTNode(s, `stmt ${idx + 1}`, idx));
        });
      }
      return {
        id: `block_${Math.random().toString(36).substr(2, 6)}`,
        badge: badge || 'body',
        title: 'BLOCK',
        value: `${children.length} statement(s)`,
        category: 'purple',
        children,
        raw: node
      };
    }

    case 'BinaryOp': {
      const children = [];
      if (node.left) children.push(convertASTNode(node.left, 'left'));
      if (node.right) children.push(convertASTNode(node.right, 'right'));
      return {
        id: `bin_${Math.random().toString(36).substr(2, 6)}`,
        badge: badge || 'expr',
        title: 'BINARYEXPR',
        value: node.op || '?',
        category: 'amber',
        children,
        raw: node
      };
    }

    case 'UnaryOp': {
      const children = [];
      if (node.operand) children.push(convertASTNode(node.operand, 'operand'));
      return {
        id: `un_${Math.random().toString(36).substr(2, 6)}`,
        badge: badge || 'expr',
        title: 'UNARYEXPR',
        value: node.op || '?',
        category: 'amber',
        children,
        raw: node
      };
    }

    case 'ArrayAccess': {
      const children = [];
      if (node.index) children.push(convertASTNode(node.index, 'index'));
      return {
        id: `arracc_${Math.random().toString(36).substr(2, 6)}`,
        badge: badge || 'target',
        title: 'ARRAYACCESS',
        value: `${node.array_name}[ ]`,
        category: 'cyan',
        children,
        raw: node
      };
    }

    case 'Identifier': {
      return {
        id: `id_${node.name}_${Math.random().toString(36).substr(2, 6)}`,
        badge: badge || 'id',
        title: 'IDENTIFIER',
        value: node.name,
        category: 'cyan',
        children: [],
        raw: node
      };
    }

    case 'IntLiteral': {
      return {
        id: `lit_${node.value}_${Math.random().toString(36).substr(2, 6)}`,
        badge: badge || 'literal',
        title: 'NUMBERLITERAL',
        value: String(node.value),
        category: 'green',
        children: [],
        raw: node
      };
    }

    case 'ReturnStatement': {
      const children = [];
      if (node.value) children.push(convertASTNode(node.value, 'value'));
      return {
        id: `ret_${Math.random().toString(36).substr(2, 6)}`,
        badge: badge || 'stmt',
        title: 'RETURNSTMT',
        value: 'return',
        category: 'purple',
        children,
        raw: node
      };
    }

    case 'PrintStatement': {
      const children = [];
      if (node.expression) children.push(convertASTNode(node.expression, 'value'));
      return {
        id: `print_${Math.random().toString(36).substr(2, 6)}`,
        badge: badge || 'stmt',
        title: 'PRINTSTMT',
        value: 'print( )',
        category: 'purple',
        children,
        raw: node
      };
    }

    default: {
      return {
        id: `node_${Math.random().toString(36).substr(2, 6)}`,
        badge: badge || '',
        title: type.toUpperCase(),
        value: String(node.value || node.name || ''),
        category: 'purple',
        children: [],
        raw: node
      };
    }
  }
}

// Compute subtree widths bottom-up
function measureTree(node) {
  if (!node.children || node.children.length === 0) {
    node.subtreeWidth = CARD_W;
    return CARD_W;
  }
  let totalChildWidth = 0;
  node.children.forEach((child, i) => {
    totalChildWidth += measureTree(child);
    if (i > 0) totalChildWidth += GAP_X;
  });
  node.subtreeWidth = Math.max(CARD_W, totalChildWidth);
  return node.subtreeWidth;
}

// Layout tree coordinates top-down
function layoutTree(node, left, depth, flatNodes) {
  node.y = depth * (CARD_H + GAP_Y) + 36;

  if (!node.children || node.children.length === 0) {
    node.x = left + node.subtreeWidth / 2;
    flatNodes.push(node);
    return;
  }

  const childrenTotal =
    node.children.reduce((acc, c) => acc + c.subtreeWidth, 0) +
    (node.children.length - 1) * GAP_X;
  let childLeft = left + (node.subtreeWidth - childrenTotal) / 2;

  node.children.forEach((child) => {
    layoutTree(child, childLeft, depth + 1, flatNodes);
    childLeft += child.subtreeWidth + GAP_X;
  });

  const firstChild = node.children[0];
  const lastChild = node.children[node.children.length - 1];
  node.x = (firstChild.x + lastChild.x) / 2;
  flatNodes.push(node);
}

// Generate orthogonal SVG connector paths
function generateLines(node, paths = []) {
  if (node.children && node.children.length > 0) {
    const px = node.x;
    const py = node.y + CARD_H;
    const midY = py + GAP_Y / 2;
    const minX = Math.min(...node.children.map((c) => c.x));
    const maxX = Math.max(...node.children.map((c) => c.x));

    // Vertical stem down from parent
    paths.push(`M ${px} ${py} L ${px} ${midY}`);

    // Horizontal bus across children
    if (minX !== maxX) {
      paths.push(`M ${minX} ${midY} L ${maxX} ${midY}`);
    }

    // Vertical drops into each child
    node.children.forEach((child) => {
      paths.push(`M ${child.x} ${midY} L ${child.x} ${child.y}`);
      generateLines(child, paths);
    });
  }
  return paths;
}

// Extract statement list for Focus dropdown
function getStatementList(rawAst) {
  if (!rawAst) return [];
  const list = [];

  const addStmt = (s, idx) => {
    let preview = s.node_type;
    if (s.node_type === 'VarDecl') preview = `${s.type_name} ${s.name} = ...`;
    else if (s.node_type === 'ArrayDecl') preview = `${s.type_name} ${s.name}[${s.size}]`;
    else if (s.node_type === 'Assignment') preview = `${s.target?.name || 'target'} = ...`;
    else if (s.node_type === 'ForLoop') preview = 'for ( ; ; )';
    else if (s.node_type === 'WhileLoop') preview = 'while ( )';
    else if (s.node_type === 'IfStatement') preview = 'if ( ... )';
    else if (s.node_type === 'ReturnStatement') preview = `return ${s.value?.value ?? ''}`;
    else if (s.node_type === 'PrintStatement') preview = 'print( ... )';

    list.push({
      id: `stmt_${idx}`,
      index: idx,
      label: `Statement ${idx + 1}: ${preview}`,
      node: s
    });
  };

  if (rawAst.node_type === 'Program') {
    const func = rawAst.body?.find((b) => b.node_type === 'FunctionDef');
    if (func && func.body?.statements) {
      func.body.statements.forEach((s, idx) => addStmt(s, idx));
    } else if (rawAst.body) {
      rawAst.body.forEach((s, idx) => addStmt(s, idx));
    }
  } else if (rawAst.node_type === 'Block' && rawAst.statements) {
    rawAst.statements.forEach((s, idx) => addStmt(s, idx));
  }

  return list;
}

export const ASTViewer = ({ ast }) => {
  const [viewMode, setViewMode] = useState('tree'); // 'tree' or 'json'
  const [focusId, setFocusId] = useState('all');
  const [canvasTheme, setCanvasTheme] = useState('light'); // 'light' or 'dark'
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const containerRef = useRef(null);

  // Extract statements for focus dropdown
  const statementList = useMemo(() => getStatementList(ast), [ast]);

  // Build the display tree based on focus
  const visualTree = useMemo(() => {
    if (!ast) return null;

    if (focusId !== 'all') {
      const selected = statementList.find((s) => s.id === focusId);
      if (selected && selected.node) {
        return convertASTNode(selected.node, `stmt ${selected.index + 1}`, selected.index);
      }
    }

    return convertASTNode(ast);
  }, [ast, focusId, statementList]);

  // Calculate coordinates & SVG lines
  const { flatNodes, svgLines, bounds } = useMemo(() => {
    if (!visualTree) return { flatNodes: [], svgLines: [], bounds: { width: 400, height: 400 } };

    measureTree(visualTree);
    const nodes = [];
    layoutTree(visualTree, 40, 0, nodes);
    const lines = generateLines(visualTree);

    let maxX = 0;
    let maxY = 0;
    nodes.forEach((n) => {
      if (n.x + CARD_W / 2 > maxX) maxX = n.x + CARD_W / 2;
      if (n.y + CARD_H > maxY) maxY = n.y + CARD_H;
    });

    return {
      flatNodes: nodes,
      svgLines: lines,
      bounds: {
        width: Math.max(maxX + 60, 600),
        height: Math.max(maxY + 60, 420)
      }
    };
  }, [visualTree]);

  // Auto-fit on load or when tree changes
  const handleFit = useCallback(() => {
    if (!containerRef.current || !bounds) return;
    const containerW = containerRef.current.clientWidth || 700;
    const containerH = containerRef.current.clientHeight || 450;

    const scaleX = (containerW - 60) / bounds.width;
    const scaleY = (containerH - 60) / bounds.height;
    const newZoom = Math.min(Math.max(Math.min(scaleX, scaleY), 0.55), 1.15);

    const centerX = Math.max(0, (containerW - bounds.width * newZoom) / 2);
    const centerY = Math.max(10, (containerH - bounds.height * newZoom) / 2);

    setZoom(newZoom);
    setPan({ x: centerX, y: centerY });
  }, [bounds]);

  useEffect(() => {
    handleFit();
  }, [handleFit, focusId]);

  // Pan interaction
  const handleMouseDown = (e) => {
    if (e.button !== 0) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Wheel zoom
  const handleWheel = (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.08 : 0.92;
    setZoom((prev) => Math.min(Math.max(prev * zoomFactor, 0.4), 2.2));
  };

  if (!ast) {
    return <div className="empty-tab-state">No AST representation available.</div>;
  }

  return (
    <div className="ast-viewer-component">
      {/* Top Controls Toolbar */}
      <div className="ast-toolbar">
        <div className="ast-toolbar-left">
          <label htmlFor="ast-focus-select" className="ast-focus-label">
            Focus:
          </label>
          <select
            id="ast-focus-select"
            className="ast-focus-dropdown"
            value={focusId}
            onChange={(e) => setFocusId(e.target.value)}
          >
            <option value="all">
              Entire Program ({statementList.length} statement{statementList.length === 1 ? '' : 's'})
            </option>
            {statementList.map((stmt) => (
              <option key={stmt.id} value={stmt.id}>
                {stmt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="ast-toolbar-right">
          {/* Canvas Theme Toggle */}
          <button
            className="btn btn-ghost btn-sm ast-theme-btn"
            onClick={() => setCanvasTheme(canvasTheme === 'light' ? 'dark' : 'light')}
            title="Toggle Canvas Theme (Light matches website, Dark matches diagram screenshot)"
          >
            {canvasTheme === 'light' ? (
              <>
                <FaMoon size={12} />
                <span>Dark Canvas</span>
              </>
            ) : (
              <>
                <FaSun size={12} />
                <span>Light Canvas</span>
              </>
            )}
          </button>

          {/* Zoom & Fit Controls */}
          <div className="ast-zoom-controls">
            <button
              className="btn btn-icon btn-sm"
              onClick={() => setZoom((z) => Math.max(z - 0.15, 0.4))}
              title="Zoom Out"
            >
              <FaMinus size={11} />
            </button>
            <span className="zoom-percentage">{Math.round(zoom * 100)}%</span>
            <button
              className="btn btn-icon btn-sm"
              onClick={() => setZoom((z) => Math.min(z + 0.15, 2.2))}
              title="Zoom In"
            >
              <FaPlus size={11} />
            </button>
            <button
              className="btn btn-icon btn-sm"
              onClick={handleFit}
              title="Reset & Center View"
            >
              <FaArrowsRotate size={11} />
            </button>
          </div>

          {/* View Mode Toggle */}
          <div className="ast-view-toggle">
            <button
              className={`view-toggle-btn ${viewMode === 'tree' ? 'active' : ''}`}
              onClick={() => setViewMode('tree')}
            >
              <FaTree size={12} />
              <span>Tree Diagram</span>
            </button>
            <button
              className={`view-toggle-btn ${viewMode === 'json' ? 'active' : ''}`}
              onClick={() => setViewMode('json')}
            >
              <FaCode size={12} />
              <span>Raw JSON</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Diagram Canvas or JSON Raw View */}
      {viewMode === 'tree' ? (
        <div
          ref={containerRef}
          className={`ast-canvas-viewport ${canvasTheme === 'dark' ? 'canvas-dark' : 'canvas-light'}`}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
          style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
        >
          <div
            className="ast-tree-world"
            style={{
              width: `${bounds.width}px`,
              height: `${bounds.height}px`,
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              transformOrigin: '0 0'
            }}
          >
            {/* SVG Connector Lines */}
            <svg
              className="ast-svg-layer"
              width={bounds.width}
              height={bounds.height}
              style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}
            >
              {svgLines.map((pathData, idx) => (
                <path
                  key={`line_${idx}`}
                  d={pathData}
                  className={`ast-connector-path ${canvasTheme === 'dark' ? 'connector-dark' : 'connector-light'}`}
                />
              ))}
            </svg>

            {/* Node Cards Layer */}
            <div className="ast-nodes-layer">
              {flatNodes.map((n) => (
                <div
                  key={n.id}
                  className={`ast-node-card card-${n.category} ${canvasTheme === 'dark' ? 'node-dark' : 'node-light'}`}
                  style={{
                    position: 'absolute',
                    left: `${n.x - CARD_W / 2}px`,
                    top: `${n.y}px`,
                    width: `${CARD_W}px`,
                    height: `${CARD_H}px`
                  }}
                >
                  {n.badge && (
                    <div className={`node-badge badge-${n.category}`}>
                      {n.badge}
                    </div>
                  )}
                  <div className={`node-title text-${n.category}`}>
                    {n.title}
                  </div>
                  <div className="node-value" title={n.value}>
                    {n.value}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="ast-raw-container">
          <pre className="ast-json-pre">
            {JSON.stringify(ast, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default ASTViewer;
