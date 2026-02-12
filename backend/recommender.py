"""
Stock Recommendation Engine
Generates Buy/Sell/Hold recommendations based on:
- Technical Indicators
- ML Predictions
- Price Trends
- Volume Analysis
"""

import pandas as pd
import numpy as np


class StockRecommender:
    
    def __init__(self):
        self.weights = {
            'technical': 0.40,
            'prediction': 0.35,
            'trend': 0.15,
            'volume': 0.10
        }
    
    def generate_recommendation(self, df, prediction_data, live_data):
        """Generate comprehensive Buy/Sell/Hold recommendation"""
        
        if df is None or df.empty:
            return None
        
        # Get signals from different sources
        technical_signal = self._analyze_technical_indicators(df)
        prediction_signal = self._analyze_prediction(prediction_data, live_data)
        trend_signal = self._analyze_trend(df)
        volume_signal = self._analyze_volume(df)
        
        # Calculate weighted score
        total_score = (
            technical_signal['score'] * self.weights['technical'] +
            prediction_signal['score'] * self.weights['prediction'] +
            trend_signal['score'] * self.weights['trend'] +
            volume_signal['score'] * self.weights['volume']
        )
        
        # Determine recommendation
        if total_score >= 65:
            recommendation = 'STRONG BUY'
            action = 'BUY'
            confidence = 'High'
        elif total_score >= 55:
            recommendation = 'BUY'
            action = 'BUY'
            confidence = 'Medium'
        elif total_score >= 45:
            recommendation = 'HOLD'
            action = 'HOLD'
            confidence = 'Medium'
        elif total_score >= 35:
            recommendation = 'SELL'
            action = 'SELL'
            confidence = 'Medium'
        else:
            recommendation = 'STRONG SELL'
            action = 'SELL'
            confidence = 'High'
        
        return {
            'recommendation': recommendation,
            'action': action,
            'confidence': confidence,
            'score': round(total_score, 2),
            'signals': {
                'technical': technical_signal,
                'prediction': prediction_signal,
                'trend': trend_signal,
                'volume': volume_signal
            },
            'summary': self._generate_summary(
                recommendation, 
                technical_signal, 
                prediction_signal, 
                trend_signal, 
                volume_signal
            )
        }
    
    def _analyze_technical_indicators(self, df):
        """Analyze technical indicators"""
        last_row = df.iloc[-1]
        score = 50  # Neutral starting point
        signals = []
        
        # RSI Analysis
        rsi = last_row.get('RSI', 50)
        if rsi < 30:
            score += 15
            signals.append('RSI indicates oversold (bullish)')
        elif rsi > 70:
            score -= 15
            signals.append('RSI indicates overbought (bearish)')
        elif rsi < 40:
            score += 8
            signals.append('RSI shows buying opportunity')
        elif rsi > 60:
            score -= 8
            signals.append('RSI shows selling pressure')
        
        # MACD Analysis
        macd = last_row.get('MACD', 0)
        macd_signal = last_row.get('MACD_Signal', 0)
        macd_hist = last_row.get('MACD_Histogram', 0)
        
        if macd > macd_signal and macd_hist > 0:
            score += 10
            signals.append('MACD bullish crossover')
        elif macd < macd_signal and macd_hist < 0:
            score -= 10
            signals.append('MACD bearish crossover')
        
        # Moving Average Analysis
        close = last_row.get('Close', 0)
        sma_20 = last_row.get('SMA_20', close)
        sma_50 = last_row.get('SMA_50', close)
        
        if close > sma_20 > sma_50:
            score += 10
            signals.append('Price above both SMAs (bullish)')
        elif close < sma_20 < sma_50:
            score -= 10
            signals.append('Price below both SMAs (bearish)')
        elif close > sma_20:
            score += 5
            signals.append('Price above SMA 20')
        elif close < sma_20:
            score -= 5
            signals.append('Price below SMA 20')
        
        # Bollinger Bands Analysis
        bb_upper = last_row.get('BB_Upper', close * 1.02)
        bb_lower = last_row.get('BB_Lower', close * 0.98)
        bb_middle = last_row.get('BB_Middle', close)
        
        if close < bb_lower:
            score += 8
            signals.append('Price at lower Bollinger Band (potential bounce)')
        elif close > bb_upper:
            score -= 8
            signals.append('Price at upper Bollinger Band (potential reversal)')
        
        # Ensure score is within 0-100
        score = max(0, min(100, score))
        
        return {
            'score': round(score, 2),
            'signals': signals,
            'indicators': {
                'RSI': round(rsi, 2),
                'MACD': round(macd, 4),
                'Price_vs_SMA20': round(((close - sma_20) / sma_20) * 100, 2),
                'Price_vs_SMA50': round(((close - sma_50) / sma_50) * 100, 2)
            }
        }
    
    def _analyze_prediction(self, prediction_data, live_data):
        """Analyze ML prediction"""
        score = 50
        signals = []
        
        if prediction_data is None or live_data is None:
            return {'score': 50, 'signals': ['Prediction data unavailable']}
        
        current_price = live_data.get('price', 0)
        predicted_price = prediction_data.get('predicted_price', current_price)
        change_percent = prediction_data.get('change_percent', 0)
        
        # Score based on predicted change
        if change_percent > 5:
            score += 20
            signals.append(f'ML predicts +{change_percent:.2f}% gain (strong bullish)')
        elif change_percent > 2:
            score += 15
            signals.append(f'ML predicts +{change_percent:.2f}% gain (bullish)')
        elif change_percent > 0:
            score += 8
            signals.append(f'ML predicts +{change_percent:.2f}% gain')
        elif change_percent < -5:
            score -= 20
            signals.append(f'ML predicts {change_percent:.2f}% loss (strong bearish)')
        elif change_percent < -2:
            score -= 15
            signals.append(f'ML predicts {change_percent:.2f}% loss (bearish)')
        elif change_percent < 0:
            score -= 8
            signals.append(f'ML predicts {change_percent:.2f}% loss')
        
        score = max(0, min(100, score))
        
        return {
            'score': round(score, 2),
            'signals': signals,
            'prediction': {
                'current_price': round(current_price, 2),
                'predicted_price': round(predicted_price, 2),
                'change_percent': round(change_percent, 2)
            }
        }
    
    def _analyze_trend(self, df):
        """Analyze price trend"""
        score = 50
        signals = []
        
        # Get recent data
        recent_df = df.tail(20)
        
        # Calculate trend
        closes = recent_df['Close'].values
        
        # Linear regression for trend
        x = np.arange(len(closes))
        slope = np.polyfit(x, closes, 1)[0]
        
        # Normalize slope
        avg_price = closes.mean()
        slope_percent = (slope / avg_price) * 100
        
        if slope_percent > 0.5:
            score += 15
            signals.append('Strong uptrend')
        elif slope_percent > 0.2:
            score += 10
            signals.append('Uptrend')
        elif slope_percent < -0.5:
            score -= 15
            signals.append('Strong downtrend')
        elif slope_percent < -0.2:
            score -= 10
            signals.append('Downtrend')
        else:
            signals.append('Sideways trend')
        
        # Volatility analysis
        volatility = closes.std() / closes.mean()
        
        if volatility > 0.05:
            signals.append('High volatility (risky)')
        elif volatility < 0.02:
            signals.append('Low volatility (stable)')
        
        score = max(0, min(100, score))
        
        return {
            'score': round(score, 2),
            'signals': signals,
            'trend': {
                'direction': 'Up' if slope_percent > 0 else 'Down',
                'strength': round(abs(slope_percent), 2),
                'volatility': round(volatility, 4)
            }
        }
    
    def _analyze_volume(self, df):
        """Analyze volume trends"""
        score = 50
        signals = []
        
        recent_df = df.tail(20)
        
        # Volume trend
        avg_volume = recent_df['Volume'].mean()
        latest_volume = recent_df['Volume'].iloc[-1]
        
        volume_ratio = latest_volume / avg_volume if avg_volume > 0 else 1
        
        # Price and volume correlation
        price_change = recent_df['Close'].pct_change().iloc[-1]
        
        if volume_ratio > 1.5 and price_change > 0:
            score += 10
            signals.append('High volume with price increase (bullish)')
        elif volume_ratio > 1.5 and price_change < 0:
            score -= 10
            signals.append('High volume with price decrease (bearish)')
        elif volume_ratio > 1.2:
            signals.append('Above average volume')
        elif volume_ratio < 0.5:
            signals.append('Low volume (lack of interest)')
        
        score = max(0, min(100, score))
        
        return {
            'score': round(score, 2),
            'signals': signals,
            'volume': {
                'current': int(latest_volume),
                'average': int(avg_volume),
                'ratio': round(volume_ratio, 2)
            }
        }
    
    def _generate_summary(self, recommendation, technical, prediction, trend, volume):
        """Generate recommendation summary"""
        summary = f"{recommendation} recommendation based on: "
        
        key_points = []
        
        # Add top signals from each category
        if technical['signals']:
            key_points.append(technical['signals'][0])
        
        if prediction['signals']:
            key_points.append(prediction['signals'][0])
        
        if trend['signals']:
            key_points.append(trend['signals'][0])
        
        summary += '; '.join(key_points)
        
        return summary


def get_recommendation(df, prediction_data, live_data):
    """Quick function to get recommendation"""
    recommender = StockRecommender()
    return recommender.generate_recommendation(df, prediction_data, live_data)
