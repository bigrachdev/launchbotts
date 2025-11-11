
import requests
import logging
from typing import Optional, Dict, List
from datetime import datetime
import time

logger = logging.getLogger(__name__)

# Rate limiting
_last_request_time = 0
_min_request_interval = 1.0  # 1 second between requests


class DexScreenerAPI:
    """DexScreener API client for DEX data"""
    
    BASE_URL = "https://api.dexscreener.com/latest/dex"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LaunchBot/1.0',
            'Accept': 'application/json'
        })
    
    def _rate_limit(self):
        """Simple rate limiting"""
        global _last_request_time
        now = time.time()
        elapsed = now - _last_request_time
        
        if elapsed < _min_request_interval:
            time.sleep(_min_request_interval - elapsed)
        
        _last_request_time = time.time()
    
    def search_pairs(self, query: str) -> Optional[List[Dict]]:
        """
        Search for token pairs by symbol or address.
        
        Args:
            query: Token symbol (e.g., 'PEPE') or contract address
        
        Returns:
            List of pair data dictionaries
        """
        try:
            self._rate_limit()
            
            url = f"{self.BASE_URL}/search/?q={query}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                
                if pairs:
                    logger.info(f"Found {len(pairs)} pairs for {query}")
                    return pairs
                else:
                    logger.warning(f"No pairs found for {query}")
                    return None
            else:
                logger.error(f"DexScreener API error: {response.status_code}")
                return None
        
        except Exception as e:
            logger.error(f"Error searching DexScreener: {e}")
            return None
    
    def get_token_pairs(self, token_address: str) -> Optional[List[Dict]]:
        """
        Get all pairs for a specific token address.
        
        Args:
            token_address: Token contract address
        
        Returns:
            List of pair data
        """
        try:
            self._rate_limit()
            
            url = f"{self.BASE_URL}/tokens/{token_address}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('pairs', [])
            else:
                return None
        
        except Exception as e:
            logger.error(f"Error fetching token pairs: {e}")
            return None
    
    def get_pair_by_address(self, pair_address: str) -> Optional[Dict]:
        """
        Get specific pair data by pair address.
        
        Args:
            pair_address: Liquidity pair address
        
        Returns:
            Pair data dictionary
        """
        try:
            self._rate_limit()
            
            url = f"{self.BASE_URL}/pairs/{pair_address}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                return pairs[0] if pairs else None
            else:
                return None
        
        except Exception as e:
            logger.error(f"Error fetching pair: {e}")
            return None


# Global instance
dex_api = DexScreenerAPI()


def get_dex_data(symbol: str) -> Optional[Dict]:
    """
    Get comprehensive DEX data for a token.
    
    Args:
        symbol: Token symbol (e.g., 'PEPE', 'SHIB')
    
    Returns:
        Processed token data dictionary
    """
    try:
        # Search for token
        pairs = dex_api.search_pairs(symbol)
        
        if not pairs:
            return None
        
        # Find best pair (highest liquidity)
        best_pair = max(pairs, key=lambda p: p.get('liquidity', {}).get('usd', 0))
        
        # Extract data
        token_data = {
            # Basic Info
            'symbol': symbol.upper(),
            'name': best_pair.get('baseToken', {}).get('name', symbol),
            'address': best_pair.get('baseToken', {}).get('address', ''),
            'chain': best_pair.get('chainId', 'unknown'),
            
            # Price Data
            'price_usd': float(best_pair.get('priceUsd', 0)),
            'price_native': float(best_pair.get('priceNative', 0)),
            
            # Price Changes
            'price_change_5m': float(best_pair.get('priceChange', {}).get('m5', 0)),
            'price_change_1h': float(best_pair.get('priceChange', {}).get('h1', 0)),
            'price_change_6h': float(best_pair.get('priceChange', {}).get('h6', 0)),
            'price_change_24h': float(best_pair.get('priceChange', {}).get('h24', 0)),
            
            # Volume
            'volume_5m': float(best_pair.get('volume', {}).get('m5', 0)),
            'volume_1h': float(best_pair.get('volume', {}).get('h1', 0)),
            'volume_6h': float(best_pair.get('volume', {}).get('h6', 0)),
            'volume_24h': float(best_pair.get('volume', {}).get('h24', 0)),
            
            # Liquidity
            'liquidity_usd': float(best_pair.get('liquidity', {}).get('usd', 0)),
            'liquidity_base': float(best_pair.get('liquidity', {}).get('base', 0)),
            'liquidity_quote': float(best_pair.get('liquidity', {}).get('quote', 0)),
            
            # Market Cap (if available)
            'market_cap': float(best_pair.get('fdv', 0)),  # Fully diluted valuation
            
            # Trading Info
            'dex_name': best_pair.get('dexId', ''),
            'pair_address': best_pair.get('pairAddress', ''),
            'pair_created_at': best_pair.get('pairCreatedAt', 0),
            
            # Buys/Sells
            'txns_5m_buys': best_pair.get('txns', {}).get('m5', {}).get('buys', 0),
            'txns_5m_sells': best_pair.get('txns', {}).get('m5', {}).get('sells', 0),
            'txns_1h_buys': best_pair.get('txns', {}).get('h1', {}).get('buys', 0),
            'txns_1h_sells': best_pair.get('txns', {}).get('h1', {}).get('sells', 0),
            'txns_6h_buys': best_pair.get('txns', {}).get('h6', {}).get('buys', 0),
            'txns_6h_sells': best_pair.get('txns', {}).get('h6', {}).get('sells', 0),
            'txns_24h_buys': best_pair.get('txns', {}).get('h24', {}).get('buys', 0),
            'txns_24h_sells': best_pair.get('txns', {}).get('h24', {}).get('sells', 0),
            
            # URLs
            'url': best_pair.get('url', ''),
            
            # Age calculation
            'age_hours': _calculate_age_hours(best_pair.get('pairCreatedAt', 0)),
        }
        
        # Calculate derived metrics
        token_data.update(_calculate_dex_metrics(token_data))
        
        return token_data
    
    except Exception as e:
        logger.error(f"Error getting DEX data for {symbol}: {e}")
        return None


