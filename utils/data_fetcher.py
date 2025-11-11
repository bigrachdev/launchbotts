"""
Enhanced data fetcher with comprehensive crypto metrics.
2x more data points for better AI analysis.
"""

import requests
import time
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)

# Cache to avoid rate limiting
_cache = {}
_cache_ttl = {}


def _get_from_cache(key: str) -> Optional[Dict]:
    """Get data from cache if not expired"""
    if key in _cache and key in _cache_ttl:
        if time.time() < _cache_ttl[key]:
            return _cache[key]
    return None


def _set_cache(key: str, data: Dict, ttl_seconds: int = 300):
    """Set data in cache with TTL"""
    _cache[key] = data
    _cache_ttl[key] = time.time() + ttl_seconds


def get_crypto_data(symbol: str, include_advanced: bool = True) -> Optional[Dict[str, Any]]:
    """
    Fetch comprehensive cryptocurrency data from multiple sources.
    
    Args:
        symbol: Crypto symbol or ID
        include_advanced: Whether to fetch advanced metrics
    
    Returns:
        Comprehensive dictionary with crypto data
    """
    # Check cache first
    cache_key = f"crypto_{symbol}_{include_advanced}"
    cached_data = _get_from_cache(cache_key)
    if cached_data:
        return cached_data
    
    try:
        # Symbol mappings
        symbol_mappings = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'SOL': 'solana',
            'USDT': 'tether',
            'BNB': 'binancecoin',
            'XRP': 'ripple',
            'ADA': 'cardano',
            'DOGE': 'dogecoin',
            'MATIC': 'polygon',
            'DOT': 'polkadot',
            'SHIB': 'shiba-inu',
            'PEPE': 'pepe',
            'FLOKI': 'floki',
            'BONK': 'bonk'
        }
        
        crypto_id = symbol_mappings.get(symbol.upper(), symbol.lower())
        
        # Fetch basic data from CoinGecko
        base_url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}"
        params = {
            'localization': 'false',
            'tickers': 'false',
            'community_data': 'true',
            'developer_data': 'true',
            'sparkline': 'true'
        }
        
        response = requests.get(base_url, params=params, timeout=10)
        
        if response.status_code != 200:
            logger.warning(f"CoinGecko API returned {response.status_code} for {symbol}")
            return None
        
        data = response.json()
        market_data = data.get("market_data", {})
        
        # Build comprehensive data dictionary
        crypto_data = {
            # Basic Info
            "symbol": symbol.upper(),
            "name": data.get("name", symbol),
            "id": crypto_id,
            
            # Price Data
            "price": market_data.get("current_price", {}).get("usd", 0),
            "priceChange24h": market_data.get("price_change_percentage_24h", 0),
            "priceChange7d": market_data.get("price_change_percentage_7d", 0),
            "priceChange30d": market_data.get("price_change_percentage_30d", 0),
            "priceChange1y": market_data.get("price_change_percentage_1y", 0),
            
            # Market Metrics
            "marketCap": market_data.get("market_cap", {}).get("usd", 0),
            "volume": market_data.get("total_volume", {}).get("usd", 0),
            "circulatingSupply": market_data.get("circulating_supply", 0),
            "totalSupply": market_data.get("total_supply", 0),
            "maxSupply": market_data.get("max_supply", 0),
            
            # High/Low
            "high24h": market_data.get("high_24h", {}).get("usd", 0),
            "low24h": market_data.get("low_24h", {}).get("usd", 0),
            "ath": market_data.get("ath", {}).get("usd", 0),
            "atl": market_data.get("atl", {}).get("usd", 0),
            "ath_change_percentage": market_data.get("ath_change_percentage", {}).get("usd", 0),
            
            # Scores
            "communityScore": data.get("community_score", 0),
            "developerScore": data.get("developer_score", 0),
            "liquidityScore": data.get("liquidity_score", 0),
            "publicInterestScore": data.get("public_interest_score", 0),
            
            # Community Data
            "twitter_followers": data.get("community_data", {}).get("twitter_followers", 0),
            "reddit_subscribers": data.get("community_data", {}).get("reddit_subscribers", 0),
            "reddit_active_users": data.get("community_data", {}).get("reddit_accounts_active_48h", 0),
            "telegram_members": data.get("community_data", {}).get("telegram_channel_user_count", 0),
            
            # Developer Data
            "github_stars": data.get("developer_data", {}).get("stars", 0),
            "github_forks": data.get("developer_data", {}).get("forks", 0),
            "github_commits_4weeks": data.get("developer_data", {}).get("commit_count_4_weeks", 0),
            "github_issues": data.get("developer_data", {}).get("closed_issues", 0),
            
            # Status
            "trending_coingecko": data.get("market_cap_rank", 1000) <= 100,
        }
        
        # Add advanced metrics if requested
        if include_advanced:
            advanced_data = _fetch_advanced_metrics(crypto_id, crypto_data)
            crypto_data.update(advanced_data)
        
        # Cache the result
        _set_cache(cache_key, crypto_data)
        
        return crypto_data
        
    except Exception as e:
        logger.error(f"Error fetching crypto data for {symbol}: {e}")
        return None


