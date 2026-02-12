"""
Hugging Face Hosted LLM Stock Analyzer
Multilingual chatbot with Tanglish-aware NLP pipeline.
"""

from collections import OrderedDict
import re
import time

import requests

from config import Config


class LLMAnalyzer:
    def __init__(self):
        self.chat_model = Config.HF_CHAT_MODEL
        self.translation_model = Config.HF_TRANSLATION_MODEL
        self.api_base = Config.HF_API_BASE.rstrip('/')
        self.timeout = Config.HF_REQUEST_TIMEOUT
        self.hf_token = Config.HF_TOKEN
        self.is_loaded = True

        self.session = requests.Session()
        self.cache = OrderedDict()
        self.cache_size = 256

        self.language_names = {
            'en': 'English',
            'hi': 'Hindi',
            'ta': 'Tamil',
            'tanglish': 'Tanglish',
        }

        self.tanglish_patterns = {
            r'\bnalla\b': 'good',
            r'\biruka\b': 'is it',
            r'\birukka\b': 'is it',
            r'\bindha\b': 'this',
            r'\bintha\b': 'this',
            r'\bvanga\b': 'buy',
            r'\bvangalama\b': 'can i buy',
            r'\bpannalama\b': 'shall we do',
            r'\bvenuma\b': 'is it needed',
            r'\bsariya\b': 'is it right',
            r'\bepdi\b': 'how',
            r'\benna\b': 'what',
            r'\bipo\b': 'now',
            r'\bippo\b': 'now',
            r'\bvirkala\b': 'should i sell',
            r'\bvirkalaama\b': 'should i sell',
            r'\bstock\b': 'stock',
            r'\bbuy\b': 'buy',
        }

        self.tanglish_markers = {
            'pannalama', 'vangalama', 'vangu', 'virka', 'nalla', 'iruka', 'irukka',
            'indha', 'intha', 'epdi', 'enna', 'ipo', 'ippo', 'sariya', 'venuma',
            'la', 'ah', 'anu', 'unga', 'enga', 'kuda', 'stock', 'buy', 'sell'
        }

        self.intent_keywords = {
            'price': ['price', 'rate', 'current', 'today', 'vilai', 'daam', 'kimat'],
            'buy_sell': ['buy', 'sell', 'hold', 'vangu', 'virka', 'kharid', 'bech'],
            'recommend': ['recommend', 'suggest', 'opinion', 'advice', 'salah'],
            'prediction': ['predict', 'forecast', 'target', 'future', 'bhavishya'],
            'portfolio': ['portfolio', 'allocation', 'diversify', 'mix'],
            'risk': ['risk', 'safe', 'volatility', 'jokhim', 'abathu'],
            'greeting': ['hi', 'hello', 'hey', 'vanakkam', 'namaste'],
        }

    def load_model(self):
        """Hosted models do not require local loading."""
        self.is_loaded = True
        return True

    def _make_cache_key(self, model, prompt, params):
        return (model, prompt.strip(), tuple(sorted(params.items())))

    def _cache_get(self, key):
        if key not in self.cache:
            return None
        value = self.cache.pop(key)
        self.cache[key] = value
        return value

    def _cache_set(self, key, value):
        if key in self.cache:
            self.cache.pop(key)
        self.cache[key] = value
        while len(self.cache) > self.cache_size:
            self.cache.popitem(last=False)

    def _hf_inference(self, model, prompt, max_new_tokens=220, temperature=0.4):
        endpoint = f"{self.api_base}/{model}"
        params = {
            'max_new_tokens': max_new_tokens,
            'temperature': temperature,
            'return_full_text': False,
            'do_sample': temperature > 0,
        }
        key = self._make_cache_key(model, prompt, params)
        cached = self._cache_get(key)
        if cached is not None:
            return cached

        headers = {'Content-Type': 'application/json'}
        if self.hf_token:
            headers['Authorization'] = f"Bearer {self.hf_token}"

        payload = {
            'inputs': prompt,
            'parameters': params,
        }

        for attempt in range(3):
            try:
                response = self.session.post(endpoint, headers=headers, json=payload, timeout=self.timeout)
                if response.status_code == 503:
                    time.sleep(1 + attempt)
                    continue
                response.raise_for_status()
                parsed = response.json()
                text = self._extract_generated_text(parsed)
                if text:
                    self._cache_set(key, text)
                    return text
                return None
            except Exception:
                if attempt == 2:
                    return None
                time.sleep(1 + attempt)

        return None

    def _extract_generated_text(self, payload):
        if isinstance(payload, list) and payload:
            first = payload[0]
            if isinstance(first, dict):
                if 'generated_text' in first:
                    return str(first['generated_text']).strip()
                if 'translation_text' in first:
                    return str(first['translation_text']).strip()
                if 'summary_text' in first:
                    return str(first['summary_text']).strip()
        if isinstance(payload, dict):
            if 'generated_text' in payload:
                return str(payload['generated_text']).strip()
            if 'translation_text' in payload:
                return str(payload['translation_text']).strip()
            if 'error' in payload:
                return None
        if isinstance(payload, str):
            return payload.strip()
        return None

    def _normalize(self, text):
        text = (text or '').strip().lower()
        text = re.sub(r'[^a-zA-Z0-9\u0900-\u097F\u0B80-\u0BFF\s]', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()

    def _is_tanglish(self, text):
        normalized = self._normalize(text)
        if not normalized:
            return False

        if re.search(r'[\u0B80-\u0BFF]', normalized):
            return False

        tokens = normalized.split()
        marker_hits = sum(1 for token in tokens if token in self.tanglish_markers)
        return marker_hits >= 2

    def detect_language(self, text, preferred_language=None):
        if preferred_language and preferred_language in self.language_names:
            return preferred_language

        if re.search(r'[\u0B80-\u0BFF]', text or ''):
            return 'ta'
        if re.search(r'[\u0900-\u097F]', text or ''):
            return 'hi'
        if self._is_tanglish(text or ''):
            return 'tanglish'
        return 'en'

    def _normalize_tanglish(self, text):
        normalized = self._normalize(text)
        for pattern, replacement in self.tanglish_patterns.items():
            normalized = re.sub(pattern, replacement, normalized)
        return re.sub(r'\s+', ' ', normalized).strip()

    def translate_to_english(self, text, source_language):
        if source_language in ('en', 'tanglish'):
            if source_language == 'tanglish':
                return self._normalize_tanglish(text)
            return text

        src_name = self.language_names.get(source_language, 'English')
        prompt = (
            f"Translate from {src_name} to English. "
            f"Only return translated text.\n"
            f"Text: {text}\n"
            "Translation:"
        )
        translated = self._hf_inference(self.translation_model, prompt, max_new_tokens=220, temperature=0.0)
        return translated or text

    def _rewrite_to_tanglish(self, text):
        prompt = (
            "Rewrite the following in Tanglish (Tamil using English letters mixed with simple English finance words). "
            "Keep it short and friendly.\n"
            f"Text: {text}\n"
            "Tanglish:"
        )
        rewritten = self._hf_inference(self.translation_model, prompt, max_new_tokens=220, temperature=0.1)
        if rewritten:
            return rewritten

        fallback = text
        fallback = fallback.replace('You can', 'Neenga')
        fallback = fallback.replace('should buy', 'buy pannalaam')
        fallback = fallback.replace('should sell', 'sell pannalaam')
        fallback = fallback.replace('risk', 'risk')
        return fallback

    def _translate_from_english(self, text, target_language):
        if target_language == 'en':
            return text
        if target_language == 'tanglish':
            return self._rewrite_to_tanglish(text)

        target_name = self.language_names.get(target_language, 'English')
        prompt = (
            f"Translate from English to {target_name}. "
            "Only return translated text.\n"
            f"Text: {text}\n"
            "Translation:"
        )
        translated = self._hf_inference(self.translation_model, prompt, max_new_tokens=220, temperature=0.0)
        return translated or text

    def _detect_intent(self, query):
        normalized = self._normalize(query)
        scores = {}
        for intent, keywords in self.intent_keywords.items():
            score = sum(1 for word in keywords if word in normalized)
            if score:
                scores[intent] = score
        if not scores:
            return 'default'
        return max(scores, key=scores.get)

    def _build_market_context(self, stock_data, recommendation, prediction_data):
        live = (stock_data or {}).get('live', {})
        rec = recommendation or {}
        technical = rec.get('signals', {}).get('technical', {})
        trend = rec.get('signals', {}).get('trend', {})

        lines = [
            f"Symbol: {live.get('symbol', 'N/A')}",
            f"Company: {live.get('name', 'N/A')}",
            f"Current Price: Rs {live.get('price', 0)}",
            f"Day Change: {live.get('change_percent', 0)}%",
            f"Recommendation: {rec.get('recommendation', 'N/A')}",
            f"Confidence Score: {rec.get('score', 0)}/100",
            f"Recommendation Summary: {rec.get('summary', 'N/A')}",
            f"RSI: {technical.get('indicators', {}).get('RSI', 'N/A')}",
            f"Trend Direction: {trend.get('trend', {}).get('direction', 'N/A')}",
        ]

        if prediction_data:
            lines.extend([
                f"Predicted Next Price: Rs {prediction_data.get('predicted_price', 0)}",
                f"Predicted Change: {prediction_data.get('change_percent', 0)}%",
            ])

        top_signals = technical.get('signals', [])[:3]
        if top_signals:
            lines.append('Top Technical Signals:')
            lines.extend([f"- {item}" for item in top_signals])

        return '\n'.join(lines)

    def _fast_response(self, intent, stock_data, recommendation, prediction_data):
        live = (stock_data or {}).get('live', {})
        rec = recommendation or {}

        if intent == 'greeting':
            return "Hello. I can help with stock analysis, risk, prediction, and portfolio questions."

        if intent == 'price':
            return (
                f"{live.get('symbol', 'This stock')} is trading near Rs {live.get('price', 0)} "
                f"with a day change of {live.get('change_percent', 0)}%."
            )

        if intent in ('buy_sell', 'recommend'):
            return (
                f"Current signal is {rec.get('recommendation', 'HOLD')} "
                f"with confidence {rec.get('score', 0)}/100. "
                f"Reason: {rec.get('summary', 'signals are mixed right now.')}"
            )

        if intent == 'risk':
            score = rec.get('score', 50)
            if score >= 65:
                return "Risk is moderate but acceptable for staggered buying. Use stop-loss and position sizing."
            if score <= 40:
                return "Risk is high right now. Better to wait or take very small exposure with strict stop-loss."
            return "Risk is balanced. A gradual approach and diversification are safer than one-shot entry."

        if intent == 'prediction':
            if prediction_data:
                return (
                    f"Model expects next move around {prediction_data.get('change_percent', 0)}% "
                    f"with estimated price near Rs {prediction_data.get('predicted_price', 0)}. "
                    "Treat this as probabilistic guidance, not certainty."
                )
            return "Prediction data is limited now, so rely more on trend and risk controls."

        if intent == 'portfolio':
            return "A strong portfolio spreads capital across sectors, avoids over-concentration, and aligns with your risk tolerance."

        return None

    def _chat_prompt(self, question_en, context):
        return (
            "You are a friendly stock market assistant. "
            "Answer in plain language for retail investors. "
            "Give practical reasoning, include risks, and never promise guaranteed returns.\n\n"
            "Use this market context:\n"
            f"{context}\n\n"
            f"User Question: {question_en}\n\n"
            "Reply format:\n"
            "1) Direct answer\n"
            "2) Why (2-3 points)\n"
            "3) Risk note\n"
            "4) Optional next step\n"
            "Answer:"
        )

    def generate_analysis(self, stock_data, recommendation, technical_signals):
        context = self._build_market_context(stock_data, recommendation, None)
        prompt = (
            "You are a stock analyst. Write a concise analysis with sections: "
            "market position, technical view, risk, recommendation.\n\n"
            f"{context}\n"
            f"Extra technical signals: {technical_signals}\n\n"
            "Analysis:"
        )
        response = self._hf_inference(self.chat_model, prompt, max_new_tokens=420, temperature=0.3)
        if response:
            return response
        return self._generate_rule_based_analysis(stock_data, recommendation, technical_signals)

    def _generate_rule_based_analysis(self, stock_data, recommendation, technical_signals):
        live = (stock_data or {}).get('live', {})
        rec = recommendation or {}

        return (
            f"{live.get('symbol', 'Stock')} is near Rs {live.get('price', 0)} with daily move "
            f"{live.get('change_percent', 0)}%. "
            f"Current recommendation is {rec.get('recommendation', 'HOLD')} "
            f"({rec.get('score', 0)}/100). "
            f"Key technical notes: {technical_signals.get('signals', [])[:3] if isinstance(technical_signals, dict) else technical_signals}. "
            "Use staggered entries, stop-loss, and diversification."
        )

    def generate_chatbot_response(self, user_query, stock_data, recommendation, prediction_data=None, preferred_language=None):
        language = self.detect_language(user_query, preferred_language)

        english_query = self.translate_to_english(user_query, language)
        intent = self._detect_intent(english_query)

        fast = self._fast_response(intent, stock_data, recommendation, prediction_data)
        if fast:
            response_text = self._translate_from_english(fast, language)
            return {'response': response_text, 'language': language, 'detected_intent': intent}

        context = self._build_market_context(stock_data, recommendation, prediction_data)
        prompt = self._chat_prompt(english_query, context)

        answer_en = self._hf_inference(self.chat_model, prompt, max_new_tokens=260, temperature=0.35)
        if not answer_en:
            answer_en = self._generate_rule_based_chatbot_response(
                english_query,
                stock_data,
                recommendation,
                prediction_data,
            )

        final_answer = self._translate_from_english(answer_en, language)
        return {'response': final_answer, 'language': language, 'detected_intent': intent}

    def _generate_rule_based_chatbot_response(self, user_query, stock_data, recommendation, prediction_data):
        _ = user_query
        live = (stock_data or {}).get('live', {})
        rec = recommendation or {}

        base = (
            f"For {live.get('symbol', 'this stock')}, the current call is {rec.get('recommendation', 'HOLD')} "
            f"with confidence {rec.get('score', 0)}/100. "
            f"Current price is around Rs {live.get('price', 0)}. "
        )

        if prediction_data:
            base += (
                f"Prediction suggests next move near {prediction_data.get('change_percent', 0)}% "
                f"towards Rs {prediction_data.get('predicted_price', 0)}. "
            )

        base += "Keep risk controls: staggered entries, stop-loss, and diversified allocation."
        return base


llm_analyzer = LLMAnalyzer()


def analyze_stock(stock_data, recommendation, technical_signals):
    return llm_analyzer.generate_analysis(stock_data, recommendation, technical_signals)


def chat_response(user_query, stock_data, recommendation, prediction_data=None, preferred_language=None):
    return llm_analyzer.generate_chatbot_response(
        user_query,
        stock_data,
        recommendation,
        prediction_data,
        preferred_language,
    )
