import React, { useState } from 'react';

const SAMPLES = [
  {
    id: 'sample_1',
    name: 'Sample 1',
    source_code: `int main() {
    int arr[4] = {10, 20, 30, 40};
    int sum = 0;

    for (int i = 0; i < 4; i++) {
        sum = sum + arr[i];
    }

    return 0;
}`
  },
  {
    id: 'sample_2',
    name: 'Sample 2',
    source_code: `int x = 15;
int y = 25;
int total = (x + y) * 2;

if (total > 50) {
    total = total - 10;
} else {
    total = total + 10;
}

print(total);`
  },
  {
    id: 'sample_syntax_err',
    name: 'Syntax Error Test',
    source_code: `int a = 10
int b = 20;
int c = a + b;`
  },
  {
    id: 'sample_semantic_err',
    name: 'Semantic Error Test',
    source_code: `int x = 10;
int y = 20;
total = x + y;`
  }
];

export const ExampleSelector = ({ onSelect }) => {
  const [selectedId, setSelectedId] = useState('sample_1');

  const handleChange = (e) => {
    const id = e.target.value;
    setSelectedId(id);
    const found = SAMPLES.find((s) => s.id === id);
    if (found && onSelect) {
      onSelect(found.source_code, found);
    }
  };

  return (
    <div className="example-selector-wrapper">
      <div className="example-selector-header">
        <label htmlFor="example-select" className="example-label">
          <strong>Load Sample:</strong>
        </label>
        <select
          id="example-select"
          className="example-dropdown"
          value={selectedId}
          onChange={handleChange}
        >
          {SAMPLES.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};

export default ExampleSelector;
