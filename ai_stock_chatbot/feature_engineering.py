import numpy as np
import pandas as pd


class FeatureBuilder:
    """Creates technical features for next-day close prediction."""

    @staticmethod
    def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(period).mean()
        rs = gain / loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))

    def build(self, df: pd.DataFrame):
        if df is None or df.empty or len(df) < 60:
            return None, None, None, None

        frame = df.copy()

        # Basic technical features
        frame["ret_1"] = frame["Close"].pct_change(1)
        frame["ret_5"] = frame["Close"].pct_change(5)
        frame["sma_5"] = frame["Close"].rolling(5).mean()
        frame["sma_10"] = frame["Close"].rolling(10).mean()
        frame["ema_10"] = frame["Close"].ewm(span=10, adjust=False).mean()
        frame["vol_chg"] = frame["Volume"].pct_change(1)
        frame["hl_spread"] = (frame["High"] - frame["Low"]) / frame["Close"].replace(0, np.nan)
        frame["oc_spread"] = (frame["Close"] - frame["Open"]) / frame["Open"].replace(0, np.nan)
        frame["rsi_14"] = self._rsi(frame["Close"], 14)

        # Target: next-day close
        frame["target_next_close"] = frame["Close"].shift(-1)

        feature_cols = [
            "Open", "High", "Low", "Close", "Volume",
            "ret_1", "ret_5", "sma_5", "sma_10", "ema_10",
            "vol_chg", "hl_spread", "oc_spread", "rsi_14",
        ]

        frame = frame.replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)
        if frame.empty:
            return None, None, None, None

        X = frame[feature_cols]
        y = frame["target_next_close"]

        # Row used for forecasting the next unseen day
        last_row_features = X.iloc[[-1]].copy()
        current_close = float(frame["Close"].iloc[-1])

        return X, y, last_row_features, current_close
