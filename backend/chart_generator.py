"""
Matplotlib Chart Generator
Creates professional technical analysis charts
"""

import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import seaborn as sns
import pandas as pd
import numpy as np
import os
from datetime import datetime
from config import Config

# Set style
sns.set_style('darkgrid')
plt.rcParams['figure.facecolor'] = '#1e1e1e'
plt.rcParams['axes.facecolor'] = '#2d2d2d'
plt.rcParams['axes.edgecolor'] = '#666666'
plt.rcParams['text.color'] = 'white'
plt.rcParams['axes.labelcolor'] = 'white'
plt.rcParams['xtick.color'] = 'white'
plt.rcParams['ytick.color'] = 'white'
plt.rcParams['grid.color'] = '#404040'


class ChartGenerator:
    
    def __init__(self, symbol):
        self.symbol = symbol
        os.makedirs(Config.CHART_OUTPUT_DIR, exist_ok=True)
    
    def create_comprehensive_chart(self, df, prediction_data=None, recommendation=None):
        """Create comprehensive technical analysis chart"""
        
        if df is None or df.empty:
            return None
        
        # Create figure with subplots
        fig = plt.figure(figsize=Config.CHART_FIGSIZE)
        gs = GridSpec(4, 1, height_ratios=[3, 1, 1, 1], hspace=0.3)
        
        # Convert Date to datetime if needed
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
        
        # Subplot 1: Price and Moving Averages
        ax1 = fig.add_subplot(gs[0])
        self._plot_price_ma(ax1, df, prediction_data)
        
        # Subplot 2: Volume
        ax2 = fig.add_subplot(gs[1], sharex=ax1)
        self._plot_volume(ax2, df)
        
        # Subplot 3: RSI
        ax3 = fig.add_subplot(gs[2], sharex=ax1)
        self._plot_rsi(ax3, df)
        
        # Subplot 4: MACD
        ax4 = fig.add_subplot(gs[3], sharex=ax1)
        self._plot_macd(ax4, df)
        
        # Add title with recommendation
        title = f'{self.symbol} - Technical Analysis'
        if recommendation:
            title += f" | {recommendation['recommendation']} (Score: {recommendation['score']})"
        
        fig.suptitle(title, fontsize=16, fontweight='bold', color='white')
        
        # Save chart
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{self.symbol}_{timestamp}.png'
        filepath = os.path.join(Config.CHART_OUTPUT_DIR, filename)
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=Config.CHART_DPI, facecolor='#1e1e1e')
        plt.close()
        
        return filepath
    
    def _plot_price_ma(self, ax, df, prediction_data):
        """Plot price with moving averages and Bollinger Bands"""
        
        # Plot Bollinger Bands first (background)
        if 'BB_Upper' in df.columns:
            ax.fill_between(
                df['Date'], 
                df['BB_Upper'], 
                df['BB_Lower'],
                alpha=0.2, 
                color='gray',
                label='Bollinger Bands'
            )
        
        # Plot price
        ax.plot(df['Date'], df['Close'], label='Close Price', color='#00ff00', linewidth=2)
        
        # Plot moving averages
        if 'SMA_20' in df.columns:
            ax.plot(df['Date'], df['SMA_20'], label='SMA 20', color='#ff9500', linewidth=1.5, alpha=0.8)
        
        if 'SMA_50' in df.columns:
            ax.plot(df['Date'], df['SMA_50'], label='SMA 50', color='#ff0000', linewidth=1.5, alpha=0.8)
        
        if 'EMA_12' in df.columns:
            ax.plot(df['Date'], df['EMA_12'], label='EMA 12', color='#00ffff', linewidth=1, alpha=0.6)
        
        # Add prediction line if available
        if prediction_data and isinstance(prediction_data, list):
            last_date = df['Date'].iloc[-1]
            pred_dates = pd.date_range(start=last_date, periods=len(prediction_data)+1, freq='D')[1:]
            pred_prices = [p['predicted_price'] for p in prediction_data]
            
            ax.plot(pred_dates, pred_prices, 
                   label='ML Prediction', 
                   color='#ff00ff', 
                   linewidth=2, 
                   linestyle='--',
                   marker='o',
                   markersize=3)
        
        ax.set_ylabel('Price (₹)', fontweight='bold')
        ax.legend(loc='upper left', fontsize=8, framealpha=0.8)
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=0)
    
    def _plot_volume(self, ax, df):
        """Plot volume bars"""
        colors = ['#00ff00' if df['Close'].iloc[i] >= df['Open'].iloc[i] 
                 else '#ff0000' for i in range(len(df))]
        
        ax.bar(df['Date'], df['Volume'], color=colors, alpha=0.6, width=0.8)
        ax.set_ylabel('Volume', fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Format y-axis for volume
        ax.ticklabel_format(style='plain', axis='y')
    
    def _plot_rsi(self, ax, df):
        """Plot RSI indicator"""
        if 'RSI' not in df.columns:
            return
        
        ax.plot(df['Date'], df['RSI'], color='#ffff00', linewidth=1.5)
        
        # Add overbought/oversold lines
        ax.axhline(y=70, color='#ff0000', linestyle='--', linewidth=1, alpha=0.7, label='Overbought')
        ax.axhline(y=30, color='#00ff00', linestyle='--', linewidth=1, alpha=0.7, label='Oversold')
        ax.axhline(y=50, color='#666666', linestyle='-', linewidth=0.5, alpha=0.5)
        
        # Fill regions
        ax.fill_between(df['Date'], df['RSI'], 70, where=(df['RSI'] >= 70), 
                        color='#ff0000', alpha=0.3)
        ax.fill_between(df['Date'], df['RSI'], 30, where=(df['RSI'] <= 30), 
                        color='#00ff00', alpha=0.3)
        
        ax.set_ylabel('RSI', fontweight='bold')
        ax.set_ylim(0, 100)
        ax.legend(loc='upper left', fontsize=8, framealpha=0.8)
        ax.grid(True, alpha=0.3)
    
    def _plot_macd(self, ax, df):
        """Plot MACD indicator"""
        if 'MACD' not in df.columns:
            return
        
        # Plot MACD and Signal lines
        ax.plot(df['Date'], df['MACD'], label='MACD', color='#00ffff', linewidth=1.5)
        ax.plot(df['Date'], df['MACD_Signal'], label='Signal', color='#ff9500', linewidth=1.5)
        
        # Plot histogram
        colors = ['#00ff00' if val >= 0 else '#ff0000' for val in df['MACD_Histogram']]
        ax.bar(df['Date'], df['MACD_Histogram'], color=colors, alpha=0.5, width=0.8)
        
        ax.axhline(y=0, color='#666666', linestyle='-', linewidth=0.5)
        ax.set_ylabel('MACD', fontweight='bold')
        ax.set_xlabel('Date', fontweight='bold')
        ax.legend(loc='upper left', fontsize=8, framealpha=0.8)
        ax.grid(True, alpha=0.3)
    
    def create_prediction_comparison_chart(self, df, predictions):
        """Create chart comparing actual vs predicted prices"""
        
        if df is None or predictions is None:
            return None
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot actual prices
        recent_df = df.tail(60)
        ax.plot(recent_df['Date'], recent_df['Close'], 
               label='Actual Price', 
               color='#00ff00', 
               linewidth=2)
        
        # Plot predictions
        last_date = recent_df['Date'].iloc[-1]
        pred_dates = pd.date_range(start=last_date, periods=len(predictions)+1, freq='D')[1:]
        pred_prices = [p['predicted_price'] for p in predictions]
        
        ax.plot(pred_dates, pred_prices, 
               label='Predicted Price', 
               color='#ff00ff', 
               linewidth=2,
               linestyle='--',
               marker='o',
               markersize=4)
        
        # Styling
        ax.set_title(f'{self.symbol} - Price Prediction (Next {len(predictions)} Days)', 
                    fontsize=14, fontweight='bold', color='white')
        ax.set_xlabel('Date', fontweight='bold')
        ax.set_ylabel('Price (₹)', fontweight='bold')
        ax.legend(loc='best', fontsize=10, framealpha=0.8)
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)
        
        # Save chart
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{self.symbol}_prediction_{timestamp}.png'
        filepath = os.path.join(Config.CHART_OUTPUT_DIR, filename)
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=Config.CHART_DPI, facecolor='#1e1e1e')
        plt.close()
        
        return filepath
    
    def create_indicator_summary_chart(self, df):
        """Create summary chart of all indicators"""
        
        if df is None or df.empty:
            return None
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.patch.set_facecolor('#1e1e1e')
        
        recent_df = df.tail(90)
        
        # Chart 1: Price with SMAs
        ax1 = axes[0, 0]
        ax1.plot(recent_df['Date'], recent_df['Close'], label='Close', color='#00ff00', linewidth=2)
        if 'SMA_20' in recent_df.columns:
            ax1.plot(recent_df['Date'], recent_df['SMA_20'], label='SMA 20', color='#ff9500')
        if 'SMA_50' in recent_df.columns:
            ax1.plot(recent_df['Date'], recent_df['SMA_50'], label='SMA 50', color='#ff0000')
        ax1.set_title('Price & Moving Averages', fontweight='bold', color='white')
        ax1.legend(fontsize=8)
        ax1.grid(True, alpha=0.3)
        
        # Chart 2: RSI
        ax2 = axes[0, 1]
        if 'RSI' in recent_df.columns:
            ax2.plot(recent_df['Date'], recent_df['RSI'], color='#ffff00', linewidth=2)
            ax2.axhline(y=70, color='#ff0000', linestyle='--', alpha=0.7)
            ax2.axhline(y=30, color='#00ff00', linestyle='--', alpha=0.7)
            ax2.set_ylim(0, 100)
        ax2.set_title('RSI Indicator', fontweight='bold', color='white')
        ax2.grid(True, alpha=0.3)
        
        # Chart 3: Volume
        ax3 = axes[1, 0]
        colors = ['#00ff00' if recent_df['Close'].iloc[i] >= recent_df['Open'].iloc[i] 
                 else '#ff0000' for i in range(len(recent_df))]
        ax3.bar(recent_df['Date'], recent_df['Volume'], color=colors, alpha=0.6)
        ax3.set_title('Volume', fontweight='bold', color='white')
        ax3.grid(True, alpha=0.3)
        
        # Chart 4: MACD
        ax4 = axes[1, 1]
        if 'MACD' in recent_df.columns:
            ax4.plot(recent_df['Date'], recent_df['MACD'], label='MACD', color='#00ffff')
            ax4.plot(recent_df['Date'], recent_df['MACD_Signal'], label='Signal', color='#ff9500')
            colors = ['#00ff00' if val >= 0 else '#ff0000' for val in recent_df['MACD_Histogram']]
            ax4.bar(recent_df['Date'], recent_df['MACD_Histogram'], color=colors, alpha=0.5)
            ax4.axhline(y=0, color='#666666', linestyle='-', linewidth=0.5)
        ax4.set_title('MACD', fontweight='bold', color='white')
        ax4.legend(fontsize=8)
        ax4.grid(True, alpha=0.3)
        
        # Format all x-axes
        for ax in axes.flat:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.suptitle(f'{self.symbol} - Technical Indicators Summary', 
                    fontsize=16, fontweight='bold', color='white', y=0.995)
        
        # Save chart
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{self.symbol}_indicators_{timestamp}.png'
        filepath = os.path.join(Config.CHART_OUTPUT_DIR, filename)
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=Config.CHART_DPI, facecolor='#1e1e1e')
        plt.close()
        
        return filepath


def generate_charts(symbol, df, prediction_data=None, recommendation=None):
    """Quick function to generate all charts"""
    generator = ChartGenerator(symbol)
    
    charts = {
        'comprehensive': generator.create_comprehensive_chart(df, prediction_data, recommendation),
        'indicators': generator.create_indicator_summary_chart(df)
    }
    
    if prediction_data and isinstance(prediction_data, list):
        charts['prediction'] = generator.create_prediction_comparison_chart(df, prediction_data)
    
    return charts
