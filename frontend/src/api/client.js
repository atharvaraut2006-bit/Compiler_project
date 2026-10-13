import axios from 'axios';
import { runLocalCompilation } from './localCompiler';

const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '/api' : 'http://localhost:8000/api');

const FALLBACK_EXAMPLES = [
  {
    id: "sample_1",
    name: "Sample 1: Array Summation",
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
    id: "sample_add",
    name: "Benchmark: Array Addition",
    source_code: `int main() {
    int a[4] = {1, 2, 3, 4};
    int b[4] = {10, 20, 30, 40};
    int c[4] = {0, 0, 0, 0};

    for (int i = 0; i < 4; i++) {
        c[i] = a[i] + b[i];
    }

    return 0;
}`
  },
  {
    id: "sample_scale",
    name: "Benchmark: Array Scaling",
    source_code: `int main() {
    int weights[4] = {5, 10, 15, 20};
    int factor = 3;

    for (int i = 0; i < 4; i++) {
        weights[i] = weights[i] * factor;
    }

    return 0;
}`
  },
  {
    id: "sample_large",
    name: "Benchmark: Large Array (32 Elements - PIM Speedup)",
    source_code: `int main() {
    int data[32] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32};
    int total = 0;

    for (int i = 0; i < 32; i++) {
        total = total + data[i];
    }

    return 0;
}`
  },
  {
    id: "sample_fallback",
    name: "Benchmark: CPU Fallback (Division)",
    source_code: `int main() {
    int arr[4] = {100, 200, 300, 400};
    int result = 0;

    for (int i = 0; i < 4; i++) {
        int val = arr[i] / 10;
        result = result + val;
    }

    return 0;
}`
  },
  {
    id: "sample_2",
    name: "Sample 2: Conditional Branching",
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
    id: "sample_stdio_functions",
    name: "Extended C: #include <stdio.h> & Functions",
    source_code: `#include <stdio.h>
#define N 4

int compute_square(int x) {
    return x * x;
}

int main() {
    int arr[N] = {2, 4, 6, 8};
    int total = 0;

    for (int i = 0; i < N; i++) {
        total += compute_square(arr[i]);
    }

    printf("Sum of squares: %d\\n", total);
    return 0;
}`
  },
  {
    id: "sample_pointers_structs",
    name: "Extended C: Pointers & Structs",
    source_code: `#include <stdio.h>

struct Vector2D {
    int x;
    int y;
};

int main() {
    struct Vector2D v;
    v.x = 15;
    v.y = 25;

    int *px = &v.x;
    *px = 30;

    int arr[2] = {v.x, v.y};
    int magnitude_squared = arr[0] * arr[0] + arr[1] * arr[1];

    printf("Magnitude squared: %d\\n", magnitude_squared);
    return 0;
}`
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

export const evaluatePerformance = async (sourceCode, customParams = null) => {
  try {
    const response = await axios.post(
      `${API_BASE}/evaluate`,
      { source_code: sourceCode, custom_params: customParams },
      { timeout: 7000 }
    );
    return response.data;
  } catch (err) {
    if (err.response && err.response.data && err.response.data.performance) {
      return err.response.data.performance;
    }
    const localResult = runLocalCompilation(sourceCode, customParams);
    return localResult.performance;
  }
};

