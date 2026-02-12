# AI Stock Recommendation Chatbot (Flask + ML)

A complete backend-only chatbot project using:
- Python + Flask
- Scikit-learn `RandomForestRegressor`
- NLTK simple intent classification
- Yahoo Finance (`yfinance`) for Indian stock data

No LLM. No sentiment analysis.

## Features
- Predict next-day closing price
- Buy / Sell / Hold recommendation
- Expected return (%) and estimated P/L
- Simple NLP chatbot route

## Project Structure
```
ai_stock_chatbot/
  app.py
  config.py
  utils.py
  data_loader.py
  feature_engineering.py
  model_manager.py
  recommender.py
  chatbot_nlp.py
  requirements.txt
  models/
```

## Setup
1. Open terminal in `ai_stock_chatbot` folder
2. Create venv:
   - Windows:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

## Run
```powershell
python app.py
```
Server starts at: `http://localhost:5050`

## API Usage

### 1) Predict
`POST /predict`

Body:
```json
{
  "stock": "RELIANCE",
  "amount": 50000,
  "risk": "medium"
}
```

### 2) Chat
`POST /chat`

Body:
```json
{
  "message": "Should I buy TCS with 20000 and low risk?"
}
```

## Notes
- Symbols are normalized to NSE by default (`.NS`) if suffix is not provided.
- Model is retrained on latest historical data per request for freshness.
- You can cache/reuse training for production optimization.