def _calculate_age_hours(created_timestamp: int) -> float:
    """Calculate token age in hours"""
    if not created_timestamp:
        return 0
    
    created_time = datetime.fromtimestamp(created_timestamp / 1000)  # milliseconds
    age = datetime.now() - created_time
    return age.total_seconds() / 3600


def _calculate_dex_metrics(data: Dict) -> Dict:
    """Calculate additional metrics from DEX data"""
    metrics = {}
    
    # Buy/Sell Pressure (last 1h)
    buys_1h = data.get('txns_1h_buys', 0)
    sells_1h = data.get('txns_1h_sells', 0)
    total_txns_1h = buys_1h + sells_1h
    
    if total_txns_1h > 0:
        metrics['buy_sell_ratio_1h'] = buys_1h / total_txns_1h
    else:
        metrics['buy_sell_ratio_1h'] = 0.5
    
    # Volume to Liquidity Ratio (24h)
    volume_24h = data.get('volume_24h', 0)
    liquidity = data.get('liquidity_usd', 1)
    
    metrics['volume_to_liquidity'] = volume_24h / liquidity if liquidity > 0 else 0
    
    # Price Momentum Score
    changes = [
        data.get('price_change_5m', 0),
        data.get('price_change_1h', 0),
        data.get('price_change_6h', 0),
        data.get('price_change_24h', 0)
    ]
    
    # Weighted momentum (recent changes matter more)
    momentum = (
        changes[0] * 0.4 +  # 5m
        changes[1] * 0.3 +  # 1h
        changes[2] * 0.2 +  # 6h
        changes[3] * 0.1    # 24h
    )
    metrics['momentum_score'] = momentum
    
    # Activity Level
    total_txns_24h = data.get('txns_24h_buys', 0) + data.get('txns_24h_sells', 0)
    
    if total_txns_24h > 1000:
        metrics['activity_level'] = 'very_high'
    elif total_txns_24h > 500:
        metrics['activity_level'] = 'high'
    elif total_txns_24h > 100:
        metrics['activity_level'] = 'medium'
    elif total_txns_24h > 10:
        metrics['activity_level'] = 'low'
    else:
        metrics['activity_level'] = 'very_low'
    
    return metrics


