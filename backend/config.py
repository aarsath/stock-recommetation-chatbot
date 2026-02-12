import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'

    # Hugging Face hosted inference settings
    HF_MODEL = os.getenv('HF_MODEL', 'mistralai/Mistral-7B-Instruct-v0.2')
    HF_CHAT_MODEL = os.getenv('HF_CHAT_MODEL', HF_MODEL)
    HF_TRANSLATION_MODEL = os.getenv('HF_TRANSLATION_MODEL', 'google/flan-t5-large')
    HF_TOKEN = os.getenv('HF_TOKEN', '')  # Required for hosted inference
    HF_API_BASE = os.getenv('HF_API_BASE', 'https://api-inference.huggingface.co/models')
    HF_REQUEST_TIMEOUT = int(os.getenv('HF_REQUEST_TIMEOUT', '45'))

    # Data settings
    HISTORICAL_DAYS = 365  # 1 year of historical data
    PREDICTION_DAYS = 30

    # Technical indicators settings
    SMA_PERIODS = [20, 50, 200]
    EMA_PERIODS = [12, 26]
    RSI_PERIOD = 14
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    BB_PERIOD = 20
    BB_STD = 2

    # ML Model settings
    MODEL_PATH = 'ml/models/'
    TRAIN_TEST_SPLIT = 0.8
    RANDOM_STATE = 42

    # Chart settings
    CHART_OUTPUT_DIR = 'static/charts/'
    CHART_DPI = 100
    CHART_FIGSIZE = (14, 10)
