import re
from typing import Dict, Tuple

import nltk
from nltk.stem import PorterStemmer
from nltk.tokenize import wordpunct_tokenize


class IntentClassifier:
    """Simple keyword + stem based intent classifier."""

    def __init__(self):
        self.stemmer = PorterStemmer()
        self.intent_keywords = {
            "predict": ["predict", "forecast", "next", "tomorrow", "price"],
            "recommend": ["buy", "sell", "hold", "recommend", "suggest"],
            "greet": ["hi", "hello", "hey"],
            "help": ["help", "how", "what", "usage"],
        }

        self.stemmed_index = {
            intent: {self.stemmer.stem(w) for w in words}
            for intent, words in self.intent_keywords.items()
        }

    def classify(self, text: str) -> str:
        tokens = [self.stemmer.stem(t.lower()) for t in wordpunct_tokenize(text or "")]
        if not tokens:
            return "help"

        scores = {}
        for intent, stems in self.stemmed_index.items():
            scores[intent] = sum(1 for t in tokens if t in stems)

        best_intent = max(scores, key=scores.get)
        return best_intent if scores[best_intent] > 0 else "help"


class ChatEntityExtractor:
    def extract(self, text: str) -> Dict:
        raw = text or ""

        # Symbol candidates: RELIANCE, TCS, INFY, etc.
        symbol_match = re.findall(r"\b[A-Z]{2,12}(?:\.NS|\.BO)?\b", raw.upper())
        symbol = symbol_match[0] if symbol_match else None

        amount_match = re.search(r"(?:rs|inr|?)?\s*([0-9]+(?:\.[0-9]+)?)", raw.lower())
        amount = float(amount_match.group(1)) if amount_match else None

        risk = None
        low_words = {"low", "safe", "conservative"}
        med_words = {"medium", "moderate"}
        high_words = {"high", "aggressive", "risky"}
        lower = raw.lower()
        if any(w in lower for w in low_words):
            risk = "low"
        elif any(w in lower for w in high_words):
            risk = "high"
        elif any(w in lower for w in med_words):
            risk = "medium"

        return {"stock": symbol, "amount": amount, "risk": risk}


class StockChatbot:
    """Rule-based NLP interface for stock recommendation workflow."""

    def __init__(self):
        self.intent = IntentClassifier()
        self.extractor = ChatEntityExtractor()

    def respond(self, message: str, context: Dict) -> Tuple[str, Dict]:
        intent = self.intent.classify(message)
        entities = self.extractor.extract(message)

        merged_context = {
            "stock": entities.get("stock") or context.get("stock"),
            "amount": entities.get("amount") or context.get("amount"),
            "risk": entities.get("risk") or context.get("risk") or "medium",
        }

        if intent == "greet":
            return (
                "Hi. Share stock name, investment amount, and risk level (low/medium/high). "
                "Example: 'Predict RELIANCE for 50000 with medium risk'.",
                merged_context,
            )

        if intent in {"predict", "recommend"}:
            if not merged_context.get("stock"):
                return "Please provide a stock symbol (example: RELIANCE or TCS).", merged_context
            if not merged_context.get("amount"):
                return "Please provide investment amount in INR.", merged_context
            if not merged_context.get("risk"):
                return "Please provide risk level: low, medium, or high.", merged_context

            return "PROCESS_PREDICTION", merged_context

        return (
            "I can predict next-day price and give Buy/Sell/Hold. "
            "Try: 'Should I buy INFY with 100000 and low risk?'",
            merged_context,
        )