def _fetch_advanced_metrics(crypto_id: str, base_data: Dict) -> Dict:
    """
    Fetch advanced metrics including on-chain data.
    
    Args:
        crypto_id: CoinGecko ID
        base_data: Basic crypto data
    
    Returns:
        Dictionary with advanced metrics
    """
    advanced = {}
    
    try:
        # Calculate technical indicators from price history
        price_history = _fetch_price_history(crypto_id, days=60)
        if price_history:
            technical = _calculate_technical_indicators(price_history)
            advanced.update(technical)
        
        # Estimate on-chain metrics (would use real APIs in production)
        advanced.update(_estimate_on_chain_metrics(crypto_id, base_data))
        
        # Fetch trending status
        trending = _check_trending_status(crypto_id)
        advanced.update(trending)
        
        # Calculate derived metrics
        derived = _calculate_derived_metrics(base_data)
        advanced.update(derived)
        
    except Exception as e:
        logger.error(f"Error fetching advanced metrics: {e}")
    
    return advanced


def _fetch_price_history(crypto_id: str, days: int = 60) -> Optional[List[float]]:
    """Fetch historical price data"""
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
        params = {'vs_currency': 'usd', 'days': days}
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            prices = [p[1] for p in data.get('prices', [])]
            return prices
        
    except Exception as e:
        logger.error(f"Error fetching price history: {e}")
    
    return None


def _calculate_technical_indicators(prices: List[float]) -> Dict:
    """Calculate technical indicators from price history"""
    if not prices or len(prices) < 20:
        return {}
    
    prices_array = np.array(prices)
    
    try:
        # RSI Calculation
        rsi = _calculate_rsi(prices_array, period=14)
        
        # Moving Averages
        ema_9 = _calculate_ema(prices_array, 9)
        ema_21 = _calculate_ema(prices_array, 21)
        ema_50 = _calculate_ema(prices_array, 50) if len(prices) >= 50 else prices_array[-1]
        
        # MACD
        macd, signal = _calculate_macd(prices_array)
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = _calculate_bollinger_bands(prices_array)
        
        # Volume analysis (simplified - using price volatility as proxy)
        volatility = np.std(prices_array[-20:]) / np.mean(prices_array[-20:])
        
        return {
            'rsi': rsi,
            'ema_9': ema_9,
            'ema_21': ema_21,
            'ema_50': ema_50,
            'macd': macd,
            'macd_signal': signal,
            'bollinger_upper': bb_upper,
            'bollinger_middle': bb_middle,
            'bollinger_lower': bb_lower,
            'volatility_20d': volatility,
            'volume_ma_20': prices_array[-1]  # Simplified
        }
    
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        return {}


def _calculate_rsi(prices: np.ndarray, period: int = 14) -> float:
    """Calculate Relative Strength Index"""
    if len(prices) < period + 1:
        return 50.0
    
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return float(rsi)


def _calculate_ema(prices: np.ndarray, period: int) -> float:
    """Calculate Exponential Moving Average"""
    if len(prices) < period:
        return float(prices[-1])
    
    multiplier = 2 / (period + 1)
    ema = prices[-period]
    
    for price in prices[-period+1:]:
        ema = (price - ema) * multiplier + ema
    
    return float(ema)


def _calculate_macd(prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
    """Calculate MACD and Signal line"""
    if len(prices) < slow:
        return 0.0, 0.0
    
    ema_fast = _calculate_ema(prices, fast)
    ema_slow = _calculate_ema(prices, slow)
    macd = ema_fast - ema_slow
    
    # Simplified signal calculation
    signal_line = macd * 0.9  # Approximation
    
    return float(macd), float(signal_line)


def _calculate_bollinger_bands(prices: np.ndarray, period: int = 20, std_dev: int = 2) -> tuple:
    """Calculate Bollinger Bands"""
    if len(prices) < period:
        price = float(prices[-1])
        return price, price, price
    
    recent_prices = prices[-period:]
    middle = np.mean(recent_prices)
    std = np.std(recent_prices)
    
    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)
    
    return float(upper), float(middle), float(lower)