def detect_rug_pull_signals(dex_data: Dict) -> Dict:
    """
    Detect potential rug pull signals from DEX data.
    
    Args:
        dex_data: Token data from get_dex_data()
    
    Returns:
        Rug pull risk analysis
    """
    risk_score = 0
    signals = []
    
    # 1. Very new token with high volume
    age_hours = dex_data.get('age_hours', 999)
    volume_24h = dex_data.get('volume_24h', 0)
    liquidity = dex_data.get('liquidity_usd', 0)
    
    if age_hours < 24 and volume_24h > liquidity * 5:
        risk_score += 30
        signals.append("🚨 New token with suspicious volume spike")
    
    # 2. Low liquidity
    if liquidity < 10000:
        risk_score += 25
        signals.append(f"⚠️ Very low liquidity (${liquidity:,.0f})")
    elif liquidity < 50000:
        risk_score += 15
        signals.append(f"⚠️ Low liquidity (${liquidity:,.0f})")
    
    # 3. Heavy selling pressure
    buy_sell_ratio = dex_data.get('buy_sell_ratio_1h', 0.5)
    if buy_sell_ratio < 0.3:
        risk_score += 20
        signals.append("📉 Heavy selling pressure (70% sells)")
    
    # 4. Extreme price volatility
    price_change_1h = abs(dex_data.get('price_change_1h', 0))
    if price_change_1h > 50:
        risk_score += 15
        signals.append(f"⚡ Extreme volatility ({price_change_1h:+.1f}% in 1h)")
    
    # 5. Very high volume to liquidity (potential dump)
    vol_to_liq = dex_data.get('volume_to_liquidity', 0)
    if vol_to_liq > 10:
        risk_score += 20
        signals.append("⚠️ Abnormally high volume vs liquidity")
    
    # 6. Dead volume (no transactions)
    total_txns_1h = (dex_data.get('txns_1h_buys', 0) + 
                     dex_data.get('txns_1h_sells', 0))
    if total_txns_1h < 5 and age_hours > 24:
        risk_score += 10
        signals.append("💀 Very low trading activity")
    
    # Classify risk
    if risk_score >= 70:
        risk_level = "🔴 CRITICAL RUG PULL RISK"
    elif risk_score >= 50:
        risk_level = "🟠 HIGH RUG PULL RISK"
    elif risk_score >= 30:
        risk_level = "🟡 MODERATE RISK"
    else:
        risk_level = "🟢 LOW RUG PULL RISK"
    
    return {
        'risk_score': min(risk_score, 100),
        'risk_level': risk_level,
        'signals': signals,
        'liquidity_usd': liquidity,
        'age_hours': age_hours,
        'buy_sell_ratio': buy_sell_ratio
    }


def format_dex_data(dex_data: Dict) -> str:
    """
    Format DEX data for display.
    
    Args:
        dex_data: Token data from get_dex_data()
    
    Returns:
        Formatted string
    """
    if not dex_data:
        return "No DEX data available"
    
    # Price changes with emojis
    changes = [
        ('5m', dex_data.get('price_change_5m', 0)),
        ('1h', dex_data.get('price_change_1h', 0)),
        ('6h', dex_data.get('price_change_6h', 0)),
        ('24h', dex_data.get('price_change_24h', 0))
    ]
    
    change_text = " | ".join([
        f"{period}: {change:+.1f}%" for period, change in changes
    ])
    
    # Buy/Sell ratio
    buy_ratio = dex_data.get('buy_sell_ratio_1h', 0.5)
    buy_pct = buy_ratio * 100
    sell_pct = (1 - buy_ratio) * 100
    
    pressure_emoji = "🟢" if buy_ratio > 0.6 else "🔴" if buy_ratio < 0.4 else "🟡"
    
    msg = (
        f"💹 DEX Data - {dex_data['dex_name']}\n"
        f"{'='*30}\n\n"
        f"💰 Price: ${dex_data['price_usd']:.8f}\n"
        f"📊 Changes: {change_text}\n\n"
        f"💧 Liquidity: ${dex_data['liquidity_usd']:,.0f}\n"
        f"📈 Volume (24h): ${dex_data['volume_24h']:,.0f}\n\n"
        f"{pressure_emoji} Buy/Sell (1h): {buy_pct:.0f}% / {sell_pct:.0f}%\n"
        f"🔄 Transactions (24h): {dex_data.get('txns_24h_buys', 0) + dex_data.get('txns_24h_sells', 0)}\n"
        f"⏰ Age: {dex_data['age_hours']:.1f} hours\n\n"
        f"🔗 Chain: {dex_data['chain']}\n"
        f"📍 Pair: {dex_data['pair_address'][:10]}..."
    )
    
    return msg