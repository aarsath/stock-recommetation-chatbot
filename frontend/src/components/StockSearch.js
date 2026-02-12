import React, { useState, useEffect } from 'react';
import { searchStock, getPopularStocks, getStockDetails } from '../services/api';
import SearchIcon from '@mui/icons-material/Search';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import CloseIcon from '@mui/icons-material/Close';
import './StockSearch.css';

const StockSearch = ({ onSelectStock }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [popularStocks, setPopularStocks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [selectedStockName, setSelectedStockName] = useState('');

  useEffect(() => {
    loadPopularStocks();
  }, []);

  const loadPopularStocks = async () => {
    try {
      const data = await getPopularStocks();
      const combined = [
        ...data.nifty_50.slice(0, 5),
        ...data.bank_nifty.slice(0, 3),
        ...data.popular.slice(0, 4)
      ];
      setPopularStocks(combined);
    } catch (error) {
      console.error('Error loading popular stocks:', error);
    }
  };

  const handleSearch = async (searchQuery) => {
    if (!searchQuery || searchQuery.length < 2) {
      setResults([]);
      setShowResults(false);
      return;
    }

    setLoading(true);
    try {
      const data = await searchStock(searchQuery);
      setResults(data.results || []);
      setShowResults(true);
    } catch (error) {
      console.error('Search error:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const value = e.target.value;
    setQuery(value);
    handleSearch(value);
  };

  const selectStock = async (symbol) => {
    setQuery('');
    setShowResults(false);
    
    try {
      // Fetch stock details to get the name
      const stockDetails = await getStockDetails(symbol);
      const stockName = stockDetails.name || symbol;
      setSelectedStockName(stockName);
    } catch (error) {
      console.error('Error fetching stock details:', error);
      setSelectedStockName(symbol);
    }
    
    onSelectStock(symbol);
  };

  const clearSelectedStock = () => {
    setSelectedStockName('');
    onSelectStock(null); // Pass null to parent to indicate no stock selected
  };

  const clearSearch = () => {
    setQuery('');
    setResults([]);
    setShowResults(false);
  };

  return (
    <div className="stock-search">
      {/* Selected Stock Display */}
      {selectedStockName && (
        <div className="selected-stock-display">
          <div className="selected-stock-info">
            <span className="selected-label">Selected: </span>
            <span className="selected-stock-name">{selectedStockName}</span>
          </div>
          <button 
            className="cancel-btn"
            onClick={clearSelectedStock}
            title="Clear selection"
          >
            <CloseIcon />
            Clear
          </button>
        </div>
      )}

      {/* Search Box */}
      <div className="search-box">
        <SearchIcon className="search-icon" />
        <input
          type="text"
          placeholder="Search NSE/BSE stocks (e.g., RELIANCE, TCS, INFY)"
          value={query}
          onChange={handleInputChange}
          onFocus={() => query && setShowResults(true)}
          className="search-input"
        />
        {query && (
          <button 
            className="clear-search-btn"
            onClick={clearSearch}
            title="Clear search"
          >
            <CloseIcon fontSize="small" />
          </button>
        )}
        {loading && <div className="search-loading"></div>}
      </div>

      {/* Search Results Dropdown */}
      {showResults && results.length > 0 && (
        <div className="search-results">
          <div className="results-header">
            <span>Search Results</span>
            <button 
              className="close-results-btn"
              onClick={() => setShowResults(false)}
            >
              <CloseIcon fontSize="small" />
            </button>
          </div>
          {results.map((stock, index) => (
            <div
              key={index}
              className="search-result-item"
              onClick={() => selectStock(stock.symbol)}
            >
              <div className="result-main">
                <div className="result-symbol">{stock.symbol}</div>
                <div className="result-name">{stock.name}</div>
              </div>
              <div className="result-exchange">{stock.exchange}</div>
            </div>
          ))}
        </div>
      )}


      {showResults && !loading && results.length === 0 && query.length >= 2 && (
        <div className="search-results">
          <div className="search-empty">No stocks found for "{query}"</div>
        </div>
      )}      {/* Popular Stocks Section */}
      <div className="popular-stocks">
        <div className="popular-header">
          <TrendingUpIcon />
          <span>Popular Stocks</span>
        </div>
        <div className="popular-list">
          {popularStocks.map((symbol, index) => (
            <button
              key={index}
              className="popular-stock-btn"
              onClick={() => selectStock(symbol)}
            >
              {symbol.replace('.NS', '').replace('.BO', '')}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default StockSearch;