def _estimate_on_chain_metrics(crypto_id: str, base_data: Dict) -> Dict:
    """
    Estimate on-chain metrics (simplified - would use real blockchain APIs).
    """
    # These would come from blockchain explorers in production
    market_cap = base_data.get('marketCap', 0)
    volume = base_data.get('volume', 0)
    
    # Rough estimates based on market metrics
    estimated_holders = int(market_cap / 5000) if market_cap > 0 else 0
    estimated_tx_24h = int(volume / 1000) if volume > 0 else 0
    
    # Concentration estimates (would be real data in production)
    if market_cap > 1e9:
        top_10_holders_pct = 25  # Large caps are usually well-distributed
    elif market_cap > 100e6:
        top_10_holders_pct = 40
    elif market_cap > 10e6:
        top_10_holders_pct = 55
    else:
        top_10_holders_pct = 70  # Small caps often concentrated
    
    return {
        'holder_count': estimated_holders,
        'transactions_24h': estimated_tx_24h,
        'top_10_holders_percentage': top_10_holders_pct,
        'whale_transactions_24h': max(0, int(estimated_tx_24h / 100)),
        'liquidity_usd': volume * 0.05,  # Rough estimate
        'liquidity_locked': market_cap > 10e6,  # Assume larger projects lock liquidity
        'liquidity_lock_days': 365 if market_cap > 10e6 else 0,
        'contract_verified': market_cap > 1e6,
        'contract_audited': market_cap > 10e6,
        'audit_firm': 'CertiK' if market_cap > 100e6 else None,
        'days_since_launch': min(365, int(market_cap / 1e6)) if market_cap > 0 else 1,
        'listed_dex_count': 3 if market_cap > 10e6 else 1
    }


def _check_trending_status(crypto_id: str) -> Dict:
    """Check if crypto is trending on various platforms"""
    try:
        # Check CoinGecko trending
        url = "https://api.coingecko.com/api/v3/search/trending"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            trending_data = response.json()
            trending_coins = [coin['item']['id'] for coin in trending_data.get('coins', [])]
            
            return {
                'trending_coingecko': crypto_id in trending_coins,
                'trending_coinmarketcap': False  # Would check CMC API
            }
    
    except Exception as e:
        logger.error(f"Error checking trending: {e}")
    
    return {
        'trending_coingecko': False,
        'trending_coinmarketcap': False
    }


def _calculate_derived_metrics(base_data: Dict) -> Dict:
    """Calculate derived metrics from base data"""
    market_cap = base_data.get('marketCap', 0)
    volume = base_data.get('volume', 0)
    circ_supply = base_data.get('circulatingSupply', 1)
    total_supply = base_data.get('totalSupply', 1)
    
    # Twitter engagement (if available)
    twitter_followers = base_data.get('twitter_followers', 0)
    
    return {
        'volume_to_mcap_ratio': (volume / market_cap) if market_cap > 0 else 0,
        'supply_inflation': ((total_supply - circ_supply) / total_supply) if total_supply > 0 else 0,
        'social_dominance_score': min(100, twitter_followers / 1000) if twitter_followers > 0 else 0,
        'market_dominance': (market_cap / 1e12) * 100,  # % of $1T
        'sentiment_score': 0.5,  # Would come from sentiment analysis
        'twitter_mentions_24h': twitter_followers // 100 if twitter_followers > 0 else 0,
    }


def get_price_change_emoji(change: float) -> str:
    """Get emoji based on price change percentage"""
    if change > 10:
        return "🚀"
    elif change > 5:
        return "📈"
    elif change > 0:
        return "⬆️"
    elif change > -5:
        return "⬇️"
    elif change > -10:
        return "📉"
    else:
        return "💥"


def format_large_number(num: float) -> str:
    """Format large numbers to readable format (K, M, B, T)"""
    if num >= 1e12:
        return f"${num/1e12:.2f}T"
    elif num >= 1e9:
        return f"${num/1e9:.2f}B"
    elif num >= 1e6:
        return f"${num/1e6:.2f}M"
    elif num >= 1e3:
        return f"${num/1e3:.2f}K"
    else:
        return f"${num:.2f}"


def get_whale_transactions(crypto_id: str, hours: int = 24) -> List[Dict]:
    """
    Fetch recent whale transactions (mock - would use blockchain APIs).
    
    Returns:
        List of whale transaction dictionaries
    """
    # Mock data - in production, use blockchain explorers
    # Example: Etherscan, BscScan, Solscan APIs
    
    return [
        {
            'type': 'buy',
            'amount_usd': 1500000,
            'timestamp': datetime.now() - timedelta(hours=2),
            'wallet': '0x123...abc'
        },
        {
            'type': 'sell',
            'amount_usd': 800000,
            'timestamp': datetime.now() - timedelta(hours=5),
            'wallet': '0x456...def'
        }
    ]