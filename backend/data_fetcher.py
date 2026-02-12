"""
Live Stock Data Fetcher
Supports NSE, BSE via Yahoo Finance
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from config import Config


class StockDataFetcher:
    
    def __init__(self, symbol):
        self.symbol = symbol
        self.ticker = yf.Ticker(symbol)
    
    def get_live_price(self):
        """Get current live price and basic info"""
        try:
            info = self.ticker.info
            history = self.ticker.history(period='1d', interval='1m')
            
            if history.empty:
                return None
            
            current_price = history['Close'].iloc[-1]
            open_price = history['Open'].iloc[0]
            high = history['High'].max()
            low = history['Low'].min()
            volume = history['Volume'].sum()
            
            # Calculate change
            prev_close = info.get('previousClose', open_price)
            change = current_price - prev_close
            change_percent = (change / prev_close) * 100 if prev_close else 0
            
            return {
                'symbol': self.symbol,
                'name': info.get('longName', self.symbol),
                'price': round(current_price, 2),
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'volume': int(volume),
                'prev_close': round(prev_close, 2),
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'week_52_high': info.get('fiftyTwoWeekHigh', 0),
                'week_52_low': info.get('fiftyTwoWeekLow', 0),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        
        except Exception as e:
            print(f"Error fetching live price: {str(e)}")
            return None
    
    def get_historical_data(self, days=1825):
        """Get historical stock data"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            df = self.ticker.history(start=start_date, end=end_date)
            
            if df.empty:
                return None
            
            # Reset index to make Date a column
            df.reset_index(inplace=True)
            
            # Rename columns
            df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits']
            
            # Keep only necessary columns
            df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
            
            return df
        
        except Exception as e:
            print(f"Error fetching historical data: {str(e)}")
            return None
    
    def get_intraday_data(self, interval='5m'):
        """Get intraday data for live charting"""
        try:
            df = self.ticker.history(period='1d', interval=interval)
            
            if df.empty:
                return None
            
            df.reset_index(inplace=True)
            df.columns = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits']
            df = df[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]
            
            return df
        
        except Exception as e:
            print(f"Error fetching intraday data: {str(e)}")
            return None
    
    def calculate_technical_indicators(self, df):
        """Calculate all technical indicators"""
        if df is None or df.empty:
            return None
        
        df = df.copy()
        
        # Simple Moving Averages
        for period in Config.SMA_PERIODS:
            df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()
        
        # Exponential Moving Averages
        for period in Config.EMA_PERIODS:
            df[f'EMA_{period}'] = df['Close'].ewm(span=period, adjust=False).mean()
        
        # RSI (Relative Strength Index)
        df['RSI'] = self._calculate_rsi(df['Close'], Config.RSI_PERIOD)
        
        # MACD
        macd_data = self._calculate_macd(
            df['Close'], 
            Config.MACD_FAST, 
            Config.MACD_SLOW, 
            Config.MACD_SIGNAL
        )
        df['MACD'] = macd_data['MACD']
        df['MACD_Signal'] = macd_data['Signal']
        df['MACD_Histogram'] = macd_data['Histogram']
        
        # Bollinger Bands
        bb_data = self._calculate_bollinger_bands(df['Close'], Config.BB_PERIOD, Config.BB_STD)
        df['BB_Upper'] = bb_data['Upper']
        df['BB_Middle'] = bb_data['Middle']
        df['BB_Lower'] = bb_data['Lower']
        
        # Price Rate of Change
        df['ROC'] = df['Close'].pct_change(periods=10) * 100
        
        # Average True Range (ATR)
        df['ATR'] = self._calculate_atr(df, period=14)
        
        return df
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        
        return {
            'MACD': macd,
            'Signal': signal_line,
            'Histogram': histogram
        }
    
    def _calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return {
            'Upper': upper,
            'Middle': middle,
            'Lower': lower
        }
    
    def _calculate_atr(self, df, period=14):
        """Calculate Average True Range"""
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        
        return true_range.rolling(period).mean()
    
    def get_complete_data(self):
        """Get complete stock data with all indicators"""
        historical_df = self.get_historical_data()
        
        if historical_df is None:
            return None
        
        # Calculate technical indicators
        df_with_indicators = self.calculate_technical_indicators(historical_df)
        
        # Get live price
        live_data = self.get_live_price()
        
        return {
            'historical': df_with_indicators,
            'live': live_data
        }


def fetch_live_price(symbol):
    """Quick function to fetch live price"""
    fetcher = StockDataFetcher(symbol)
    return fetcher.get_live_price()


def fetch_historical_data(symbol, days=365):
    """Quick function to fetch historical data"""
    fetcher = StockDataFetcher(symbol)
    return fetcher.get_historical_data(days)


def fetch_complete_data(symbol):
    """Quick function to fetch complete data"""
    fetcher = StockDataFetcher(symbol)
    return fetcher.get_complete_data()
