import os
from typing import Dict, Optional

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

from config import settings


class StockModelManager:
    """Trains and serves RandomForest models per stock symbol."""

    def __init__(self):
        self.models: Dict[str, RandomForestRegressor] = {}
        self.metrics: Dict[str, dict] = {}
        os.makedirs(settings.model_path, exist_ok=True)

    def _model_file(self, symbol: str) -> str:
        return os.path.join(settings.model_path, f"{symbol.replace('.', '_')}_rf.pkl")

    def load_model(self, symbol: str) -> Optional[RandomForestRegressor]:
        model_path = self._model_file(symbol)
        if not os.path.exists(model_path):
            return None
        model = joblib.load(model_path)
        self.models[symbol] = model
        return model

    def train_model(self, symbol: str, X, y):
        if X is None or y is None or len(X) < 30:
            return {"success": False, "error": "Not enough data to train model."}

        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=False
            )

            model = RandomForestRegressor(
                n_estimators=300,
                max_depth=14,
                min_samples_split=4,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
            )
            model.fit(X_train, y_train)

            preds = model.predict(X_test)
            mae = float(mean_absolute_error(y_test, preds))

            self.models[symbol] = model
            self.metrics[symbol] = {
                "mae": round(mae, 2),
                "train_rows": int(len(X_train)),
                "test_rows": int(len(X_test)),
            }

            joblib.dump(model, self._model_file(symbol))
            return {"success": True, "metrics": self.metrics[symbol]}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def predict_next_close(self, symbol: str, last_row_features) -> Optional[float]:
        model = self.models.get(symbol) or self.load_model(symbol)
        if model is None:
            return None

        try:
            pred = model.predict(last_row_features)[0]
            if isinstance(pred, np.generic):
                pred = float(pred)
            return float(pred)
        except Exception:
            return None
