import React, { useState } from 'react';
import { FaChevronDown, FaChevronRight } from 'react-icons/fa6';

const TreeNode = ({ nodeKey, data, depth = 0 }) => {
  const [collapsed, setCollapsed] = useState(depth > 2);

  const isObject = data !== null && typeof data === 'object';
  const isArray = Array.isArray(data);

  if (!isObject) {
    return (
      <div className="tree-leaf" style={{ paddingLeft: `${depth * 16}px` }}>
        {nodeKey && <span className="tree-key">{nodeKey}: </span>}
        <span className={`tree-val tree-val-${typeof data}`}>
          {typeof data === 'string' ? `"${data}"` : String(data)}
        </span>
      </div>
    );
  }

  const keys = Object.keys(data);
  const nodeType = data.type || data.node_type || (isArray ? `Array[${data.length}]` : 'Node');

  return (
    <div className="tree-node">
      <div
        className="tree-node-header"
        style={{ paddingLeft: `${depth * 16}px` }}
        onClick={() => setCollapsed(!collapsed)}
      >
        <span className="tree-toggle-icon">
          {collapsed ? <FaChevronRight size={10} /> : <FaChevronDown size={10} />}
        </span>
        {nodeKey && <span className="tree-key">{nodeKey}: </span>}
        <span className="tree-type-tag">{nodeType}</span>
        {isArray && <span className="tree-count">({data.length} items)</span>}
      </div>

      {!collapsed && (
        <div className="tree-children">
          {keys.map((k) => (
            <TreeNode key={k} nodeKey={k} data={data[k]} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
};

export const ASTViewer = ({ ast }) => {
  const [viewMode, setViewMode] = useState('tree'); // 'tree' or 'json'

  if (!ast) {
    return <div className="empty-tab-state">No AST representation available.</div>;
  }

  // Handle if ast is a string (e.g. from print_ast)
  if (typeof ast === 'string') {
    return (
      <div className="ast-viewer-container">
        <pre className="code-block-display">{ast}</pre>
      </div>
    );
  }

  return (
    <div className="ast-viewer-container">
      <div className="tab-actions-bar">
        <div className="btn-group">
          <button
            className={`btn btn-sm ${viewMode === 'tree' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setViewMode('tree')}
          >
            Visual Tree
          </button>
          <button
            className={`btn btn-sm ${viewMode === 'json' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setViewMode('json')}
          >
            JSON Raw
          </button>
        </div>
      </div>

      <div className="ast-content">
        {viewMode === 'tree' ? (
          <div className="interactive-tree">
            <TreeNode nodeKey="Root" data={ast} depth={0} />
          </div>
        ) : (
          <pre className="code-block-display">
            {JSON.stringify(ast, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
};

export default ASTViewer;
