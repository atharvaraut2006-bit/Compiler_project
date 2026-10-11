import React, { useState, useEffect } from 'react';
import { getExamples } from '../api/client';

const PHASE1_EXAMPLES = [
  {
    id: 'array_summation_main',
    name: '1. Array Reduction (Summation)',
    category: 'valid',
    description: 'Computes sum of array elements using a for-loop accumulator with int main().',
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
    id: 'simple_arithmetic',
    name: '2. Valid Simple Arithmetic & Control Flow',
    category: 'valid',
    description: 'Standard arithmetic expressions, parenthesization, conditionals, and built-in print.',
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
    id: 'syntax_error_missing_semicolon',
    name: '3. Invalid Syntax (Missing Semicolon Error)',
    category: 'invalid_syntax',
    description: 'Demonstrates parser syntax diagnostic when a semicolon is omitted after variable declaration.',
    source_code: `int a = 10
int b = 20;
int c = a + b;`
  },
  {
    id: 'semantic_error_undeclared',
    name: '4. Invalid Semantic (Undeclared Variable Error)',
    category: 'invalid_semantic',
    description: 'Demonstrates semantic analyzer error detection when assigning to an undeclared identifier.',
    source_code: `int x = 10;
int y = 20;
total = x + y;`
  }
];

export const ExampleSelector = ({ onSelect }) => {
  const [examples, setExamples] = useState(PHASE1_EXAMPLES);
  const [selectedId, setSelectedId] = useState(PHASE1_EXAMPLES[0].id);

  useEffect(() => {
    getExamples()
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setExamples(data);
        }
      })
      .catch((err) => {
        console.warn('Using local fallback examples:', err);
      });
  }, []);

  const handleChange = (e) => {
    const id = e.target.value;
    setSelectedId(id);
    const found = examples.find((ex) => ex.id === id);
    if (found && onSelect) {
      onSelect(found.source_code, found);
    }
  };

  const selectedExample = examples.find((ex) => ex.id === selectedId);

  return (
    <div className="example-selector-wrapper">
      <div className="example-selector-header">
        <label htmlFor="example-select" className="example-label">
          <strong>Select Sample Program:</strong>
        </label>
        <select
          id="example-select"
          className="example-dropdown"
          value={selectedId}
          onChange={handleChange}
        >
          {examples.map((ex) => (
            <option key={ex.id} value={ex.id}>
              {ex.name}
            </option>
          ))}
        </select>
      </div>
      {selectedExample && (
        <p className="example-description-text">{selectedExample.description}</p>
      )}
    </div>
  );
};

export default ExampleSelector;
