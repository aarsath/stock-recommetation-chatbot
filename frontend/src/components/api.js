import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes for ML operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// API Functions
export const searchStock = async (query) => {
  const response = await api.get(`/search-stock?query=${query}`);
  return response.data;
};

export const getLivePrice = async (symbol) => {
  const response = await api.get(`/live-price/${symbol}`);
  return response.data;
};

export const getHistoricalData = async (symbol, days = 365) => {
  const response = await api.get(`/historical/${symbol}?days=${days}`);
  return response.data;
};

export const predictStock = async (symbol, days = 30, retrain = false) => {
  const response = await api.get(`/predict/${symbol}?days=${days}&retrain=${retrain}`);
  return response.data;
};

export const getRecommendation = async (symbol) => {
  const response = await api.get(`/recommend/${symbol}`);
  return response.data;
};

export const getAnalysis = async (symbol) => {
  const response = await api.get(`/analyze/${symbol}`);
  return response.data;
};

export const generateCharts = async (symbol) => {
  const response = await api.get(`/charts/${symbol}`);
  return response.data;
};

export const chatWithAI = async (query, symbol) => {
  const response = await api.post('/chat', { query, symbol });
  return response.data;
};

export const loadLLMModel = async () => {
  const response = await api.post('/load-llm');
  return response.data;
};

export const getIndices = async () => {
  const response = await api.get('/indices');
  return response.data;
};

export const getPopularStocks = async () => {
  const response = await api.get('/popular-stocks');
  return response.data;
};

export default api;
