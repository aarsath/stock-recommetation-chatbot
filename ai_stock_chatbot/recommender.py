from typing import Dict


def recommend_action(current_price: float, predicted_price: float, amount: float, risk_level: str) -> Dict:
    """Generate Buy/Sell/Hold with expected return based on risk profile."""
    if current_price <= 0:
        return {
            "action": "HOLD",
            "expected_return_pct": 0.0,
            "estimated_profit": 0.0,
            "reason": "Invalid current price.",
        }

    expected_return_pct = ((predicted_price - current_price) / current_price) * 100

    thresholds = {
        "low": {"buy": 2.0, "sell": -1.5},
        "medium": {"buy": 1.0, "sell": -1.0},
        "high": {"buy": 0.5, "sell": -0.5},
    }
    risk = risk_level if risk_level in thresholds else "medium"
    t = thresholds[risk]

    if expected_return_pct >= t["buy"]:
        action = "BUY"
        reason = "Predicted upside is above your risk threshold."
    elif expected_return_pct <= t["sell"]:
        action = "SELL"
        reason = "Predicted downside is below your risk threshold."
    else:
        action = "HOLD"
        reason = "Predicted move is within neutral range for your risk profile."

    estimated_profit = (amount or 0) * (expected_return_pct / 100.0)

    return {
        "action": action,
        "expected_return_pct": round(expected_return_pct, 2),
        "estimated_profit": round(estimated_profit, 2),
        "reason": reason,
    }
