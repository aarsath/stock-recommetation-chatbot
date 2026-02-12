import re
from typing import Optional


def normalize_symbol(stock: str) -> str:
    """Normalize symbol for Indian market on Yahoo Finance (NSE)."""
    if not stock:
        return ""
    symbol = stock.strip().upper()

    # Already has exchange suffix.
    if symbol.endswith(".NS") or symbol.endswith(".BO"):
        return symbol

    # Common user input like "RELIANCE" -> "RELIANCE.NS"
    return f"{symbol}.NS"


def parse_amount(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = re.sub(r"[^0-9.]", "", str(value))
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def normalize_risk(risk: str) -> str:
    if not risk:
        return "medium"
    text = str(risk).strip().lower()
    if text in {"low", "conservative"}:
        return "low"
    if text in {"high", "aggressive"}:
        return "high"
    return "medium"
