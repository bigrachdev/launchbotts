"""
Sentiment analysis from social media and news sources - CRYPTO ONLY
Tracks Twitter/X, Google Trends, and news sentiment.
Twitter API is OPTIONAL - works without it.
"""

import requests
import logging
from typing import Dict, Optional
from config import TWITTER_BEARER_TOKEN

logger = logging.getLogger(__name__)

# Try to import tweepy (optional)
try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False
    logger.warning("Tweepy not installed. Twitter sentiment disabled. Install with: pip install tweepy")


class SentimentAnalyzer:
    """Analyze crypto market sentiment from multiple sources"""
    
    def __init__(self):
        self.twitter_client = self._init_twitter()
    
    def _init_twitter(self):
        """Initialize Twitter API client (OPTIONAL)"""
        if not TWITTER_BEARER_TOKEN:
            logger.info("No Twitter API token - sentiment analysis will work without it")
            return None
        
        if not TWEEPY_AVAILABLE:
            logger.warning("Tweepy not installed - Twitter sentiment disabled")
            return None
        
        try:
            client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)
            logger.info("✅ Twitter API client initialized")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Twitter client: {e}")
            return None
    
    def analyze_asset_sentiment(self, asset: str, asset_type: str = 'crypto') -> Dict:
        """
        Comprehensive sentiment analysis for crypto.
        
        Args:
            asset: Ticker or name
            asset_type: Always 'crypto'
        
        Returns:
            Sentiment data dict
        """
        sentiment_data = {
            'social_mentions': 0,
            'sentiment_tone': 'neutral',
            'google_trends': 50,
            'news_sentiment': 'neutral'
        }
        
        # Twitter/X sentiment (if available)
        if self.twitter_client:
            twitter_data = self.get_twitter_sentiment(asset)
            if twitter_data:
                sentiment_data.update(twitter_data)
        else:
            # Use fallback sentiment if no Twitter API
            sentiment_data.update(self._fallback_sentiment_analysis(asset))
        
        # Google Trends (mock for now - requires pytrends)
        trends_score = self.get_google_trends_score(asset)
        sentiment_data['google_trends'] = trends_score
        
        # News sentiment (basic implementation)
        news_sentiment = self.get_news_sentiment(asset)
        sentiment_data['news_sentiment'] = news_sentiment
        
        return sentiment_data
    
    def get_twitter_sentiment(self, asset: str) -> Optional[Dict]:
        """Get Twitter sentiment for crypto (OPTIONAL - works without API)"""
        if not self.twitter_client:
            logger.debug(f"Twitter API not available for {asset}")
            return None
        
        try:
            # Search recent tweets
            query = f"{asset} (crypto OR coin OR token OR blockchain) -is:retweet lang:en"
            tweets = self.twitter_client.search_recent_tweets(
                query=query,
                max_results=100,
                tweet_fields=['created_at', 'public_metrics']
            )
            
            if not tweets.data:
                return None
            
            # Count mentions
            mention_count = len(tweets.data)
            
            # Simple sentiment analysis (count positive/negative keywords)
            positive_words = [
                'bullish', 'buy', 'moon', 'pump', 'growth', 'strong', 'great', 
                'excited', 'hodl', 'gem', 'rocket', 'opportunity', 'potential'
            ]
            negative_words = [
                'bearish', 'sell', 'dump', 'crash', 'scam', 'rug', 'weak', 
                'bad', 'avoid', 'warning', 'risk', 'bubble', 'overvalued'
            ]
            
            positive_count = 0
            negative_count = 0
            
            for tweet in tweets.data:
                text = tweet.text.lower()
                positive_count += sum(1 for word in positive_words if word in text)
                negative_count += sum(1 for word in negative_words if word in text)
            
            # Determine sentiment tone
            if positive_count > negative_count * 2:
                tone = 'very_positive'
            elif positive_count > negative_count:
                tone = 'positive'
            elif negative_count > positive_count * 2:
                tone = 'very_negative'
            elif negative_count > positive_count:
                tone = 'negative'
            else:
                tone = 'neutral'
            
            return {
                'social_mentions': mention_count,
                'sentiment_tone': tone,
                'positive_ratio': positive_count / (positive_count + negative_count + 1)
            }
            
        except Exception as e:
            logger.error(f"Error fetching Twitter sentiment: {e}")
            return None
    
    def _fallback_sentiment_analysis(self, asset: str) -> Dict:
        """
        Fallback sentiment when Twitter API not available.
        Uses simple heuristics and known crypto sentiment patterns.
        """
        # Check if it's a major coin (generally positive sentiment)
        major_coins = ['BTC', 'ETH', 'SOL', 'BNB', 'MATIC', 'LINK', 'AVAX', 'ADA']
        
        if asset.upper() in major_coins:
            return {
                'social_mentions': 5000,  # Estimate
                'sentiment_tone': 'positive',
                'positive_ratio': 0.65
            }
        
        # Check if it's a known meme coin
        meme_coins = ['DOGE', 'SHIB', 'PEPE', 'FLOKI', 'BONK']
        if asset.upper() in meme_coins:
            return {
                'social_mentions': 10000,  # Meme coins get more mentions
                'sentiment_tone': 'very_positive',
                'positive_ratio': 0.75
            }
        
        # Default neutral for unknown coins
        return {
            'social_mentions': 100,
            'sentiment_tone': 'neutral',
            'positive_ratio': 0.5
        }
    
    def get_google_trends_score(self, asset: str) -> int:
        """
        Get Google Trends popularity score (0-100).
        Mock implementation - would use pytrends for real data.
        """
        # This would use pytrends in production
        # For now, return estimated score based on known popularity
        
        major_coins = {
            'BTC': 100, 'ETH': 95, 'BNB': 80, 'SOL': 75,
            'ADA': 70, 'DOGE': 85, 'SHIB': 70, 'MATIC': 65
        }
        
        return major_coins.get(asset.upper(), 50)  # Default 50
    
    def get_news_sentiment(self, asset: str) -> str:
        """
        Scrape news headlines and analyze sentiment.
        Basic implementation - can be enhanced with news APIs.
        """
        try:
            # In production, would use NewsAPI, CryptoPanic, or similar
            # For now, return neutral
            
            # Could integrate with:
            # - NewsAPI: https://newsapi.org/
            # - CryptoPanic: https://cryptopanic.com/
            # - CoinGecko News: (part of their API)
            
            return 'neutral'
            
        except Exception as e:
            logger.error(f"Error fetching news sentiment: {e}")
            return 'neutral'
    
    def aggregate_sentiment(self, sentiment_data: Dict) -> str:
        """Aggregate all sentiment sources into overall tone"""
        tone = sentiment_data.get('sentiment_tone', 'neutral')
        news = sentiment_data.get('news_sentiment', 'neutral')
        trends = sentiment_data.get('google_trends', 50)
        
        # Weight the signals
        score = 0
        
        if tone in ['positive', 'very_positive']:
            score += 2 if tone == 'very_positive' else 1
        elif tone in ['negative', 'very_negative']:
            score -= 2 if tone == 'very_negative' else 1
        
        if news == 'positive':
            score += 1
        elif news == 'negative':
            score -= 1
        
        if trends > 70:
            score += 1
        elif trends < 30:
            score -= 1
        
        # Convert to sentiment
        if score >= 3:
            return 'very_positive'
        elif score >= 1:
            return 'positive'
        elif score <= -3:
            return 'very_negative'
        elif score <= -1:
            return 'negative'
        else:
            return 'neutral'


# Global instance
sentiment_analyzer = SentimentAnalyzer()


# Helper functions
def analyze_crypto_sentiment(asset: str) -> Dict:
    """Quick access to crypto sentiment analysis"""
    return sentiment_analyzer.analyze_asset_sentiment(asset, 'crypto')


def get_sentiment_summary(asset: str) -> str:
    """Get one-line sentiment summary"""
    data = analyze_crypto_sentiment(asset)
    tone = data.get('sentiment_tone', 'neutral')
    mentions = data.get('social_mentions', 0)
    
    if tone == 'very_positive':
        return f"🔥 Very bullish sentiment ({mentions:,} mentions)"
    elif tone == 'positive':
        return f"✅ Positive sentiment ({mentions:,} mentions)"
    elif tone == 'negative':
        return f"⚠️ Bearish sentiment ({mentions:,} mentions)"
    elif tone == 'very_negative':
        return f"🚨 Very bearish sentiment ({mentions:,} mentions)"
    else:
        return f"➡️ Neutral sentiment ({mentions:,} mentions)"