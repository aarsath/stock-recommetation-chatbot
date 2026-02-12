# 🚀 Complete Setup Guide - Stock Analysis AI Platform

## System Requirements

### Minimum Requirements:
- **OS**: Ubuntu 20.04+, macOS 11+, or Windows 10+
- **Python**: 3.8 or higher
- **Node.js**: 14 or higher
- **RAM**: 8GB (16GB recommended for LLM)
- **Storage**: 10GB free space
- **GPU**: Optional (NVIDIA GPU with CUDA for faster LLM inference)

---

## 📥 Installation Steps

### Step 1: Clone or Download the Project

```bash
# If using git
git clone <your-repo-url>
cd stock_ai_project

# Or download and extract the ZIP file
```

### Step 2: Backend Setup

```bash
cd backend

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt --break-system-packages

# Create necessary directories
mkdir -p static/charts
mkdir -p ml/models
```

### Step 3: Frontend Setup

```bash
cd ../frontend

# Install Node.js dependencies
npm install

# Or using yarn
yarn install
```

### Step 4: Environment Configuration

#### Backend (.env):
```bash
cd ../backend

# Edit .env file
nano .env
```

Configure:
```
SECRET_KEY=your-super-secret-key-here
DEBUG=True
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.1
HF_TOKEN=  # Optional: Add Hugging Face token for gated models
```

#### Frontend (.env):
```bash
cd ../frontend

# Edit .env file
nano .env
```

Configure:
```
REACT_APP_API_URL=http://localhost:5000/api
```

---

## 🏃 Running the Application

### Option 1: Development Mode (Recommended for Testing)

#### Terminal 1 - Start Backend:
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python app.py
```

Backend will run on: `http://localhost:5000`

#### Terminal 2 - Start Frontend:
```bash
cd frontend
npm start
```

Frontend will run on: `http://localhost:3000`

### Option 2: Production Mode

#### Build Frontend:
```bash
cd frontend
npm run build
```

#### Serve with Flask:
```bash
cd backend
# Install production server
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 🧪 Testing the Application

### 1. Basic API Test:
```bash
# Test if backend is running
curl http://localhost:5000/

# Test stock search
curl http://localhost:5000/api/search-stock?query=RELIANCE

# Test live price
curl http://localhost:5000/api/live-price/RELIANCE.NS
```

### 2. Frontend Test:
- Open browser: `http://localhost:3000`
- Search for "RELIANCE" or "TCS"
- Select a stock from results
- Wait for analysis to complete

---

## 🔧 Troubleshooting

### Issue 1: Python Package Installation Errors

**Error**: `externally-managed-environment`

**Solution**:
```bash
# Use --break-system-packages flag
pip install -r requirements.txt --break-system-packages

# Or use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Issue 2: Port Already in Use

**Backend Port 5000 busy**:
```bash
# Find and kill the process
lsof -i :5000
kill -9 <PID>

# Or change port in app.py:
app.run(port=5001)
```

**Frontend Port 3000 busy**:
```bash
# Change port
PORT=3001 npm start
```

### Issue 3: CORS Errors

Ensure backend has CORS enabled:
```python
from flask_cors import CORS
CORS(app)
```

### Issue 4: LLM Model Not Loading

**Out of memory**:
- Use smaller model: `google/flan-t5-large` (requires less RAM)
- Disable LLM (app will use rule-based analysis)
- Add more RAM or use GPU

**Slow loading**:
- First time loading downloads the model (~4-14GB)
- Be patient, subsequent loads are faster

### Issue 5: Yahoo Finance API Errors

**No data returned**:
- Check internet connection
- Verify symbol format (use `.NS` for NSE stocks)
- Try alternative symbol

---

## 🎯 Using the Application

### 1. Search for a Stock:
- Enter stock name or symbol (e.g., "RELIANCE", "TCS", "INFY")
- Click on search result
- Or use quick access buttons for popular stocks

### 2. View Analysis:
- **Overview Tab**: Technical signals and scores
- **Charts Tab**: Price charts with indicators (SMA, RSI, MACD, Volume)
- **AI Analysis Tab**: Complete AI-generated analysis
- **Ask AI Tab**: Interactive chatbot

### 3. Get Recommendations:
- View Buy/Sell/Hold recommendation
- Check confidence score
- Read detailed signal explanations

### 4. Chat with AI:
- Ask questions like:
  - "Should I buy this stock?"
  - "What is the risk level?"
  - "What are the technical indicators showing?"
  - "What is the price prediction?"

---

## 📊 Understanding the Indicators

### RSI (Relative Strength Index):
- **Above 70**: Overbought (potential sell signal)
- **Below 30**: Oversold (potential buy signal)
- **50**: Neutral

### MACD (Moving Average Convergence Divergence):
- **MACD > Signal**: Bullish
- **MACD < Signal**: Bearish
- **Histogram**: Momentum strength

### Moving Averages:
- **Price > SMA 20 > SMA 50**: Strong uptrend
- **Price < SMA 20 < SMA 50**: Strong downtrend

### Bollinger Bands:
- **Price at upper band**: Overbought
- **Price at lower band**: Oversold

---

## 🔐 Security Notes

### Production Deployment:
1. Change `SECRET_KEY` in `.env`
2. Set `DEBUG=False`
3. Use HTTPS
4. Add authentication
5. Implement rate limiting
6. Use environment variables for sensitive data

### API Keys:
- Store Hugging Face token in `.env` file
- Never commit `.env` to version control
- Add `.env` to `.gitignore`

---

## 📈 Performance Optimization

### Backend:
1. **Use Redis for caching**:
   ```bash
   pip install redis
   ```

2. **Enable model caching**:
   - Models are cached after first load
   - Reuse predictor instances

3. **Use GPU for LLM** (if available):
   - Automatically detected
   - 10x faster inference

### Frontend:
1. **Build for production**:
   ```bash
   npm run build
   ```

2. **Use CDN for static files**

3. **Enable lazy loading for charts**

---

## 🆘 Support

### Common Questions:

**Q: Which stocks are supported?**
A: All NSE and BSE stocks, plus major indices (NIFTY 50, BANK NIFTY, etc.)

**Q: How often is data updated?**
A: Live data is fetched in real-time via Yahoo Finance API

**Q: Can I use this for trading?**
A: This is for educational purposes only. Always consult a financial advisor.

**Q: Which LLM model should I use?**
A: 
- `mistralai/Mistral-7B-Instruct-v0.1`: Best quality (14GB RAM)
- `google/flan-t5-large`: Faster, less RAM (4GB RAM)
- Rule-based: No LLM, instant responses

**Q: How accurate are the predictions?**
A: ML predictions are based on historical patterns. Past performance doesn't guarantee future results.

---

## 📝 Next Steps

1. **Customize**: Modify technical indicator parameters in `config.py`
2. **Extend**: Add new features (email alerts, portfolio tracking)
3. **Deploy**: Host on cloud (AWS, Google Cloud, Heroku)
4. **Monitor**: Add logging and analytics

---

## ⚠️ Disclaimer

This application is for educational and research purposes only. Stock market investments carry risk. Always do your own research and consult with qualified financial advisors before making investment decisions.

---

**Happy Trading! 📊🚀**
