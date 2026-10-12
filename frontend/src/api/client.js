import axios from 'axios';
import { runLocalCompilation } from './localCompiler';

const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '/api' : 'http://localhost:8000/api');

const FALLBACK_EXAMPLES = [
  {
    id: "sample_1",
    name: "Sample 1",
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
    id: "sample_2",
    name: "Sample 2",
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
    id: "sample_syntax_err",
    name: "Syntax Error Test",
    source_code: `int a = 10
int b = 20;
int c = a + b;`
  },
  {
    id: "sample_semantic_err",
    name: "Semantic Error Test",
    source_code: `int x = 10;
int y = 20;
total = x + y;`
  }
];

export const checkHealth = async () => {
  try {
    const response = await axios.get(`${API_BASE}/health`, { timeout: 3500 });
    return response.data;
  } catch (err) {
    return { status: "local", service: "In-Browser Compiler Engine", version: "1.0.0" };
  }
};

export const getExamples = async () => {
  try {
    const response = await axios.get(`${API_BASE}/examples`, { timeout: 3500 });
    return response.data;
  } catch (err) {
    return FALLBACK_EXAMPLES;
  }
};

export const compileCode = async (sourceCode) => {
  try {
    const response = await axios.post(
      `${API_BASE}/compile`,
      { source_code: sourceCode },
      { timeout: 7000 }
    );
    return response.data;
  } catch (err) {
    // If the server explicitly responded with an HTTP status (e.g. 400 or 500), check response
    if (err.response && err.response.data && err.response.data.stages) {
      return err.response.data;
    }

    // Network error, mixed-content block, serverless cold-start timeout, or connection refused
    // Seamlessly fall back to the in-browser compilation & simulation engine!
    console.warn("Backend unavailable or network error encountered. Falling back to in-browser compiler engine:", err.message);
    const localResult = runLocalCompilation(sourceCode);
    return localResult;
  }
};

export const simulateCode = async (sourceCode) => {
  try {
    const response = await axios.post(
      `${API_BASE}/simulate`,
      { source_code: sourceCode },
      { timeout: 7000 }
    );
    return response.data;
  } catch (err) {
    const localResult = runLocalCompilation(sourceCode);
    return localResult.simulation;
  }
};
