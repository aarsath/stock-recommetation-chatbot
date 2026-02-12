import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const searchStock = async (query) => {
  const response = await api.get(`/search-stock?query=${query}`);
  return response.data;
};

export const getLivePrice = async (symbol) => {
  const response = await api.get(`/live-price/${symbol}`);
  return response.data;
};

export const getStockDetails = async (symbol) => {
  const response = await api.get(`/live-price/${symbol}`);
  const stockData = response.data?.data || {};

  return {
    symbol: stockData.symbol || symbol,
    name: stockData.name || symbol,
    ...stockData,
  };
};

export const getHistoricalData = async (symbol, days = 365) => {
  const response = await api.get(`/historical/${symbol}?days=${days}`);
  return response.data;
};

export const predictStock = async (symbol, days = 30, retrain = false) => {
  const response = await api.get(`/predict/${symbol}?days=${days}&retrain=${retrain}`);
  return response.data;
};


export const getPredictionIndicator = async (symbol, days = 5, retrain = false) => {
  const safeSymbol = encodeURIComponent(symbol || '');

  const toSignal = (pct) => {
    if (pct > 0.01) return { trend: 'INCREASE', trend_label: 'Increase', ai_signal: 'BUY' };
    if (pct < -0.01) return { trend: 'DECREASE', trend_label: 'Decrease', ai_signal: 'SELL' };
    return { trend: 'HOLD', trend_label: 'Stable', ai_signal: 'HOLD' };
  };

  const normalize = (payload, fallbackSymbol = symbol) => {
    const timeline = Array.isArray(payload?.future_predictions)
      ? payload.future_predictions
          .slice(0, Math.max(3, Math.min(days, 5)))
          .map((item, idx) => ({
            day: Number(item?.day ?? idx + 1),
            predicted_price: Number(item?.predicted_price ?? 0),
          }))
      : [];

    const current = Number(payload?.current_price ?? 0);
    const lastPred = Number(timeline[timeline.length - 1]?.predicted_price ?? current);
    const pct = current ? ((lastPred - current) / current) * 100 : 0;

    const signal = toSignal(pct);
    let confidence = Number(payload?.confidence_score ?? payload?.confidence ?? 35);
    confidence = confidence <= 1 ? confidence * 100 : confidence;

    return {
      success: true,
      symbol: payload?.symbol || fallbackSymbol,
      days: timeline.length || Math.max(3, Math.min(days, 5)),
      current_price: Number(current.toFixed(2)),
      future_predictions: timeline,
      trend: payload?.trend || signal.trend,
      trend_label: payload?.trend_label || signal.trend_label,
      percentage_change: Number((payload?.percentage_change ?? pct).toFixed(2)),
      confidence_score: Number(Math.max(0, Math.min(100, confidence)).toFixed(2)),
      ai_signal: payload?.ai_signal || signal.ai_signal,
    };
  };

  try {
    const response = await api.get(`/predict-indicator/${safeSymbol}?days=${days}&retrain=${retrain}`);
    return response.data;
  } catch (primaryError) {
    try {
      // Fallback 1: derive from existing /predict endpoint.
      const fallback = await api.get(`/predict/${safeSymbol}?days=${days}&retrain=${retrain}`);
      const payload = fallback.data || {};

      const timeline = Array.isArray(payload.predictions)
        ? payload.predictions
            .slice(0, Math.max(3, Math.min(days, 5)))
            .map((item, idx) => ({
              day: Number(item?.day ?? idx + 1),
              predicted_price: Number(item?.predicted_price ?? 0),
            }))
        : [];

      if (!timeline.length) {
        throw primaryError;
      }

      const nextDay = payload.next_day || {};
      const current = Number(nextDay.current_price ?? 0);
      const lastPred = Number(timeline[timeline.length - 1]?.predicted_price ?? current);
      const pct = current ? ((lastPred - current) / current) * 100 : 0;

      let confidence = Number(nextDay.confidence ?? 0);
      confidence = confidence <= 1 ? confidence * 100 : confidence;

      const signal = toSignal(pct);

      return {
        success: true,
        symbol: payload.symbol || symbol,
        days: timeline.length,
        current_price: Number(current.toFixed(2)),
        future_predictions: timeline.map((p) => ({
          day: p.day,
          predicted_price: Number(p.predicted_price.toFixed(2)),
        })),
        trend: signal.trend,
        trend_label: signal.trend_label,
        percentage_change: Number(pct.toFixed(2)),
        confidence_score: Number(Math.max(0, Math.min(100, confidence)).toFixed(2)),
        ai_signal: signal.ai_signal,
      };
    } catch (secondaryError) {
      // Fallback 2: heuristic projection from live price only.
      const liveRes = await api.get(`/live-price/${safeSymbol}`);
      const live = liveRes?.data?.data || {};
      const current = Number(live.price ?? 0);
      const changePct = Number(live.change_percent ?? 0);
      const projectedDailyReturn = Math.max(-0.03, Math.min(0.03, (changePct / 100) * 0.35));

      const timeline = [];
      let running = current;
      for (let i = 1; i <= Math.max(3, Math.min(days, 5)); i += 1) {
        running *= (1 + projectedDailyReturn);
        timeline.push({ day: i, predicted_price: Number(running.toFixed(2)) });
      }

      return normalize(
        {
          symbol: live.symbol || symbol,
          current_price: current,
          future_predictions: timeline,
          confidence_score: 35,
        },
        symbol
      );
    }
  }
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

export const chatWithAI = async (query, symbol, language, context = {}) => {
  const payload = {
    query,
    symbol,
    context,
  };
  if (language) payload.language = language;
  const response = await api.post('/chatbot', payload);
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

export const getPortfolioRecommendations = async (symbols, budget) => {
  const response = await api.post('/portfolio-recommendations', { symbols, budget });
  return response.data;
};

export default api;



