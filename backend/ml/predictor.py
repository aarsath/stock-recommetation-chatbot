"""
ML-Based Stock Price Predictor
Uses RandomForest Regressor with technical indicators
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import joblib
import os
from config import Config


class StockPredictor:
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.is_trained = False

    def _sanitize_feature_frame(self, X, y=None):
        """Remove non-finite values that break sklearn scaling/prediction."""
        if X is None or len(X) == 0:
            return (None, None) if y is not None else None

        X_clean = X.copy()
        X_clean = X_clean.replace([np.inf, -np.inf], np.nan)
        X_clean = X_clean.apply(pd.to_numeric, errors='coerce')
        X_clean = X_clean.clip(lower=-1e12, upper=1e12)

        if y is None:
            X_clean = X_clean.dropna()
            return X_clean if len(X_clean) else None

        y_clean = pd.to_numeric(y, errors='coerce')
        valid_mask = X_clean.notna().all(axis=1) & y_clean.notna() & np.isfinite(y_clean)

        X_clean = X_clean.loc[valid_mask]
        y_clean = y_clean.loc[valid_mask]

        if len(X_clean) == 0:
            return None, None

        return X_clean, y_clean
    
    def prepare_features(self, df):
        """Prepare features for ML model"""
        if df is None or df.empty:
            return None, None
        
        df = df.copy()
        
        # Remove rows with NaN values
        df = df.dropna()
        
        if len(df) < 50:
            return None, None
        
        # Feature engineering
        feature_columns = [
            'Open', 'High', 'Low', 'Volume',
            'SMA_20', 'SMA_50', 'EMA_12', 'EMA_26',
            'RSI', 'MACD', 'MACD_Signal', 'MACD_Histogram',
            'BB_Upper', 'BB_Middle', 'BB_Lower', 'ROC', 'ATR'
        ]
        
        # Check if all features exist
        available_features = [col for col in feature_columns if col in df.columns]
        
        if len(available_features) < 10:
            return None, None
        
        # Additional features
        df['Price_Range'] = df['High'] - df['Low']
        df['Price_Change'] = df['Close'] - df['Open']
        df['Volume_Change'] = df['Volume'].pct_change()
        
        # Lag features
        for lag in [1, 2, 3, 5, 7]:
            df[f'Close_Lag_{lag}'] = df['Close'].shift(lag)
            df[f'Volume_Lag_{lag}'] = df['Volume'].shift(lag)
        
        # Rolling statistics
        df['Close_Rolling_Mean_7'] = df['Close'].rolling(window=7).mean()
        df['Close_Rolling_Std_7'] = df['Close'].rolling(window=7).std()
        df['Volume_Rolling_Mean_7'] = df['Volume'].rolling(window=7).mean()
        
        # Drop NaN created by lag and rolling
        df = df.dropna()
        
        # Update feature columns
        self.feature_columns = available_features + [
            'Price_Range', 'Price_Change', 'Volume_Change',
            'Close_Lag_1', 'Close_Lag_2', 'Close_Lag_3', 'Close_Lag_5', 'Close_Lag_7',
            'Volume_Lag_1', 'Volume_Lag_2', 'Volume_Lag_3', 'Volume_Lag_5', 'Volume_Lag_7',
            'Close_Rolling_Mean_7', 'Close_Rolling_Std_7', 'Volume_Rolling_Mean_7'
        ]
        
        # Filter available features
        self.feature_columns = [col for col in self.feature_columns if col in df.columns]
        
        X = df[self.feature_columns]
        y = df['Close']
        
        return X, y
    
    def train(self, df):
        """Train the ML model"""
        X, y = self.prepare_features(df)
        X, y = self._sanitize_feature_frame(X, y)

        if X is None or y is None:
            return {
                'success': False,
                'error': 'Insufficient data for training'
            }
        
        try:
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                test_size=1-Config.TRAIN_TEST_SPLIT,
                random_state=Config.RANDOM_STATE,
                shuffle=False  # Don't shuffle time series data
            )

            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # Train RandomForest model
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=20,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=Config.RANDOM_STATE,
                n_jobs=-1
            )

            self.model.fit(X_train_scaled, y_train)

            # Evaluate
            y_pred_train = self.model.predict(X_train_scaled)
            y_pred_test = self.model.predict(X_test_scaled)
        except Exception as e:
            self.model = None
            self.is_trained = False
            return {
                'success': False,
                'error': f'Model training failed: {str(e)}'
            }
        
        train_mae = mean_absolute_error(y_train, y_pred_train)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        
        self.is_trained = True
        
        return {
            'success': True,
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'train_mae': round(train_mae, 2),
            'test_mae': round(test_mae, 2),
            'train_rmse': round(train_rmse, 2),
            'test_rmse': round(test_rmse, 2),
            'train_r2': round(train_r2, 4),
            'test_r2': round(test_r2, 4),
            'feature_count': len(self.feature_columns)
        }
    
    def predict(self, df, days=30):
        """Predict future prices"""
        if not self.is_trained or self.model is None:
            return None
        
        X, _ = self.prepare_features(df)
        X = self._sanitize_feature_frame(X)

        if X is None:
            return None
        
        # Get last row for prediction
        last_data = X.iloc[-1:].copy()
        
        predictions = []
        current_data = last_data.copy()
        
        for day in range(days):
            # Scale and predict
            current_data = self._sanitize_feature_frame(current_data)
            if current_data is None:
                break
            current_scaled = self.scaler.transform(current_data)
            predicted_price = self.model.predict(current_scaled)[0]
            
            predictions.append({
                'day': day + 1,
                'predicted_price': round(predicted_price, 2)
            })
            
            # Update features for next prediction (simplified approach)
            # In production, you'd update all lag features properly
            if day < days - 1:
                current_data = current_data.copy()
                # Update close-related features
                for col in current_data.columns:
                    if 'Close_Lag' in col:
                        lag_num = int(col.split('_')[-1])
                        if lag_num > 1:
                            prev_lag_col = f'Close_Lag_{lag_num-1}'
                            if prev_lag_col in current_data.columns:
                                current_data[col] = current_data[prev_lag_col]
                        else:
                            current_data[col] = predicted_price
        
        return predictions
    
    def predict_next_day(self, df):
        """Predict next day price"""
        if not self.is_trained or self.model is None:
            return None
        
        X, _ = self.prepare_features(df)
        X = self._sanitize_feature_frame(X)

        if X is None:
            return None
        
        # Get last row
        last_data = X.iloc[-1:].copy()
        
        # Scale and predict
        last_scaled = self.scaler.transform(last_data)
        predicted_price = self.model.predict(last_scaled)[0]
        
        # Get actual last price
        actual_price = df['Close'].iloc[-1]
        
        # Calculate confidence based on model performance
        confidence = self._calculate_confidence()
        
        return {
            'current_price': round(actual_price, 2),
            'predicted_price': round(predicted_price, 2),
            'change': round(predicted_price - actual_price, 2),
            'change_percent': round((((predicted_price - actual_price) / actual_price) * 100) if actual_price else 0, 2),
            'confidence': confidence
        }
    
    def _calculate_confidence(self):
        """Calculate prediction confidence"""
        # This is a simplified confidence calculation
        # In production, use proper uncertainty quantification
        if not self.is_trained:
            return 0.5
        
        # Base confidence on feature importance variance
        feature_importance = self.model.feature_importances_
        importance_std = np.std(feature_importance)
        
        # Lower std = more confident (features are balanced)
        confidence = max(0.6, min(0.95, 1 - importance_std))
        
        return round(confidence, 2)
    
    def get_feature_importance(self):
        """Get feature importance"""
        if not self.is_trained or self.model is None:
            return None
        
        importance = self.model.feature_importances_
        
        feature_importance = []
        for i, col in enumerate(self.feature_columns):
            feature_importance.append({
                'feature': col,
                'importance': round(importance[i], 4)
            })
        
        # Sort by importance
        feature_importance = sorted(feature_importance, key=lambda x: x['importance'], reverse=True)
        
        return feature_importance[:10]  # Top 10 features
    
    def save_model(self, symbol):
        """Save trained model"""
        if not self.is_trained:
            return False
        
        os.makedirs(Config.MODEL_PATH, exist_ok=True)
        
        model_file = os.path.join(Config.MODEL_PATH, f'{symbol}_model.pkl')
        scaler_file = os.path.join(Config.MODEL_PATH, f'{symbol}_scaler.pkl')
        
        joblib.dump(self.model, model_file)
        joblib.dump(self.scaler, scaler_file)
        
        return True
    
    def load_model(self, symbol):
        """Load trained model"""
        model_file = os.path.join(Config.MODEL_PATH, f'{symbol}_model.pkl')
        scaler_file = os.path.join(Config.MODEL_PATH, f'{symbol}_scaler.pkl')
        
        if not os.path.exists(model_file) or not os.path.exists(scaler_file):
            return False
        
        self.model = joblib.load(model_file)
        self.scaler = joblib.load(scaler_file)
        self.is_trained = True
        
        return True



