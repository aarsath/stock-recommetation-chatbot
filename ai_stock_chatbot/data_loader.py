import pandas as pd
import yfinance as yf

from utils import normalize_symbol


class MarketDataLoader:
    """Loads historical Indian stock data from Yahoo Finance."""

    def fetch_stock_history(self, stock: str, period: str = "5y", interval: str = "1d") -> pd.DataFrame:
        symbol = normalize_symbol(stock)
        if not symbol:
            return pd.DataFrame()

        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=False)

        if df is None or df.empty:
            return pd.DataFrame()

        df = df.reset_index()

        # Standardize columns
        keep_cols = [c for c in ["Date", "Open", "High", "Low", "Close", "Volume"] if c in df.columns]
        df = df[keep_cols].copy()

        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"])

        df = df.dropna().reset_index(drop=True)
        return df
