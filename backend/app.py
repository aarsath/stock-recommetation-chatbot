"""
Main Flask Application
REST API for Stock Analysis Platform
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import os
from datetime import datetime
import math

# Import modules
from config import Config
from data_fetcher import StockDataFetcher, fetch_live_price, fetch_complete_data
from ml.predictor import StockPredictor
from recommender import StockRecommender, get_recommendation
from chart_generator import ChartGenerator, generate_charts
from llm_analyzer import LLMAnalyzer, analyze_stock, chat_response
from symbol_list import StockSymbols, get_stock_name

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Create necessary directories
os.makedirs(Config.CHART_OUTPUT_DIR, exist_ok=True)
os.makedirs(Config.MODEL_PATH, exist_ok=True)

# Global instances
llm_analyzer = LLMAnalyzer()

# Store analysis cache (in production, use Redis)
analysis_cache = {}


@app.route('/')
def home():
    """API Home"""
    return jsonify({
        'message': 'Stock Analysis AI API',
        'version': '1.0.0',
        'endpoints': {
            'search': '/api/search-stock?query=RELIANCE',
            'live_price': '/api/live-price/<symbol>',
            'historical': '/api/historical/<symbol>',
            'predict': '/api/predict/<symbol>',
            'recommend': '/api/recommend/<symbol>',
            'analyze': '/api/analyze/<symbol>',
            'charts': '/api/charts/<symbol>',
            'chat': '/api/chat (POST)',
            'portfolio': '/api/portfolio-recommendations (POST)',
        }
    })


@app.route('/api/search-stock', methods=['GET'])
def search_stock():
    """Search for stock symbols"""
    query = request.args.get('query', '')
    
    if not query:
        return jsonify({'error': 'Query parameter required'}), 400
    
    results = StockSymbols.search_symbol(query)
    
    return jsonify({
        'query': query,
        'results': results,
        'count': len(results)
    })


@app.route('/api/live-price/<symbol>', methods=['GET'])
def get_live_price(symbol):
    """Get live stock price"""
    try:
        # Format symbol
        formatted_symbol = StockSymbols.format_symbol(symbol)
        
        # Fetch live data
        live_data = fetch_live_price(formatted_symbol)
        
        if not live_data:
            return jsonify({'error': 'Failed to fetch live price'}), 404
        
        return jsonify({
            'success': True,
            'data': live_data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/historical/<symbol>', methods=['GET'])
def get_historical(symbol):
    """Get historical stock data"""
    try:
        # Get days parameter
        days = request.args.get('days', 365, type=int)
        
        # Format symbol
        formatted_symbol = StockSymbols.format_symbol(symbol)
        
        # Fetch data
        fetcher = StockDataFetcher(formatted_symbol)
        df = fetcher.get_historical_data(days)
        
        if df is None:
            return jsonify({'error': 'Failed to fetch historical data'}), 404
        
        # Calculate indicators
        df_with_indicators = fetcher.calculate_technical_indicators(df)
        
        # Convert to JSON
        data = df_with_indicators.to_dict(orient='records')
        
        # Convert datetime to string
        for record in data:
            if 'Date' in record and hasattr(record['Date'], 'strftime'):
                record['Date'] = record['Date'].strftime('%Y-%m-%d')
        
        return jsonify({
            'success': True,
            'symbol': formatted_symbol,
            'data': data,
            'count': len(data)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/predict/<symbol>', methods=['GET', 'POST'])
def predict_stock(symbol):
    """Train ML model and predict future prices"""
    try:
        # Format symbol
        formatted_symbol = StockSymbols.format_symbol(symbol)
        
        # Get parameters
        days = request.args.get('days', 30, type=int)
        retrain = request.args.get('retrain', 'false').lower() == 'true'
        
        # Fetch complete data
        fetcher = StockDataFetcher(formatted_symbol)
        complete_data = fetcher.get_complete_data()
        
        if not complete_data:
            return jsonify({'error': 'Failed to fetch stock data'}), 404
        
        df = complete_data['historical']
        
        # Initialize predictor
        predictor = StockPredictor()
        
        # Try to load existing model
        model_loaded = False
        if not retrain:
            model_loaded = predictor.load_model(formatted_symbol)
        
        # Train if needed
        if not model_loaded:
            print(f"Training model for {formatted_symbol}...")
            train_result = predictor.train(df)
            
            if not train_result['success']:
                return jsonify({'error': train_result.get('error')}), 400
            
            # Save model
            predictor.save_model(formatted_symbol)
            
            print(f"Model trained: MAE={train_result['test_mae']}, RÂ²={train_result['test_r2']}")
        
        # Predict
        predictions = predictor.predict(df, days)
        next_day_pred = predictor.predict_next_day(df)
        feature_importance = predictor.get_feature_importance()
        
        return jsonify({
            'success': True,
            'symbol': formatted_symbol,
            'next_day': next_day_pred,
            'predictions': predictions,
            'feature_importance': feature_importance,
            'model_retrained': not model_loaded
        })
    
    except Exception as e:
        print(f"Prediction error: {str(e)}")
        return jsonify({'error': str(e)}), 500



@app.route('/api/predict-indicator/<symbol>', methods=['GET'])
def predict_indicator(symbol):
    """Return compact AI future price prediction indicator for right-side panel"""
    try:
        formatted_symbol = StockSymbols.format_symbol(symbol)
        days = request.args.get('days', 5, type=int)
        days = max(3, min(days, 5))
        retrain = request.args.get('retrain', 'false').lower() == 'true'

        def _heuristic_projection(live_data, engine='heuristic_fallback'):
            current_price = float((live_data or {}).get('price', 0) or 0)
            change_pct = float((live_data or {}).get('change_percent', 0) or 0)

            projected_daily_return = max(-0.03, min(0.03, (change_pct / 100.0) * 0.35))

            timeline = []
            running_price = current_price
            for day in range(1, days + 1):
                running_price = running_price * (1 + projected_daily_return)
                timeline.append({
                    'day': day,
                    'predicted_price': round(float(running_price), 2)
                })

            predicted_last = timeline[-1]['predicted_price'] if timeline else current_price
            delta = predicted_last - current_price
            pct_change = (delta / current_price * 100) if current_price else 0.0

            if abs(delta) < 0.01:
                trend = 'HOLD'
                trend_label = 'Stable'
            elif delta > 0:
                trend = 'INCREASE'
                trend_label = 'Increase'
            else:
                trend = 'DECREASE'
                trend_label = 'Decrease'

            if delta > 0.01:
                ai_signal = 'BUY'
            elif delta < -0.01:
                ai_signal = 'SELL'
            else:
                ai_signal = 'HOLD'

            return {
                'success': True,
                'symbol': formatted_symbol,
                'days': days,
                'current_price': round(current_price, 2),
                'future_predictions': timeline,
                'trend': trend,
                'trend_label': trend_label,
                'percentage_change': round(pct_change, 2),
                'confidence_score': 35.0,
                'ai_signal': ai_signal,
                'engine': engine
            }

        fetcher = StockDataFetcher(formatted_symbol)
        complete_data = fetcher.get_complete_data()

        # Primary path: ML prediction. Any model/data numeric failures auto-fallback.
        if complete_data:
            try:
                df = complete_data['historical']
                live_data = complete_data.get('live') or {}

                predictor = StockPredictor()
                model_loaded = predictor.load_model(formatted_symbol) if not retrain else False

                if not model_loaded:
                    train_result = predictor.train(df)
                    if not train_result['success']:
                        return jsonify({'error': train_result.get('error', 'Model training failed')}), 400
                    predictor.save_model(formatted_symbol)

                predictions = predictor.predict(df, days) or []
                next_day = predictor.predict_next_day(df) or {}

                if predictions:
                    current_price = live_data.get('price')
                    if current_price is None:
                        current_price = float(df['Close'].iloc[-1]) if df is not None and not df.empty else 0

                    current_price = float(current_price or 0)
                    predicted_last = float(predictions[-1].get('predicted_price', current_price) or current_price)
                    delta = predicted_last - current_price
                    pct_change = (delta / current_price * 100) if current_price else 0.0

                    if abs(delta) < 0.01:
                        trend = 'HOLD'
                        trend_label = 'Stable'
                    elif delta > 0:
                        trend = 'INCREASE'
                        trend_label = 'Increase'
                    else:
                        trend = 'DECREASE'
                        trend_label = 'Decrease'

                    if delta > 0.01:
                        ai_signal = 'BUY'
                    elif delta < -0.01:
                        ai_signal = 'SELL'
                    else:
                        ai_signal = 'HOLD'

                    confidence_score = float(next_day.get('confidence', 0.0) or 0.0) * 100
                    confidence_score = max(0.0, min(100.0, confidence_score))

                    timeline = []
                    for point in predictions:
                        timeline.append({
                            'day': int(point.get('day', 0) or 0),
                            'predicted_price': round(float(point.get('predicted_price', 0) or 0), 2)
                        })

                    return jsonify({
                        'success': True,
                        'symbol': formatted_symbol,
                        'days': days,
                        'current_price': round(current_price, 2),
                        'future_predictions': timeline,
                        'trend': trend,
                        'trend_label': trend_label,
                        'percentage_change': round(pct_change, 2),
                        'confidence_score': round(confidence_score, 2),
                        'ai_signal': ai_signal,
                        'engine': 'ml'
                    })
            except Exception as ml_err:
                print(f"Predict indicator ML fallback for {formatted_symbol}: {str(ml_err)}")

            # If ML failed but live data exists, still return heuristic projection.
            live_data = complete_data.get('live') or fetch_live_price(formatted_symbol)
            if live_data:
                return jsonify(_heuristic_projection(live_data, engine='ml_fallback'))

        # Last fallback path: direct live fetch when complete_data unavailable
        live_data = fetch_live_price(formatted_symbol)
        if not live_data:
            return jsonify({'error': f'Failed to fetch stock data for {formatted_symbol}'}), 404

        return jsonify(_heuristic_projection(live_data, engine='heuristic_fallback'))

    except Exception as e:
        print(f"Predict indicator error: {str(e)}")
        return jsonify({'error': str(e)}), 500
@app.route('/api/recommend/<symbol>', methods=['GET'])
def recommend_stock(symbol):
    """Get Buy/Sell/Hold recommendation"""
    try:
        # Format symbol
        formatted_symbol = StockSymbols.format_symbol(symbol)
        
        # Check cache
        cache_key = f"{formatted_symbol}_recommend"
        if cache_key in analysis_cache:
            cached = analysis_cache[cache_key]
            # Check if cache is less than 5 minutes old
            if (datetime.now() - cached['timestamp']).seconds < 300:
                return jsonify(cached['data'])
        
        # Fetch complete data
        fetcher = StockDataFetcher(formatted_symbol)
        complete_data = fetcher.get_complete_data()
        
        if not complete_data:
            return jsonify({'error': 'Failed to fetch stock data'}), 404
        
        df = complete_data['historical']
        live_data = complete_data['live']
        
        # Get prediction
        predictor = StockPredictor()
        predictor.load_model(formatted_symbol)
        
        if predictor.is_trained:
            prediction_data = predictor.predict_next_day(df)
        else:
            prediction_data = None
        
        # Get recommendation
        recommendation = get_recommendation(df, prediction_data, live_data)
        
        response = {
            'success': True,
            'symbol': formatted_symbol,
            'name': get_stock_name(formatted_symbol),
            'live_price': live_data,
            'recommendation': recommendation
        }
        
        # Cache result
        analysis_cache[cache_key] = {
            'data': response,
            'timestamp': datetime.now()
        }
        
        return jsonify(response)
    
    except Exception as e:
        print(f"Recommendation error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio-recommendations', methods=['POST'])
def portfolio_recommendations():
    """Generate portfolio recommendations for multiple stocks"""
    try:
        data = request.get_json() or {}
        symbols = data.get('symbols', [])
        budget = data.get('budget', 0)

        if not isinstance(symbols, list) or not symbols:
            return jsonify({'error': 'Symbols list required'}), 400

        try:
            budget = float(budget)
        except (TypeError, ValueError):
            budget = 0

        if budget <= 0:
            return jsonify({'error': 'Valid budget required'}), 400

        unique_symbols = []
        seen = set()
        for symbol in symbols:
            if not isinstance(symbol, str):
                continue
            cleaned = symbol.strip().upper()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                unique_symbols.append(cleaned)

        if not unique_symbols:
            return jsonify({'error': 'Symbols list required'}), 400

        allocations = []
        total_buy_score = 0

        for symbol in unique_symbols:
            formatted_symbol = StockSymbols.format_symbol(symbol)
            try:
                fetcher = StockDataFetcher(formatted_symbol)
                complete_data = fetcher.get_complete_data()

                if not complete_data:
                    allocations.append({
                        'symbol': formatted_symbol,
                        'error': 'Failed to fetch stock data'
                    })
                    continue

                df = complete_data['historical']
                live_data = complete_data['live']

                predictor = StockPredictor()
                predictor.load_model(formatted_symbol)
                prediction_data = predictor.predict_next_day(df) if predictor.is_trained else None

                recommendation = get_recommendation(df, prediction_data, live_data)
                score = recommendation.get('score', 0) if recommendation else 0
                action = recommendation.get('action') if recommendation else None

                is_buy = action == 'BUY'
                if is_buy:
                    total_buy_score += score

                allocations.append({
                    'symbol': formatted_symbol,
                    'name': get_stock_name(formatted_symbol),
                    'recommendation': recommendation,
                    'live_price': live_data,
                    'score': score,
                    'eligible': is_buy
                })
            except Exception as inner_err:
                allocations.append({
                    'symbol': formatted_symbol,
                    'error': str(inner_err)
                })

        total_invested = 0.0
        for item in allocations:
            if not item.get('eligible') or total_buy_score <= 0:
                item['weight'] = 0
                item['allocation_amount'] = 0
                item['shares'] = 0
                item['invested_amount'] = 0
                item['unallocated_amount'] = 0
                continue

            weight = item['score'] / total_buy_score if total_buy_score > 0 else 0
            allocation_amount = budget * weight
            live_price = item.get('live_price') or {}
            price = live_price.get('price', 0)

            if price and price > 0:
                shares = math.floor(allocation_amount / price)
                invested_amount = shares * price
                unallocated_amount = allocation_amount - invested_amount
            else:
                shares = 0
                invested_amount = 0
                unallocated_amount = allocation_amount

            item['weight'] = round(weight, 4)
            item['allocation_amount'] = round(allocation_amount, 2)
            item['shares'] = int(shares)
            item['invested_amount'] = round(invested_amount, 2)
            item['unallocated_amount'] = round(unallocated_amount, 2)

            total_invested += invested_amount

        remaining_cash = round(budget - total_invested, 2)

        return jsonify({
            'success': True,
            'budget': budget,
            'total_invested': round(total_invested, 2),
            'remaining_cash': remaining_cash,
            'allocations': allocations
        })
    except Exception as e:
        print(f"Portfolio recommendation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze/<symbol>', methods=['GET'])
def analyze_stock_endpoint(symbol):
    """Get complete AI analysis"""
    try:
        # Format symbol
        formatted_symbol = StockSymbols.format_symbol(symbol)
        
        # Fetch complete data
        fetcher = StockDataFetcher(formatted_symbol)
        complete_data = fetcher.get_complete_data()
        
        if not complete_data:
            return jsonify({'error': 'Failed to fetch stock data'}), 404
        
        df = complete_data['historical']
        live_data = complete_data['live']
        
        # Get prediction
        predictor = StockPredictor()
        model_loaded = predictor.load_model(formatted_symbol)
        
        if not model_loaded:
            # Train model
            predictor.train(df)
            predictor.save_model(formatted_symbol)
        
        prediction_data = predictor.predict_next_day(df)
        
        # Get recommendation
        recommendation = get_recommendation(df, prediction_data, live_data)
        
        # Generate LLM analysis
        technical_signals = recommendation['signals']['technical']
        llm_analysis = analyze_stock(complete_data, recommendation, technical_signals)
        
        return jsonify({
            'success': True,
            'symbol': formatted_symbol,
            'name': get_stock_name(formatted_symbol),
            'live_price': live_data,
            'prediction': prediction_data,
            'recommendation': recommendation,
            'ai_analysis': llm_analysis
        })
    
    except Exception as e:
        print(f"Analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/charts/<symbol>', methods=['GET'])
def generate_stock_charts(symbol):
    """Generate technical analysis charts"""
    try:
        # Format symbol
        formatted_symbol = StockSymbols.format_symbol(symbol)
        
        # Fetch complete data
        fetcher = StockDataFetcher(formatted_symbol)
        complete_data = fetcher.get_complete_data()
        
        if not complete_data:
            return jsonify({'error': 'Failed to fetch stock data'}), 404
        
        df = complete_data['historical']
        live_data = complete_data['live']
        
        # Get prediction
        predictor = StockPredictor()
        predictor.load_model(formatted_symbol)
        
        predictions = None
        if predictor.is_trained:
            predictions = predictor.predict(df, 30)
        
        # Get recommendation
        prediction_data = predictor.predict_next_day(df) if predictor.is_trained else None
        recommendation = get_recommendation(df, prediction_data, live_data)
        
        # Generate charts
        charts = generate_charts(formatted_symbol, df, predictions, recommendation)
        
        # Convert file paths to relative URLs
        chart_urls = {}
        for chart_type, filepath in charts.items():
            if filepath:
                filename = os.path.basename(filepath)
                chart_urls[chart_type] = f"/static/charts/{filename}"
        
        return jsonify({
            'success': True,
            'symbol': formatted_symbol,
            'charts': chart_urls
        })
    
    except Exception as e:
        print(f"Chart generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
@app.route('/api/chatbot', methods=['POST'])
def chat():
    """AI multilingual chatbot endpoint"""
    try:
        data = request.get_json() or {}

        user_query = data.get('query', '')
        symbol = data.get('symbol', '')
        language = data.get('language')

        if not user_query:
            return jsonify({'error': 'Query required'}), 400

        # General finance chat is allowed without a selected symbol.
        complete_data = {'live': {}}
        recommendation = {'recommendation': 'HOLD', 'score': 50, 'summary': 'No stock selected yet.'}
        prediction_data = None
        formatted_symbol = None

        if symbol:
            formatted_symbol = StockSymbols.format_symbol(symbol)

            fetcher = StockDataFetcher(formatted_symbol)
            fetched = fetcher.get_complete_data()
            if fetched:
                complete_data = fetched

                df = complete_data['historical']
                live_data = complete_data['live']

                predictor = StockPredictor()
                predictor.load_model(formatted_symbol)
                prediction_data = predictor.predict_next_day(df) if predictor.is_trained else None

                recommendation = get_recommendation(df, prediction_data, live_data)

        chat_payload = chat_response(
            user_query,
            complete_data,
            recommendation,
            prediction_data=prediction_data,
            preferred_language=language,
        )

        return jsonify({
            'success': True,
            'query': user_query,
            'response': chat_payload.get('response', ''),
            'language': chat_payload.get('language', language or 'en'),
            'intent': chat_payload.get('detected_intent', 'default'),
            'symbol': formatted_symbol,
        })

    except Exception as e:
        print(f"Chat error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/load-llm', methods=['POST'])
def load_llm_model():
    """Load Hugging Face LLM model"""
    try:
        success = llm_analyzer.load_model()
        
        return jsonify({
            'success': success,
            'model': Config.HF_MODEL,
            'loaded': llm_analyzer.is_loaded
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/static/charts/<filename>')
def serve_chart(filename):
    """Serve generated chart images"""
    filepath = os.path.join(Config.CHART_OUTPUT_DIR, filename)
    
    if os.path.exists(filepath):
        return send_file(filepath, mimetype='image/png')
    else:
        return jsonify({'error': 'Chart not found'}), 404


@app.route('/api/indices', methods=['GET'])
def get_indices():
    """Get market indices"""
    return jsonify({
        'success': True,
        'indices': StockSymbols.INDICES
    })


@app.route('/api/popular-stocks', methods=['GET'])
def get_popular_stocks():
    """Get popular stocks list"""
    return jsonify({
        'success': True,
        'nifty_50': StockSymbols.NIFTY_50[:10],
        'bank_nifty': StockSymbols.BANK_NIFTY[:5],
        'popular': StockSymbols.POPULAR_NSE[:10]
    })


if __name__ == '__main__':
    print("="*50)
    print("Stock Analysis AI - Backend Server")
    print("="*50)
    print(f"Model: {Config.HF_MODEL}")
    print(f"Debug Mode: {Config.DEBUG}")
    print("="*50)
    
    # Optional: Pre-load LLM model (comment out if you want to load on-demand)
    # print("Loading LLM model...")
    # llm_analyzer.load_model()
    
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)









