import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in .env file")

# Database Configuration
DB_PATH = os.getenv('DB_PATH', 'launchbot.db')

# Alert Configuration
ALERT_INTERVAL_HOURS = int(os.getenv('ALERT_INTERVAL_HOURS', '2'))
ALERT_RISK_THRESHOLD = int(os.getenv('ALERT_RISK_THRESHOLD', '70'))

# Portfolio Configuration
PORTFOLIO_UPDATE_INTERVAL_MINUTES = int(os.getenv('PORTFOLIO_UPDATE_INTERVAL_MINUTES', '30'))

# AI Configuration - Hugging Face (replacing OpenAI)
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
HUGGINGFACE_MODEL = os.getenv('HUGGINGFACE_MODEL', 'meta-llama/Llama-2-7b-chat-hf')
USE_LOCAL_MODEL = os.getenv('USE_LOCAL_MODEL', 'true').lower() == 'true'

# Advanced AI Settings
AI_CONFIDENCE_THRESHOLD = float(os.getenv('AI_CONFIDENCE_THRESHOLD', '0.75'))
AI_ENSEMBLE_MODELS = int(os.getenv('AI_ENSEMBLE_MODELS', '3'))  # Use multiple models for better accuracy
AI_TEMPERATURE = float(os.getenv('AI_TEMPERATURE', '0.3'))  # Lower = more focused

# Twitter/X Configuration
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')

# Launch Alert Configuration
LAUNCH_ALERT_DAYS_BEFORE = int(os.getenv('LAUNCH_ALERT_DAYS_BEFORE', '3'))
LAUNCH_CHECK_INTERVAL_HOURS = int(os.getenv('LAUNCH_CHECK_INTERVAL_HOURS', '12'))

# Enhanced Risk Thresholds (More granular)
RISK_THRESHOLDS = {
    'very_low': 4.5,    # 4.5-5.0 = Very Low Risk (Excellent)
    'low': 3.8,         # 3.8-4.4 = Low Risk (Good)
    'medium_low': 3.2,  # 3.2-3.7 = Medium-Low Risk (Acceptable)
    'medium': 2.5,      # 2.5-3.1 = Medium Risk (Neutral)
    'medium_high': 1.8, # 1.8-2.4 = Medium-High Risk (Caution)
    'high': 1.2,        # 1.2-1.7 = High Risk (Risky)
    'very_high': 0.0    # 0.0-1.1 = Very High Risk (Danger)
}

# Advanced Scoring Weights (Fine-tuned for crypto)
SCORING_WEIGHTS = {
    'market_fundamentals': 0.25,
    'technical_indicators': 0.20,
    'on_chain_metrics': 0.20,
    'sentiment_analysis': 0.15,
    'liquidity_analysis': 0.10,
    'community_strength': 0.10
}

# Meme Coin Specific Weights (Higher risk focus)
MEME_COIN_WEIGHTS = {
    'market_fundamentals': 0.15,
    'technical_indicators': 0.15,
    'on_chain_metrics': 0.25,
    'sentiment_analysis': 0.25,
    'liquidity_analysis': 0.15,
    'community_strength': 0.05
}

# Technical Indicators Configuration
TECHNICAL_INDICATORS = {
    'rsi_period': 14,
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    'bollinger_period': 20,
    'bollinger_std': 2,
    'ema_periods': [9, 21, 50, 200],
    'volume_ma_period': 20
}

# On-Chain Metrics Thresholds
ON_CHAIN_THRESHOLDS = {
    'whale_alert_threshold': 1000000,  # $1M+
    'min_liquidity_usd': 100000,       # $100K minimum
    'max_holder_concentration': 0.50,   # Top 10 holders < 50%
    'min_transaction_count_24h': 100,
    'min_unique_holders': 1000
}

# Sentiment Analysis Configuration
SENTIMENT_CONFIG = {
    'twitter_weight': 0.40,
    'reddit_weight': 0.30,
    'telegram_weight': 0.20,
    'news_weight': 0.10,
    'min_mentions_threshold': 10,
    'sentiment_decay_hours': 24
}

# Machine Learning Models Configuration
ML_MODELS = {
    'price_prediction': {
        'enabled': True,
        'model_type': 'lstm',
        'lookback_periods': 60,
        'forecast_periods': 7
    },
    'anomaly_detection': {
        'enabled': True,
        'model_type': 'isolation_forest',
        'contamination': 0.1
    },
    'pattern_recognition': {
        'enabled': True,
        'patterns': ['head_shoulders', 'double_top', 'bull_flag', 'ascending_triangle']
    }
}

# Weekly Report Configuration
WEEKLY_REPORT_DAY = int(os.getenv('WEEKLY_REPORT_DAY', '0'))  # 0 = Monday
WEEKLY_REPORT_HOUR = int(os.getenv('WEEKLY_REPORT_HOUR', '9'))  # 9 AM UTC
PRICE_DROP_ALERT_THRESHOLD = float(os.getenv('PRICE_DROP_ALERT_THRESHOLD', '-10.0'))  # -10%

# Advanced Alert Configuration
ADVANCED_ALERTS = {
    'whale_movement': True,
    'unusual_volume': True,
    'price_breakout': True,
    'sentiment_spike': True,
    'liquidity_warning': True,
    'rug_pull_detection': True
}

# Free Features (No more payment plans)
FREE_FEATURES = [
    '✅ Unlimited crypto watchlist',
    '✅ Advanced AI-powered risk analysis',
    '✅ Real-time meme coin tracking',
    '✅ Smart alerts & notifications',
    '✅ Launch event monitoring',
    '✅ Unlimited portfolio tracking',
    '✅ Advanced analytics & charts',
    '✅ ML-powered price predictions',
    '✅ On-chain metrics analysis',
    '✅ Whale movement tracking',
    '✅ Rug pull detection',
    '✅ Community-driven insights'
]

# Cache Configuration
CACHE_CONFIG = {
    'enabled': True,
    'ttl_seconds': 300,  # 5 minutes
    'max_size': 1000
}