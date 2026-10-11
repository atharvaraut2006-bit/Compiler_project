import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const checkHealth = async () => {
  const response = await axios.get(`${API_BASE}/health`);
  return response.data;
};

export const getExamples = async () => {
  const response = await axios.get(`${API_BASE}/examples`);
  return response.data;
};

export const compileCode = async (sourceCode) => {
  const response = await axios.post(`${API_BASE}/compile`, { source_code: sourceCode });
  return response.data;
};
