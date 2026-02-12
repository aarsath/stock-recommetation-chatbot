import React, { useState, useEffect, useRef } from 'react';
import {
  getLivePrice,
  predictStock,
  getRecommendation,
  getAnalysis,
  getPortfolioRecommendations,
  getPopularStocks,
  getPredictionIndicator,
} from '../services/api';
import Charts from './Charts';
import ChatBot from './ChatBot';
import StockSearch from './StockSearch';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import RefreshIcon from '@mui/icons-material/Refresh';
import './Dashboard.css';

const Dashboard = () => {
  const [selectedSymbol, setSelectedSymbol] = useState(null);
  const [liveData, setLiveData] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [recommendation, setRecommendation] = useState(null);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [showPlannerView, setShowPlannerView] = useState(false);
  const [userName, setUserName] = useState('');
  const [investAmount, setInvestAmount] = useState('');
  const [portfolioSymbols, setPortfolioSymbols] = useState('');
  const [portfolioData, setPortfolioData] = useState(null);
  const [portfolioLoading, setPortfolioLoading] = useState(false);
  const [portfolioError, setPortfolioError] = useState(null);
  const [selectedStock, setSelectedStock] = useState(null);
  const [rightPanelData, setRightPanelData] = useState(null);
  const [predictionIndicatorLoading, setPredictionIndicatorLoading] = useState(false);
  const [predictionIndicatorError, setPredictionIndicatorError] = useState(null);
  const [popularLoading, setPopularLoading] = useState(false);
  const [plannerStep, setPlannerStep] = useState('name');
  const [plannerInput, setPlannerInput] = useState('');
  const [plannerMessages, setPlannerMessages] = useState([
    {
      role: 'assistant',
      text: "Hi there! Welcome to your personal Investment Planner. To get started, may I know your name?",
    },
  ]);
  const plannerEndRef = useRef(null);
  const loadRequestRef = useRef(0);

  useEffect(() => {
    if (selectedSymbol) {
      loadStockData(selectedSymbol);
    }
  }, [selectedSymbol]);

  const loadStockData = async (symbol) => {
    const requestId = loadRequestRef.current + 1;
    loadRequestRef.current = requestId;

    setLoading(true);
    setError(null);

    try {
      const [liveRes, recommendationRes] = await Promise.allSettled([
        getLivePrice(symbol),
        getRecommendation(symbol),
      ]);

      if (requestId !== loadRequestRef.current) return;

      if (liveRes.status === 'fulfilled') {
        setLiveData(liveRes.value.data);
      }

      if (recommendationRes.status === 'fulfilled') {
        setRecommendation(recommendationRes.value.recommendation);
      }

      if (liveRes.status !== 'fulfilled' && recommendationRes.status !== 'fulfilled') {
        setError('Failed to load stock data. Please try again.');
      }
    } catch (err) {
      if (requestId !== loadRequestRef.current) return;
      console.error('Fast load error:', err);
      setError('Failed to load stock data. Please try again.');
    } finally {
      if (requestId === loadRequestRef.current) {
        setLoading(false);
      }
    }

    Promise.allSettled([
      predictStock(symbol, 30, false),
      getPredictionIndicator(symbol, 5, false),
      getAnalysis(symbol),
    ]).then(([predictionRes, indicatorRes, analysisRes]) => {
      if (requestId !== loadRequestRef.current) return;

      const mlPredictions =
        predictionRes.status === 'fulfilled' && Array.isArray(predictionRes.value?.predictions)
          ? predictionRes.value.predictions
          : [];

      if (mlPredictions.length > 0) {
        setPrediction(mlPredictions);
      } else if (
        indicatorRes.status === 'fulfilled' &&
        indicatorRes.value?.success &&
        Array.isArray(indicatorRes.value?.future_predictions)
      ) {
        const derived = indicatorRes.value.future_predictions.map((item, idx) => ({
          day: Number(item?.day ?? idx + 1),
          predicted_price: Number(item?.predicted_price ?? 0),
        }));
        setPrediction(derived);
      } else {
        setPrediction([]);
      }

      if (analysisRes.status === 'fulfilled') {
        setAiAnalysis(analysisRes.value.ai_analysis);
      }
    }).catch((err) => {
      if (requestId !== loadRequestRef.current) return;
      console.error('Background load error:', err);
    });
  };

  const handleRefresh = () => {
    if (selectedSymbol) {
      loadStockData(selectedSymbol);
    }
  };

  const getRecommendationClass = (rec) => {
    if (!rec) return '';
    if (rec.includes('STRONG BUY') || rec.includes('BUY')) return 'rec-buy';
    if (rec.includes('SELL')) return 'rec-sell';
    return 'rec-hold';
  };

  const toNumber = (value) => {
    const num = Number.parseFloat(value);
    return Number.isFinite(num) ? num : null;
  };

  const formatMoney = (value) => (Number.isFinite(value) ? value.toFixed(2) : '--');
  const formatNumber = (value) => (Number.isFinite(value) ? value.toLocaleString() : '--');

  const numericInvestAmount = Number.parseFloat(investAmount);
  const hasBudget = Number.isFinite(numericInvestAmount) && numericInvestAmount > 0;

  const livePriceValue = toNumber(liveData?.price);
  const liveChange = toNumber(liveData?.change);
  const liveChangePercent = toNumber(liveData?.change_percent);
  const liveOpen = toNumber(liveData?.open);
  const liveHigh = toNumber(liveData?.high);
  const liveLow = toNumber(liveData?.low);
  const weekHigh = toNumber(liveData?.week_52_high);
  const weekLow = toNumber(liveData?.week_52_low);
  const liveVolume = toNumber(liveData?.volume);

  const buyableShares = hasBudget && livePriceValue ? Math.floor(numericInvestAmount / livePriceValue) : 0;
  const remainingBudget = hasBudget && livePriceValue ? numericInvestAmount - buyableShares * livePriceValue : null;

  const recText = recommendation?.recommendation || '';
  const isSellSignal = recText.includes('SELL');

  useEffect(() => {
    if (plannerEndRef.current) {
      plannerEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [plannerMessages]);

  const appendPlannerMessage = (role, text) => {
    setPlannerMessages((prev) => [...prev, { role, text }]);
  };

  const handlePlannerQuickFill = (value) => {
    setPlannerInput(value);
  };

  const handlePlannerSubmit = () => {
    const answer = plannerInput.trim();
    if (!answer) return;

    appendPlannerMessage('user', answer);
    setPlannerInput('');

    if (plannerStep === 'name') {
      if (answer.length < 2) {
        appendPlannerMessage('assistant', 'Please enter at least 2 characters so I can personalize your plan.');
        return;
      }

      setUserName(answer);
      setPlannerStep('goal');
      appendPlannerMessage(
        'assistant',
        `Nice to meet you, ${answer}! What is your primary financial goal? Example: retirement, buying a house, child education, or wealth creation.`
      );
      return;
    }

    if (plannerStep === 'goal') {
      setPlannerStep('horizon');
      appendPlannerMessage(
        'assistant',
        'Great goal. In how many years do you want to achieve this? Enter a number like 10, 15, or 20.'
      );
      return;
    }

    if (plannerStep === 'horizon') {
      const years = Number.parseInt(answer, 10);
      if (!Number.isFinite(years) || years < 1 || years > 60) {
        appendPlannerMessage('assistant', 'Please enter a valid time horizon in years between 1 and 60.');
        return;
      }

      setPlannerStep('risk');
      appendPlannerMessage(
        'assistant',
        'Understood. What is your risk tolerance: Low, Medium, or High?'
      );
      return;
    }

    if (plannerStep === 'risk') {
      const normalizedRisk = answer.toLowerCase();
      const riskValue = normalizedRisk.includes('low')
        ? 'Low'
        : normalizedRisk.includes('high')
          ? 'High'
          : normalizedRisk.includes('med')
            ? 'Medium'
            : null;

      if (!riskValue) {
        appendPlannerMessage('assistant', 'Please choose one of: Low, Medium, or High.');
        return;
      }

      setPlannerStep('monthly');
      appendPlannerMessage(
        'assistant',
        'Perfect. What approximate amount can you invest now (Rs)? You can enter values like 5000 or 25000.'
      );
      return;
    }

    if (plannerStep === 'monthly') {
      const amount = Number.parseFloat(answer.replace(/,/g, ''));
      if (!Number.isFinite(amount) || amount <= 0) {
        appendPlannerMessage('assistant', 'Please enter a valid positive amount in rupees.');
        return;
      }

      setInvestAmount(String(amount));
      setPlannerStep('symbols');
      appendPlannerMessage(
        'assistant',
        'Great. Enter preferred stock symbols separated by commas (example: RELIANCE, TCS, INFY). You can type "popular" to auto-fill.'
      );
      return;
    }

    if (plannerStep === 'symbols') {
      if (answer.toLowerCase() === 'popular') {
        handleUsePopularStocks();
        setPlannerStep('complete');
        appendPlannerMessage(
          'assistant',
          'Loaded popular stocks. Click "Build Portfolio Recommendation" below when ready.'
        );
        return;
      }

      const symbols = answer
        .split(',')
        .map((item) => item.trim().toUpperCase())
        .filter(Boolean);

      if (!symbols.length) {
        appendPlannerMessage('assistant', 'Please enter at least one valid symbol.');
        return;
      }

      setPortfolioSymbols(symbols.join(', '));
      setPlannerStep('complete');
      appendPlannerMessage(
        'assistant',
        `Thanks${userName ? `, ${userName}` : ''}. I now have your plan inputs. Click "Build Portfolio Recommendation" for your allocation suggestion.`
      );
      return;
    }

    appendPlannerMessage('assistant', 'Your planner inputs are ready. You can build or refresh your portfolio recommendation now.');
  };

  const handlePlannerKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handlePlannerSubmit();
    }
  };

  const handlePlannerReset = () => {
    setPlannerStep('name');
    setPlannerInput('');
    setUserName('');
    setInvestAmount('');
    setPortfolioSymbols('');
    setPlannerMessages([
      {
        role: 'assistant',
        text: "Hi there! Welcome to your personal Investment Planner. To get started, may I know your name?",
      },
    ]);
  };

  const handleUsePopularStocks = async () => {
    setPopularLoading(true);
    setPortfolioError(null);

    try {
      const response = await getPopularStocks();
      const allSymbols = [
        ...(response.nifty_50 || []),
        ...(response.bank_nifty || []),
        ...(response.popular || []),
      ];
      const unique = Array.from(new Set(allSymbols.map((s) => s.trim().toUpperCase()))).filter(
        Boolean
      );

      if (!unique.length) {
        setPortfolioError('No popular stocks found right now.');
        return;
      }

      setPortfolioSymbols(unique.join(', '));
      appendPlannerMessage('assistant', `Loaded ${unique.length} popular stocks for your portfolio.`);
    } catch (err) {
      console.error('Popular stocks error:', err);
      setPortfolioError('Failed to load popular stocks.');
    } finally {
      setPopularLoading(false);
    }
  };

  const handlePortfolioRecommendation = async () => {
    setPortfolioError(null);
    setPortfolioData(null);
    setSelectedStock(null);
    setRightPanelData(null);
    setPredictionIndicatorError(null);

    const budgetValue = Number.parseFloat(investAmount);
    if (!Number.isFinite(budgetValue) || budgetValue <= 0) {
      setPortfolioError('Enter a valid investment amount.');
      return;
    }

    const symbolList = portfolioSymbols
      .split(',')
      .map((item) => item.trim().toUpperCase())
      .filter(Boolean);

    if (selectedSymbol) {
      const normalizedSelected = selectedSymbol.trim().toUpperCase();
      if (!symbolList.includes(normalizedSelected)) {
        symbolList.unshift(normalizedSelected);
      }
    }

    if (!symbolList.length) {
      setPortfolioError('Add at least one stock symbol.');
      return;
    }

    setPortfolioLoading(true);
    try {
      const response = await getPortfolioRecommendations(symbolList, budgetValue);
      setPortfolioData(response);
    } catch (err) {
      console.error('Portfolio recommendation error:', err);
      setPortfolioError('Failed to load portfolio recommendation.');
    } finally {
      setPortfolioLoading(false);
    }
  };

  const openPortfolioStockView = (symbol, tab = 'overview') => {
    if (!symbol) return;
    setSelectedSymbol(symbol);
    setActiveTab(tab);
  };

  const handlePortfolioDetailOpen = async (item) => {
    if (!item || item.error) return;

    const live = item.live_price || {};
    const selected = item.symbol || null;

    setSelectedStock(selected);
    setPredictionIndicatorError(null);
    setRightPanelData({
      symbol: selected || '--',
      companyName: item.name || selected || '--',
      livePrice: toNumber(live.price),
      dayChangePercent: toNumber(live.change_percent),
      volume: toNumber(live.volume),
      predictionIndicator: null,
    });

    if (!selected) return;

    setPredictionIndicatorLoading(true);
    try {
      const indicator = await getPredictionIndicator(selected, 5, false);
      setRightPanelData((prev) => {
        if (!prev || prev.symbol !== selected) return prev;
        return {
          ...prev,
          predictionIndicator: indicator?.success ? indicator : null,
        };
      });
      if (!indicator?.success) {
        setPredictionIndicatorError('Prediction indicator unavailable for this stock.');
      }
    } catch (err) {
      console.error('Prediction indicator error:', err);
      setPredictionIndicatorError(err?.response?.data?.error || 'Failed to load prediction indicator.');
    } finally {
      setPredictionIndicatorLoading(false);
    }
  };

  const getSuggestedPortfolioStocks = () => {
    const allocations = portfolioData?.allocations || [];
    const valid = allocations.filter((item) => !item.error && item.recommendation);

    const buyFirst = valid
      .filter((item) => {
        const rec = (item.recommendation?.recommendation || '').toUpperCase();
        return rec.includes('BUY') || rec.includes('HOLD');
      })
      .sort((a, b) => (toNumber(b?.recommendation?.score) || 0) - (toNumber(a?.recommendation?.score) || 0));

    const fallback = valid
      .sort((a, b) => (toNumber(b?.recommendation?.score) || 0) - (toNumber(a?.recommendation?.score) || 0));

    return (buyFirst.length ? buyFirst : fallback).slice(0, 5);
  };
  const investmentPlanner = (
    <div className="investment-card">
      <div className="investment-header planner-header-row">
        <div>
          <h3>Investment Planner Assistant</h3>
          <p>Answer a few guided questions and I will prepare your portfolio inputs.</p>
          <div className="investment-meta">
            {selectedSymbol ? (
              <>
                Selected stock context: <strong>{selectedSymbol}</strong>
                {livePriceValue ? ` (Rs ${formatMoney(livePriceValue)})` : ''}
              </>
            ) : (
              'No stock selected yet. You can still build a diversified portfolio.'
            )}
          </div>
        </div>
        <button type="button" className="portfolio-btn secondary" onClick={handlePlannerReset}>
          Restart Chat
        </button>
      </div>

      <div className="planner-chat-window">
        {plannerMessages.map((message, index) => (
          <div key={`${message.role}-${index}`} className={`planner-message ${message.role}`}>
            <div className="planner-role">{message.role === 'assistant' ? 'Planner' : 'You'}</div>
            <div className="planner-text">{message.text}</div>
          </div>
        ))}
        <div ref={plannerEndRef} />
      </div>

      <div className="planner-input-row">
        <textarea
          value={plannerInput}
          onChange={(event) => setPlannerInput(event.target.value)}
          onKeyDown={handlePlannerKeyDown}
          rows={2}
          placeholder="Type your answer and press Enter..."
        />
        <button type="button" className="portfolio-btn" onClick={handlePlannerSubmit}>
          Send
        </button>
      </div>

      <div className="planner-budget-box">
        <label htmlFor="plannerBudget">Investment Amount (Rs)</label>
        <input
          id="plannerBudget"
          type="number"
          min="0"
          step="0.01"
          value={investAmount}
          onChange={(event) => setInvestAmount(event.target.value)}
          placeholder="Enter budget amount"
        />
      </div>

      <div className="planner-symbols-box">
        <label htmlFor="plannerSymbols">Portfolio Symbols (comma separated)</label>
        <input
          id="plannerSymbols"
          type="text"
          value={portfolioSymbols}
          onChange={(event) => setPortfolioSymbols(event.target.value.toUpperCase())}
          placeholder="RELIANCE.NS, TCS.NS, INFY.NS"
        />
      </div>

      {plannerStep === 'risk' && (
        <div className="planner-quick-actions">
          <button type="button" className="portfolio-btn secondary" onClick={() => handlePlannerQuickFill('Low')}>
            Low Risk
          </button>
          <button type="button" className="portfolio-btn secondary" onClick={() => handlePlannerQuickFill('Medium')}>
            Medium Risk
          </button>
          <button type="button" className="portfolio-btn secondary" onClick={() => handlePlannerQuickFill('High')}>
            High Risk
          </button>
        </div>
      )}
      <div className="investment-actions">
        <button
          className="portfolio-btn"
          type="button"
          onClick={handlePortfolioRecommendation}
          disabled={portfolioLoading}
        >
          {portfolioLoading ? 'Building Portfolio...' : 'Build Portfolio Recommendation'}
        </button>
        <button
          className="portfolio-btn secondary"
          type="button"
          onClick={handleUsePopularStocks}
          disabled={popularLoading}
        >
          {popularLoading ? 'Loading Popular...' : 'Use Popular Stocks'}
        </button>
      </div>

      <div className="investment-result">
        {isSellSignal && (
          <div className="result-note negative">
            AI signal suggests SELL for the selected stock. Consider waiting before buying this one.
          </div>
        )}
        {!isSellSignal && hasBudget && livePriceValue ? (
          <div className="result-note positive">
            {userName ? `${userName}, ` : ''}
            at Rs {formatMoney(livePriceValue)} you can buy up to <strong>{buyableShares}</strong> shares.
            {remainingBudget !== null ? (
              buyableShares > 0 ? (
                <span> Estimated balance: Rs {formatMoney(remainingBudget)}</span>
              ) : (
                <span> Budget is below current price. Balance: Rs {formatMoney(remainingBudget)}</span>
              )
            ) : null}
          </div>
        ) : (
          !isSellSignal && (
            <div className="result-note neutral">
              {selectedSymbol
                ? 'Complete the planner flow and enter an amount to see buyable shares.'
                : 'You can finish the planner flow even without selecting a stock.'}
            </div>
          )
        )}
        {portfolioError && <div className="result-note negative">{portfolioError}</div>}
        {portfolioData?.allocations && (
          <div className="portfolio-results">
            {getSuggestedPortfolioStocks().length > 0 && (
              <div className="portfolio-suggested">
                <div className="portfolio-suggested-title">Suggested Stocks</div>
                <div className="portfolio-suggested-list">
                  {getSuggestedPortfolioStocks().map((item) => (
                    <button
                      key={`suggest-${item.symbol}`}
                      type="button"
                      className="suggested-stock-btn"
                      onClick={() => openPortfolioStockView(item.symbol, 'overview')}
                    >
                      <span>{item.symbol}</span>
                      <small>{item.recommendation?.recommendation || 'N/A'}</small>
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="portfolio-two-panel">
              <div className="portfolio-middle-panel">
                {portfolioData.allocations.map((item) => (
                  <div
                    key={item.symbol}
                    className={`portfolio-select-row ${item.error ? 'error' : ''} ${selectedStock === item.symbol ? 'active' : ''}`}
                  >
                    <div className="portfolio-select-main">
                      <div className="portfolio-select-symbol">{item.symbol}</div>
                      <div className="portfolio-select-reco">
                        {item.error ? item.error : item.recommendation?.recommendation || 'N/A'}
                      </div>
                    </div>
                    <button
                      type="button"
                      className="portfolio-arrow-btn"
                      onClick={() => handlePortfolioDetailOpen(item)}
                      disabled={!!item.error}
                      title="Open details"
                    >
                      <span aria-hidden="true">&#9654;</span>
                    </button>
                  </div>
                ))}
              </div>

              <div className="portfolio-right-panel">
                {rightPanelData ? (
                  <div className="portfolio-detail-card">
                    <div className="portfolio-detail-title">{rightPanelData.symbol}</div>
                    <div className="portfolio-detail-item">
                      <span>Company Name</span>
                      <strong>{rightPanelData.companyName}</strong>
                    </div>
                    <div className="portfolio-detail-item">
                      <span>Live Price</span>
                      <strong>Rs {formatMoney(rightPanelData.livePrice)}</strong>
                    </div>
                    <div className="portfolio-detail-item">
                      <span>Day Change (%)</span>
                      <strong>
                        {rightPanelData.dayChangePercent !== null
                          ? `${rightPanelData.dayChangePercent.toFixed(2)}%`
                          : '--'}
                      </strong>
                    </div>
                    <div className="portfolio-detail-item">
                      <span>Volume</span>
                      <strong>{formatNumber(rightPanelData.volume)}</strong>
                    </div>

                    <div className="portfolio-prediction-block">
                      <div className="portfolio-prediction-title">AI Future Price Prediction Indicator</div>

                      {predictionIndicatorLoading && (
                        <div className="portfolio-prediction-loading">Calculating future trend...</div>
                      )}

                      {!predictionIndicatorLoading && predictionIndicatorError && (
                        <div className="portfolio-prediction-error">{predictionIndicatorError}</div>
                      )}

                      {!predictionIndicatorLoading && !predictionIndicatorError && rightPanelData.predictionIndicator && (
                        <>
                          <div className="portfolio-detail-item">
                            <span>Future Price Prediction (Next {rightPanelData.predictionIndicator.days} Days)</span>
                            <div className="portfolio-prediction-list">
                              {rightPanelData.predictionIndicator.future_predictions.map((point) => (
                                <div key={`pred-day-${point.day}`} className="portfolio-prediction-row">
                                  <span>Day {point.day}</span>
                                  <strong>Rs {formatMoney(toNumber(point.predicted_price))}</strong>
                                </div>
                              ))}
                            </div>
                          </div>

                          <div className="portfolio-detail-item">
                            <span>Trend</span>
                            <strong>
                              {rightPanelData.predictionIndicator.trend === 'INCREASE'
                                ? 'Increase ??'
                                : rightPanelData.predictionIndicator.trend === 'DECREASE'
                                  ? 'Decrease ??'
                                  : 'Stable'}
                            </strong>
                          </div>

                          <div className="portfolio-detail-item">
                            <span>Percentage Change</span>
                            <strong>{rightPanelData.predictionIndicator.percentage_change.toFixed(2)}%</strong>
                          </div>

                          <div className="portfolio-detail-item">
                            <span>Confidence Score</span>
                            <strong>{rightPanelData.predictionIndicator.confidence_score.toFixed(2)}%</strong>
                          </div>

                          <div className="portfolio-detail-item">
                            <span>Final AI Signal</span>
                            <strong className={`signal-${(rightPanelData.predictionIndicator.ai_signal || 'HOLD').toLowerCase()}`}>
                              {rightPanelData.predictionIndicator.ai_signal || 'HOLD'}
                            </strong>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="portfolio-detail-empty">
                    Click ? on any stock in the middle panel to view details here.
                  </div>
                )}
              </div>
            </div>

            <div className="portfolio-summary">
              Total invested: Rs {formatMoney(toNumber(portfolioData.total_invested))} | Remaining cash: Rs{' '}
              {formatMoney(toNumber(portfolioData.remaining_cash))}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const priceChangeClass = liveChange !== null && liveChange < 0 ? 'negative' : 'positive';
  const changeDisplay = liveChange !== null ? liveChange.toFixed(2) : '--';
  const changePercentDisplay = liveChangePercent !== null ? liveChangePercent.toFixed(2) : '--';

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <div className="logo">
            <ShowChartIcon fontSize="large" />
            <h1>Stock Analysis AI</h1>
          </div>
          <div className="header-subtitle">
            Live Indian Stock Market Analysis & AI-Powered Recommendations
          </div>
        </div>
      </header>

      <div className="dashboard-body">
        <div className="sidebar">
          <StockSearch onSelectStock={setSelectedSymbol} />
        </div>

        <div className="main-content">
          {showPlannerView ? (
            <div className="planner-standalone">
              <div className="planner-topbar">
                <button className="refresh-btn planner-back-btn" onClick={() => setShowPlannerView(false)}>
                  Back
                </button>
              </div>
              {investmentPlanner}
            </div>
          ) : !selectedSymbol ? (
            <>
              <div className="welcome-screen">
                <ShowChartIcon style={{ fontSize: 100, color: '#00ff00' }} />
                <h2>Welcome to Stock Analysis AI</h2>
                <p>Search and select a stock to view comprehensive analysis</p>
                <button className="refresh-btn planner-open-btn" onClick={() => setShowPlannerView(true)}>Open Investment Planner</button>
              </div>
              
            </>
          ) : loading ? (
            <div className="loading-screen">
              <div className="spinner"></div>
              <p>Loading stock data and generating analysis...</p>
            </div>
          ) : error ? (
            <div className="error-screen">
              <p>{error}</p>
              <button onClick={handleRefresh}>Retry</button>
            </div>
          ) : (
            <>
              <div className="stock-info-header">
                <div className="stock-main-info">
                  <h2>{liveData?.name || selectedSymbol}</h2>
                  <div className="stock-symbol">{selectedSymbol}</div>
                </div>
                <div className="stock-price-info">
                  <div className="current-price">Rs {formatMoney(livePriceValue)}</div>
                  <div className={`price-change ${priceChangeClass}`}>
                    {liveChange !== null ? (liveChange >= 0 ? <TrendingUpIcon /> : <TrendingDownIcon />) : (
                      <ShowChartIcon />
                    )}
                    {changeDisplay} ({changePercentDisplay}%)
                  </div>
                </div>
                <button className="refresh-btn planner-open-btn" onClick={() => setShowPlannerView(true)}>
                  Investment Planner
                </button>
                <button className="refresh-btn" onClick={handleRefresh}>
                  <RefreshIcon /> Refresh
                </button>
              </div>

              

              <div className="market-stats">
                <div className="stat-item">
                  <div className="stat-label">Open</div>
                  <div className="stat-value">Rs {formatMoney(liveOpen)}</div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">High</div>
                  <div className="stat-value">Rs {formatMoney(liveHigh)}</div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">Low</div>
                  <div className="stat-value">Rs {formatMoney(liveLow)}</div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">Volume</div>
                  <div className="stat-value">{formatNumber(liveVolume)}</div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">52W High</div>
                  <div className="stat-value">Rs {formatMoney(weekHigh)}</div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">52W Low</div>
                  <div className="stat-value">Rs {formatMoney(weekLow)}</div>
                </div>
              </div>

              {recommendation && (
                <div className={`recommendation-card ${getRecommendationClass(recommendation.recommendation)}`}>
                  <div className="rec-header">
                    <h3>AI Recommendation</h3>
                    <div className="rec-badge">{recommendation.recommendation}</div>
                  </div>
                  <div className="rec-details">
                    <div className="rec-score">
                      <span>Confidence Score:</span>
                      <strong>{recommendation.score}/100</strong>
                    </div>
                    <div className="rec-confidence">
                      <span>Level:</span>
                      <strong>{recommendation.confidence}</strong>
                    </div>
                  </div>
                  <div className="rec-summary">{recommendation.summary}</div>
                </div>
              )}

              <div className="tabs">
                <button
                  className={activeTab === 'overview' ? 'active' : ''}
                  onClick={() => setActiveTab('overview')}
                >
                  Overview
                </button>
                <button
                  className={activeTab === 'charts' ? 'active' : ''}
                  onClick={() => setActiveTab('charts')}
                >
                  Charts
                </button>
                <button
                  className={activeTab === 'analysis' ? 'active' : ''}
                  onClick={() => setActiveTab('analysis')}
                >
                  AI Analysis
                </button>
                <button
                  className={activeTab === 'prediction' ? 'active' : ''}
                  onClick={() => setActiveTab('prediction')}
                >
                  Prediction
                </button>
              </div>

              <div className="tab-content">
                {activeTab === 'overview' && (
                  <div className="overview-tab">
                    {recommendation && (
                      <div className="signals-grid">
                        <div className="signal-card">
                          <h4>Technical Signals</h4>
                          <ul>
                            {recommendation.signals.technical.signals.map((signal, i) => (
                              <li key={i}>{signal}</li>
                            ))}
                          </ul>
                          <div className="signal-score">
                            Score: {recommendation.signals.technical.score}/100
                          </div>
                        </div>
                        <div className="signal-card">
                          <h4>Prediction Signals</h4>
                          <ul>
                            {recommendation.signals.prediction.signals.map((signal, i) => (
                              <li key={i}>{signal}</li>
                            ))}
                          </ul>
                          <div className="signal-score">
                            Score: {recommendation.signals.prediction.score}/100
                          </div>
                        </div>
                        <div className="signal-card">
                          <h4>Trend Analysis</h4>
                          <ul>
                            {recommendation.signals.trend.signals.map((signal, i) => (
                              <li key={i}>{signal}</li>
                            ))}
                          </ul>
                          <div className="signal-score">
                            Score: {recommendation.signals.trend.score}/100
                          </div>
                        </div>
                        <div className="signal-card">
                          <h4>Volume Analysis</h4>
                          <ul>
                            {recommendation.signals.volume.signals.map((signal, i) => (
                              <li key={i}>{signal}</li>
                            ))}
                          </ul>
                          <div className="signal-score">
                            Score: {recommendation.signals.volume.score}/100
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'charts' && (
                  <Charts symbol={selectedSymbol} />
                )}

                {activeTab === 'analysis' && (
                  <div className="analysis-tab">
                    <div className="analysis-content">
                      {aiAnalysis ? (
                        <div className="ai-analysis">
                          <pre>{aiAnalysis}</pre>
                        </div>
                      ) : (
                        <p>Generating AI analysis...</p>
                      )}
                    </div>
                  </div>
                )}

                {activeTab === 'prediction' && (
                  <div className="analysis-tab">
                    <div className="analysis-content">
                      {Array.isArray(prediction) && prediction.length > 0 ? (
                        <div className="prediction-list">
                          {prediction.slice(0, 10).map((item, idx) => {
                            const dateValue = item?.Date || item?.date || item?.day || `Day ${idx + 1}`;
                            const priceValue = toNumber(item?.Predicted_Close ?? item?.predicted_price ?? item?.price);
                            const confidenceValue = toNumber(item?.confidence ?? item?.probability ?? item?.confidence_score);
                            return (
                              <div key={`pred-${idx}`} className="prediction-row">
                                <span>{dateValue}</span>
                                <strong>Rs {formatMoney(priceValue)}</strong>
                                {confidenceValue !== null && <small>Confidence: {confidenceValue.toFixed(2)}%</small>}
                              </div>
                            );
                          })}
                        </div>
                      ) : (
                        <p>Prediction data is not available yet for this stock.</p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      <ChatBot
        symbol={selectedSymbol}
        stockName={liveData?.name || selectedSymbol}
        recommendation={recommendation}
        prediction={Array.isArray(prediction) && prediction.length ? prediction[0] : null}
      />
    </div>
  );
};

export default Dashboard;





































