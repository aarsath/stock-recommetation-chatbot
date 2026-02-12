import React, { useEffect, useMemo, useState } from 'react';
import { generateCharts } from '../services/api';
import './Charts.css';

const chartTitleMap = {
  comprehensive: 'Comprehensive Technical Chart',
  prediction: 'Prediction Comparison',
};

const toTitle = (key) => {
  if (!key) return 'Chart';
  if (chartTitleMap[key]) return chartTitleMap[key];
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
};

const Charts = ({ symbol }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [chartUrls, setChartUrls] = useState({});

  useEffect(() => {
    const loadCharts = async () => {
      if (!symbol) {
        setChartUrls({});
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const response = await generateCharts(symbol);
        setChartUrls(response?.charts || {});
      } catch (err) {
        console.error('Chart load error:', err);
        setError('Failed to load matplotlib charts.');
        setChartUrls({});
      } finally {
        setLoading(false);
      }
    };

    loadCharts();
  }, [symbol]);

  const chartEntries = useMemo(() => Object.entries(chartUrls || {}), [chartUrls]);

  if (!symbol) {
    return <div className="no-data">Select a stock to view chart images.</div>;
  }

  if (loading) {
    return <div className="no-data">Generating matplotlib charts...</div>;
  }

  if (error) {
    return <div className="no-data">{error}</div>;
  }

  if (!chartEntries.length) {
    return <div className="no-data">No chart images available for this stock.</div>;
  }

  return (
    <div className="charts-container matplotlib-charts">
      {chartEntries.map(([key, url]) => (
        <div className="matplotlib-chart-box" key={key}>
          <div className="matplotlib-chart-title">{toTitle(key)}</div>
          <img src={url} alt={toTitle(key)} className="matplotlib-chart-image" loading="lazy" />
        </div>
      ))}
    </div>
  );
};

export default Charts;
