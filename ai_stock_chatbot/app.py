from flask import Flask, jsonify, request
from flask_cors import CORS

from config import settings
from data_loader import MarketDataLoader
from feature_engineering import FeatureBuilder
from model_manager import StockModelManager
from recommender import recommend_action
from chatbot_nlp import StockChatbot
from utils import normalize_risk, parse_amount, normalize_symbol


app = Flask(__name__)
CORS(app)

loader = MarketDataLoader()
features = FeatureBuilder()
models = StockModelManager()
chatbot = StockChatbot()

# Lightweight in-memory conversation context.
chat_context = {"stock": None, "amount": None, "risk": "medium"}


def _run_prediction(stock: str, amount: float, risk: str):
    symbol = normalize_symbol(stock)
    df = loader.fetch_stock_history(symbol, period=settings.default_period, interval=settings.default_interval)
    if df.empty:
        return None, f"No historical data found for {symbol}."

    X, y, last_row, current_close = features.build(df)
    if X is None or y is None or last_row is None:
        return None, "Not enough valid historical data to build features."

    train_result = models.train_model(symbol, X, y)
    if not train_result.get("success"):
        return None, f"Model training failed: {train_result.get('error', 'unknown error')}"

    predicted_close = models.predict_next_close(symbol, last_row)
    if predicted_close is None:
        return None, "Prediction failed for this stock."

    reco = recommend_action(
        current_price=current_close,
        predicted_price=predicted_close,
        amount=amount,
        risk_level=risk,
    )

    payload = {
        "symbol": symbol,
        "current_close": round(current_close, 2),
        "predicted_next_close": round(predicted_close, 2),
        "risk_level": risk,
        "investment_amount": round(amount, 2),
        "recommendation": reco,
        "model_metrics": train_result.get("metrics", {}),
    }
    return payload, None


@app.route("/")
def home():
    return jsonify(
        {
            "message": "AI Stock Recommendation Chatbot API",
            "routes": {
                "predict": "POST /predict",
                "chat": "POST /chat",
            },
        }
    )


@app.route("/predict", methods=["POST"])
def predict():
    """
    Input JSON:
    {
      "stock": "RELIANCE",
      "amount": 50000,
      "risk": "medium"
    }
    """
    data = request.get_json() or {}

    stock = data.get("stock")
    amount = parse_amount(data.get("amount"))
    risk = normalize_risk(data.get("risk"))

    if not stock:
        return jsonify({"success": False, "error": "'stock' is required."}), 400
    if amount is None or amount <= 0:
        return jsonify({"success": False, "error": "'amount' must be a positive number."}), 400

    result, error = _run_prediction(stock=stock, amount=amount, risk=risk)
    if error:
        return jsonify({"success": False, "error": error}), 400

    return jsonify({"success": True, "data": result})


@app.route("/chat", methods=["POST"])
def chat():
    """
    Input JSON:
    {
      "message": "Should I buy TCS with 20000 and low risk?"
    }
    """
    global chat_context

    data = request.get_json() or {}
    message = str(data.get("message", "")).strip()
    if not message:
        return jsonify({"success": False, "error": "'message' is required."}), 400

    reply, updated_context = chatbot.respond(message, chat_context)
    chat_context = updated_context

    if reply != "PROCESS_PREDICTION":
        return jsonify({
            "success": True,
            "response": reply,
            "context": chat_context,
        })

    result, error = _run_prediction(
        stock=chat_context["stock"],
        amount=float(chat_context["amount"]),
        risk=normalize_risk(chat_context["risk"]),
    )

    if error:
        return jsonify({"success": True, "response": f"I could not process this request: {error}"})

    reco = result["recommendation"]
    response_text = (
        f"For {result['symbol']}, current close is INR {result['current_close']} and "
        f"predicted next close is INR {result['predicted_next_close']}. "
        f"Recommendation: {reco['action']}. "
        f"Expected return: {reco['expected_return_pct']}%. "
        f"Estimated P/L on INR {result['investment_amount']}: INR {reco['estimated_profit']}. "
        f"Reason: {reco['reason']}"
    )

    return jsonify({
        "success": True,
        "response": response_text,
        "data": result,
    })


if __name__ == "__main__":
    app.run(host=settings.app_host, port=settings.app_port, debug=settings.debug)
