"""
Hugging Face LLM Stock Analyzer
Generates natural language explanations using open-source LLMs
"""

from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from config import Config
import json
import re


class LLMAnalyzer:
    
    def __init__(self):
        self.model_name = Config.HF_MODEL
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self.is_loaded = False
        self.language_names = {
            'en': 'English',
            'hi': 'Hindi',
            'ta': 'Tamil',
            'te': 'Telugu',
            'ml': 'Malayalam',
            'kn': 'Kannada',
        }
        self.language_hints = {
            'hi': ['kya', 'kitna', 'khareed', 'bech', 'nivesh', 'salah', 'surakshit', 'bhavishya'],
            'ta': ['enna', 'epdi', 'vangu', 'virka', 'mudaleedu', 'abathu', 'padhukappu', 'vilai'],
            'te': ['emi', 'ela', 'konali', 'ammali', 'pettubadi', 'risk', 'dhara', 'salahaa'],
            'ml': ['entha', 'engane', 'vangano', 'vilkano', 'nikshepam', 'apadam', 'vila'],
            'kn': ['enu', 'hegide', 'kolli', 'marata', 'hoodike', 'apayada', 'bele'],
        }
        self.intent_keywords = {
            'price': {
                'en': ['price', 'cost', 'current value', 'today price', 'rate'],
                'hi': ['price', 'daam', 'kimat', 'bhav'],
                'ta': ['price', 'vilai', 'rate'],
                'te': ['price', 'dhara', 'retu'],
                'ml': ['price', 'vila', 'rate'],
                'kn': ['price', 'bele', 'rate'],
            },
            'buy_sell': {
                'en': ['buy', 'sell', 'invest', 'entry', 'exit'],
                'hi': ['kharid', 'khareed', 'bech', 'nivesh', 'entry'],
                'ta': ['buy', 'sell', 'vangu', 'virka', 'mudaleedu'],
                'te': ['buy', 'sell', 'konali', 'ammali', 'pettubadi'],
                'ml': ['buy', 'sell', 'vanguka', 'vilkkuka', 'nikshepam'],
                'kn': ['buy', 'sell', 'kolli', 'mara', 'hoodike'],
            },
            'recommend': {
                'en': ['recommend', 'suggest', 'advice', 'opinion'],
                'hi': ['salah', 'recommend', 'sujhav', 'raay'],
                'ta': ['sollu', 'recommend', 'suggest', 'arivurai'],
                'te': ['salahaa', 'recommend', 'suggest', 'abhiprayam'],
                'ml': ['abhiprayam', 'recommend', 'suggest', 'nirdesham'],
                'kn': ['salahhe', 'recommend', 'suggest', 'abhipraya'],
            },
            'risk': {
                'en': ['risk', 'safe', 'safety', 'volatile'],
                'hi': ['risk', 'surakshit', 'safe', 'jokhim'],
                'ta': ['risk', 'safe', 'padhukappu', 'abathu'],
                'te': ['risk', 'safe', 'suraksha', 'pramadam'],
                'ml': ['risk', 'safe', 'suraksha', 'apadam'],
                'kn': ['risk', 'safe', 'surakshita', 'apayada'],
            },
            'target': {
                'en': ['target', 'future', 'prediction', 'forecast'],
                'hi': ['target', 'future', 'prediction', 'bhavishya'],
                'ta': ['target', 'future', 'prediction', 'ethirkaalam'],
                'te': ['target', 'future', 'prediction', 'bhavishyat'],
                'ml': ['target', 'future', 'prediction', 'bhavi'],
                'kn': ['target', 'future', 'prediction', 'bhavishya'],
            },
        }    
    def load_model(self):
        """Load Hugging Face model"""
        if self.is_loaded:
            return True
        
        try:
            print(f"Loading model: {self.model_name}...")
            
            # Determine device
            device = 0 if torch.cuda.is_available() else -1
            
            # Load model using pipeline for efficiency
            self.pipeline = pipeline(
                "text-generation",
                model=self.model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None,
                max_length=1024,
                token=Config.HF_TOKEN if Config.HF_TOKEN else None
            )
            
            self.is_loaded = True
            print("Model loaded successfully!")
            return True
            
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            print("Falling back to rule-based analysis...")
            return False
    
    def generate_analysis(self, stock_data, recommendation, technical_signals):
        """Generate comprehensive stock analysis"""
        
        if not self.is_loaded:
            # Fallback to rule-based analysis
            return self._generate_rule_based_analysis(stock_data, recommendation, technical_signals)
        
        # Prepare prompt
        prompt = self._create_analysis_prompt(stock_data, recommendation, technical_signals)
        
        try:
            # Generate response
            response = self.pipeline(
                prompt,
                max_new_tokens=500,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                num_return_sequences=1
            )
            
            # Extract generated text
            generated_text = response[0]['generated_text']
            
            # Remove prompt from response
            analysis = generated_text.replace(prompt, '').strip()
            
            return analysis
            
        except Exception as e:
            print(f"Error generating LLM analysis: {str(e)}")
            return self._generate_rule_based_analysis(stock_data, recommendation, technical_signals)
    
    def _create_analysis_prompt(self, stock_data, recommendation, technical_signals):
        """Create prompt for LLM"""
        
        live_data = stock_data.get('live', {})
        
        prompt = f"""You are a professional stock market analyst. Analyze the following stock and provide investment advice.

Stock: {live_data.get('symbol', 'N/A')}
Company: {live_data.get('name', 'N/A')}

Current Market Data:
- Current Price: Ã¢â€šÂ¹{live_data.get('price', 0)}
- Day Change: {live_data.get('change_percent', 0)}%
- Volume: {live_data.get('volume', 0):,}
- 52-Week High: Ã¢â€šÂ¹{live_data.get('week_52_high', 0)}
- 52-Week Low: Ã¢â€šÂ¹{live_data.get('week_52_low', 0)}

Technical Analysis:
- Recommendation: {recommendation.get('recommendation', 'N/A')}
- Confidence Score: {recommendation.get('score', 0)}/100
- RSI: {technical_signals.get('indicators', {}).get('RSI', 'N/A')}
- MACD Status: {"Bullish" if technical_signals.get('indicators', {}).get('MACD', 0) > 0 else "Bearish"}

Key Signals:
{chr(10).join('- ' + s for s in technical_signals.get('signals', [])[:3])}

Provide a clear, concise analysis explaining:
1. Current market position
2. Technical indicator interpretation
3. Risk factors
4. Investment recommendation with reasoning

Analysis:"""

        return prompt
    
    def _generate_rule_based_analysis(self, stock_data, recommendation, technical_signals):
        """Generate analysis using rules (fallback)"""
        
        live_data = stock_data.get('live', {})
        rec_data = recommendation
        tech_data = technical_signals
        
        symbol = live_data.get('symbol', 'Stock')
        price = live_data.get('price', 0)
        change_pct = live_data.get('change_percent', 0)
        rec_type = rec_data.get('recommendation', 'HOLD')
        score = rec_data.get('score', 50)
        
        # Build analysis
        analysis = f"**{symbol} Stock Analysis**\n\n"
        
        # Market Position
        analysis += f"**Current Market Position:**\n"
        analysis += f"The stock is currently trading at Ã¢â€šÂ¹{price:.2f}, "
        
        if change_pct > 0:
            analysis += f"up {change_pct:.2f}% today, showing positive momentum. "
        elif change_pct < 0:
            analysis += f"down {abs(change_pct):.2f}% today, experiencing selling pressure. "
        else:
            analysis += f"flat for the day, indicating consolidation. "
        
        # Technical Analysis
        analysis += f"\n\n**Technical Indicator Analysis:**\n"
        
        rsi = tech_data.get('indicators', {}).get('RSI', 50)
        if rsi > 70:
            analysis += f"RSI at {rsi:.2f} indicates overbought conditions, suggesting potential reversal. "
        elif rsi < 30:
            analysis += f"RSI at {rsi:.2f} indicates oversold conditions, presenting a potential buying opportunity. "
        else:
            analysis += f"RSI at {rsi:.2f} is in neutral territory, indicating balanced momentum. "
        
        # Add key signals
        if tech_data.get('signals'):
            analysis += f"\n\nKey technical signals observed:\n"
            for signal in tech_data['signals'][:3]:
                analysis += f"Ã¢â‚¬Â¢ {signal}\n"
        
        # Recommendation
        analysis += f"\n\n**Investment Recommendation:**\n"
        analysis += f"Based on comprehensive analysis, our recommendation is **{rec_type}** "
        analysis += f"with a confidence score of {score}/100. "
        
        if rec_type in ['STRONG BUY', 'BUY']:
            analysis += "The technical indicators and price action suggest upward momentum. "
            analysis += "Consider accumulating positions with proper risk management. "
        elif rec_type == 'HOLD':
            analysis += "The current signals are mixed, suggesting a wait-and-watch approach. "
            analysis += "Monitor key support and resistance levels before taking action. "
        else:
            analysis += "Multiple bearish signals suggest caution. "
            analysis += "Consider reducing exposure or waiting for better entry points. "
        
        # Risk Factors
        analysis += f"\n\n**Risk Factors:**\n"
        analysis += "Ã¢â‚¬Â¢ Market volatility can impact short-term prices\n"
        analysis += "Ã¢â‚¬Â¢ Technical indicators are based on historical patterns\n"
        analysis += "Ã¢â‚¬Â¢ Always use stop-loss orders to manage risk\n"
        analysis += "Ã¢â‚¬Â¢ Diversification is key to portfolio management\n"
        
        analysis += "\n\n*Disclaimer: This analysis is for educational purposes only. "
        analysis += "Please consult with a financial advisor before making investment decisions.*"
        
        return analysis
    
    def detect_language(self, text, preferred_language=None):
        """Detect language from user text or use preferred override."""
        if preferred_language and preferred_language in self.language_names:
            return preferred_language

        if re.search(r'[\u0B80-\u0BFF]', text):
            return 'ta'
        if re.search(r'[\u0900-\u097F]', text):
            return 'hi'
        if re.search(r'[\u0C00-\u0C7F]', text):
            return 'te'
        if re.search(r'[\u0D00-\u0D7F]', text):
            return 'ml'
        if re.search(r'[\u0C80-\u0CFF]', text):
            return 'kn'

        normalized = self._normalize_query(text)
        scores = {}
        for lang, hints in self.language_hints.items():
            score = sum(1 for token in hints if token in normalized)
            if score:
                scores[lang] = score

        if scores:
            return max(scores, key=scores.get)
        return 'en'

    def _normalize_query(self, text):
        """Normalize user text for keyword-based NLP intent matching."""
        normalized = text.lower().strip()
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized

    def _detect_intent(self, user_query, language):
        """Detect user intent from multilingual keywords and transliterated text."""
        query = self._normalize_query(user_query)

        intent_scores = {}
        for intent, lang_keywords in self.intent_keywords.items():
            keywords = lang_keywords.get(language, []) + lang_keywords.get('en', [])
            score = sum(1 for token in keywords if token in query)
            if score:
                intent_scores[intent] = score

        if not intent_scores:
            return 'default'

        return max(intent_scores, key=intent_scores.get)

    def _localized_message(self, language, key, **kwargs):
        """Return localized fallback messages for rule-based chatbot responses."""
        templates = {
            'en': {
                'price': "The current price of {symbol} is Rs {price:.2f}, {change:.2f}% from previous close.",
                'buy_sell': "Our recommendation for {symbol} is {recommendation} with a confidence score of {score}/100. {summary}",
                'recommend': "Based on technical analysis, we recommend {recommendation} for {symbol}. This is based on RSI, MACD, and trend indicators.",
                'risk_high': "The current technical indicators suggest moderate to low risk for buying, but all investments carry market risk.",
                'risk_low': "The technical indicators suggest higher risk right now. Consider waiting for better entry points and using strict stop-loss orders.",
                'risk_mid': "The current risk level is moderate. Diversification and proper position sizing are recommended.",
                'target': "Our ML model provides short-term predictions. Monitor key support and resistance levels for {symbol}.",
                'default': "I can help you with analysis of {symbol}. Ask about current price, buy/sell recommendation, technical indicators, or risk.",
            },
            'hi': {
                'price': "{symbol} ka current price Rs {price:.2f} hai, jo previous close se {change:.2f}% badla hai.",
                'buy_sell': "{symbol} ke liye hamari recommendation {recommendation} hai, confidence score {score}/100. {summary}",
                'recommend': "Technical analysis ke basis par {symbol} ke liye recommendation {recommendation} hai. Isme RSI, MACD aur trend indicators use kiye gaye hain.",
                'risk_high': "Current technical indicators ke hisab se risk moderate se low hai, lekin market risk hamesha hota hai.",
                'risk_low': "Current indicators higher risk dikhate hain. Better entry ka wait karein aur strict stop-loss use karein.",
                'risk_mid': "Risk level abhi moderate hai. Diversification aur proper position sizing follow karein.",
                'target': "Hamari ML model short-term prediction deti hai. {symbol} ke key support aur resistance levels monitor karein.",
                'default': "Main {symbol} ke analysis mein help kar sakta hoon. Aap price, buy/sell recommendation, indicators, ya risk ke baare mein puch sakte hain.",
            },
            'ta': {
                'price': "{symbol} in tharpothaiya vilai Rs {price:.2f}. Idhu previous close-ai vida {change:.2f}% maatram.",
                'buy_sell': "{symbol} kkaana engal recommendation {recommendation}. Confidence score {score}/100. {summary}",
                'recommend': "Technical analysis adipadaiyil {symbol} kku {recommendation} recommendation. RSI, MACD matrum trend indicators payanpaduthappattullana.",
                'risk_high': "Tharpothaiya technical indicators padi risk moderate to low. Aana market risk eppothum irukkum.",
                'risk_low': "Tharpothu indicators adhiga risk kaattugiradhu. Better entry varum varai kaathirundhu strict stop-loss payanpadungal.",
                'risk_mid': "Risk level ippodhu moderate. Diversification matrum proper position sizing parinduraikkapadugiradhu.",
                'target': "{symbol} kkaana short-term prediction-ku key support and resistance levels-ai gavaniyungal.",
                'default': "{symbol} patriya analysis-il naan help panna mudiyum. Price, buy/sell recommendation, indicators, risk patri kelungal.",
            },
            'te': {
                'price': "{symbol} current dhara Rs {price:.2f}, previous close nundi {change:.2f}% marindi.",
                'buy_sell': "{symbol} kosam maa recommendation {recommendation}, confidence score {score}/100. {summary}",
                'recommend': "{symbol} pai technical analysis base chesi recommendation {recommendation}.",
                'risk_high': "Current technical indicators prakaram risk moderate to low undi, kani market risk untundi.",
                'risk_low': "Current indicators high risk chupisthunnayi. Better entry kosam wait cheyyandi.",
                'risk_mid': "Ippudu risk level moderate. Diversification mariyu position sizing follow cheyyandi.",
                'target': "{symbol} kosam key support mariyu resistance levels monitor cheyyandi.",
                'default': "{symbol} gurinchi analysis lo nenu help chestha. Price, recommendation, risk leka prediction adagandi.",
            },
            'ml': {
                'price': "{symbol} current vila Rs {price:.2f}, previous close il ninnum {change:.2f}% maariyittundu.",
                'buy_sell': "{symbol} inu nammade recommendation {recommendation}, confidence score {score}/100. {summary}",
                'recommend': "{symbol} inu technical analysis adisthanamayi recommendation {recommendation}.",
                'risk_high': "Current technical indicators prakaram risk moderate to low aanu, pakshe market risk undu.",
                'risk_low': "Current indicators high risk kaanikkunnu. Better entry point varunnath vare wait cheyyuka.",
                'risk_mid': "Risk level ippo moderate aanu. Diversificationum proper position sizingum nallathu.",
                'target': "{symbol} inu key support-resistance levels monitor cheyyuka.",
                'default': "{symbol} analysis il njan sahayikkam. Price, recommendation, risk, prediction ivaye kurich chodikku.",
            },
            'kn': {
                'price': "{symbol} current bele Rs {price:.2f}, previous close inda {change:.2f}% badalide.",
                'buy_sell': "{symbol} ge namma recommendation {recommendation}, confidence score {score}/100. {summary}",
                'recommend': "{symbol} mele technical analysis adharadalli recommendation {recommendation}.",
                'risk_high': "Current technical indicators prakara risk moderate to low ide, adre market risk ide.",
                'risk_low': "Current indicators high risk torisuttive. Better entry ge swalpa kaayiri.",
                'risk_mid': "Iga risk level moderate ide. Diversification mattu proper position sizing madi.",
                'target': "{symbol} ge key support mattu resistance levels monitor madi.",
                'default': "{symbol} analysis ge nanu sahaya madabahudu. Price, recommendation, risk athava prediction keli.",
            },
        }

        lang_templates = templates.get(language, templates['en'])
        template = lang_templates.get(key, templates['en']['default'])
        return template.format(**kwargs)

    def generate_chatbot_response(self, user_query, stock_data, recommendation, preferred_language=None):
        """Generate chatbot response to user questions"""
        language = self.detect_language(user_query, preferred_language)

        if not self.is_loaded:
            response_text = self._generate_rule_based_chatbot_response(
                user_query,
                stock_data,
                recommendation,
                language
            )
            return {'response': response_text, 'language': language}

        # Create conversational prompt
        live_data = stock_data.get('live', {})

        prompt = f"""You are a helpful stock market assistant. Answer the user's question based on the following data.
Respond in {self.language_names.get(language, 'English')}.
Keep the response clear and practical.

Stock: {live_data.get('symbol', 'N/A')}
Current Price: Rs {live_data.get('price', 0)}
Recommendation: {recommendation.get('recommendation', 'N/A')}

User Question: {user_query}

Answer:"""

        try:
            response = self.pipeline(
                prompt,
                max_new_tokens=200,
                temperature=0.7,
                do_sample=True
            )

            answer = response[0]['generated_text'].replace(prompt, '').strip()
            return {'response': answer, 'language': language}

        except Exception as e:
            print(f"Error generating chatbot response: {str(e)}")
            response_text = self._generate_rule_based_chatbot_response(
                user_query,
                stock_data,
                recommendation,
                language
            )
            return {'response': response_text, 'language': language}

    def _generate_rule_based_chatbot_response(self, user_query, stock_data, recommendation, language='en'):
        """Generate rule-based chatbot response"""

        live_data = stock_data.get('live', {})
        rec_data = recommendation
        intent = self._detect_intent(user_query, language)

        if intent == 'price':
            return self._localized_message(
                language,
                'price',
                symbol=live_data.get('symbol'),
                price=live_data.get('price', 0),
                change=live_data.get('change_percent', 0),
            )

        if intent == 'buy_sell':
            return self._localized_message(
                language,
                'buy_sell',
                symbol=live_data.get('symbol'),
                recommendation=rec_data.get('recommendation'),
                score=rec_data.get('score'),
                summary=rec_data.get('summary', ''),
            )

        if intent == 'recommend':
            return self._localized_message(
                language,
                'recommend',
                symbol=live_data.get('symbol'),
                recommendation=rec_data.get('recommendation'),
            )

        if intent == 'risk':
            score = rec_data.get('score', 50)
            if score > 60:
                return self._localized_message(language, 'risk_high')
            elif score < 40:
                return self._localized_message(language, 'risk_low')
            else:
                return self._localized_message(language, 'risk_mid')

        if intent == 'target':
            return self._localized_message(language, 'target', symbol=live_data.get('symbol'))

        return self._localized_message(language, 'default', symbol=live_data.get('symbol'))


# Global instance
llm_analyzer = LLMAnalyzer()


def analyze_stock(stock_data, recommendation, technical_signals):
    """Quick function to analyze stock"""
    return llm_analyzer.generate_analysis(stock_data, recommendation, technical_signals)


def chat_response(user_query, stock_data, recommendation, preferred_language=None):
    """Quick function for chatbot response"""
    return llm_analyzer.generate_chatbot_response(user_query, stock_data, recommendation, preferred_language)





