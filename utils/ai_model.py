"""
AI-powered risk scoring engine for stocks and cryptocurrencies.
Uses heuristic-based scoring with machine learning potential.
"""

import numpy as np
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)
"""
AI-powered risk scoring engine for cryptocurrencies.
CRYPTO ONLY - Stock support removed
Enhanced with DexScreener metrics for better meme coin analysis
"""

import numpy as np
from typing import Dict, Any, Tuple, List
import logging

logger = logging.getLogger(__name__)


def score_crypto(data: Dict[str, Any]) -> Tuple[int, str, List[str]]:
    """
    Calculate risk score for a cryptocurrency (0-100, higher = better/safer).
    
    Args:
        data: Crypto data dictionary from data_fetcher
    
    Returns:
        Tuple of (score, risk_level, factors)
    """
    score = 0
    factors = []
    
    try:
        # Market Cap Score (max 30 points)
        market_cap = data.get("marketCap", 0)
        if market_cap > 100e9:  # >$100B
            score += 30
            factors.append("✅ Mega-cap ($100B+) - Very stable")
        elif market_cap > 50e9:  # >$50B
            score += 28
            factors.append("✅ Top-tier market cap ($50B+)")
        elif market_cap > 10e9:  # >$10B
            score += 25
            factors.append("✅ Large cap ($10B+)")
        elif market_cap > 1e9:  # >$1B
            score += 20
            factors.append("✅ Medium cap ($1B+)")
        elif market_cap > 100e6:  # >$100M
            score += 15
            factors.append("⚠️ Small cap ($100M+)")
        elif market_cap > 10e6:  # >$10M
            score += 10
            factors.append("⚠️ Micro cap ($10M+)")
        else:
            score += 5
            factors.append("❌ Nano cap (<$10M) - High risk")
        
        # Volume Score (max 20 points)
        volume = data.get("volume", 0)
        if volume > 5e9:  # >$5B
            score += 20
            factors.append("✅ Massive trading volume ($5B+)")
        elif volume > 1e9:  # >$1B
            score += 18
            factors.append("✅ High trading volume ($1B+)")
        elif volume > 100e6:  # >$100M
            score += 15
            factors.append("✅ Good volume ($100M+)")
        elif volume > 10e6:  # >$10M
            score += 12
            factors.append("✅ Moderate volume ($10M+)")
        elif volume > 1e6:  # >$1M
            score += 8
            factors.append("⚠️ Low volume ($1M+)")
        else:
            score += 3
            factors.append("❌ Very low volume (<$1M)")
        
        # Volume to Market Cap Ratio (Health check)
        if market_cap > 0:
            volume_ratio = (volume / market_cap) * 100
            if 1 <= volume_ratio <= 10:
                score += 5
                factors.append("✅ Healthy volume/mcap ratio")
            elif volume_ratio > 20:
                score -= 3
                factors.append("⚠️ Abnormally high volume - possible pump")
        
        # Community Score (max 15 points)
        community_score = data.get("communityScore", 0)
        if community_score > 80:
            score += 15
            factors.append("✅ Exceptional community (80+)")
        elif community_score > 70:
            score += 13
            factors.append("✅ Strong community (70+)")
        elif community_score > 50:
            score += 10
            factors.append("✅ Good community (50+)")
        elif community_score > 30:
            score += 6
            factors.append("⚠️ Moderate community (30+)")
        else:
            score += 2
            factors.append("❌ Weak community (<30)")
        
        # Developer Score (max 15 points)
        dev_score = data.get("developerScore", 0)
        if dev_score > 80:
            score += 15
            factors.append("✅ Exceptional development (80+)")
        elif dev_score > 70:
            score += 13
            factors.append("✅ Active development (70+)")
        elif dev_score > 50:
            score += 10
            factors.append("✅ Good development (50+)")
        elif dev_score > 30:
            score += 6
            factors.append("⚠️ Moderate development (30+)")
        else:
            score += 2
            factors.append("❌ Low development activity (<30)")
        
        # Price Volatility Analysis (max 20 points)
        price_change_24h = abs(data.get("priceChange24h", 0))
        price_change_7d = abs(data.get("priceChange7d", 0))
        price_change_30d = abs(data.get("priceChange30d", 0))
        
        # Calculate volatility score
        if price_change_24h < 3 and price_change_7d < 10:
            score += 20
            factors.append("✅ Very low volatility - Stable")
        elif price_change_24h < 5 and price_change_7d < 15:
            score += 17
            factors.append("✅ Low volatility")
        elif price_change_24h < 10 and price_change_7d < 30:
            score += 14
            factors.append("✅ Moderate volatility")
        elif price_change_24h < 20 and price_change_7d < 50:
            score += 10
            factors.append("⚠️ High volatility")
        elif price_change_24h < 40:
            score += 6
            factors.append("⚠️ Very high volatility")
        else:
            score += 3
            factors.append("❌ Extreme volatility (>40% in 24h)")
        
        # Price trend analysis
        if price_change_24h > 0 and price_change_7d > 0 and price_change_30d > 0:
            score += 3
            factors.append("✅ Consistent uptrend across all timeframes")
        elif price_change_24h < 0 and price_change_7d < 0 and price_change_30d < 0:
            score -= 3
            factors.append("❌ Consistent downtrend across all timeframes")
        
        # Liquidity Score (if available from DexScreener integration)
        liquidity = data.get("liquidity_usd", 0)
        if liquidity > 0:
            if liquidity > 10e6:  # >$10M
                score += 5
                factors.append("✅ Excellent liquidity ($10M+)")
            elif liquidity > 1e6:  # >$1M
                score += 4
                factors.append("✅ Good liquidity ($1M+)")
            elif liquidity > 100e3:  # >$100K
                score += 2
                factors.append("⚠️ Moderate liquidity ($100K+)")
            else:
                score -= 2
                factors.append("❌ Low liquidity (<$100K)")
        
        # Holder concentration (if available)
        holder_concentration = data.get("top_10_holders_percentage", 0)
        if holder_concentration > 0:
            if holder_concentration < 30:
                score += 5
                factors.append("✅ Well distributed (<30% top holders)")
            elif holder_concentration < 50:
                score += 3
                factors.append("✅ Fair distribution (30-50%)")
            elif holder_concentration < 70:
                score -= 2
                factors.append("⚠️ Concentrated holdings (50-70%)")
            else:
                score -= 5
                factors.append("❌ Highly concentrated (>70% top holders)")
        
        # Age/maturity bonus (if available)
        days_old = data.get("days_since_launch", 0)
        if days_old > 365:
            score += 5
            factors.append("✅ Established project (1+ years)")
        elif days_old > 180:
            score += 3
            factors.append("✅ Mature project (6+ months)")
        elif days_old < 30:
            score -= 3
            factors.append("⚠️ Very new project (<1 month)")
        
        # ATH distance (how far from all-time high)
        ath_change = data.get("ath_change_percentage", 0)
        if ath_change and ath_change != 0:
            if ath_change > -20:
                score += 3
                factors.append("✅ Near all-time high")
            elif ath_change < -80:
                score += 2
                factors.append("💡 Deep discount from ATH (-80%+)")
        
        # Ensure score is between 0-100
        score = max(0, min(100, score))
        
        # Determine risk level with more granular categories
        if score >= 80:
            risk_level = "🟢 VERY LOW RISK"
        elif score >= 70:
            risk_level = "🟢 LOW RISK"
        elif score >= 60:
            risk_level = "🟡 LOW-MEDIUM RISK"
        elif score >= 50:
            risk_level = "🟡 MEDIUM RISK"
        elif score >= 40:
            risk_level = "🟠 MEDIUM-HIGH RISK"
        elif score >= 30:
            risk_level = "🟠 HIGH RISK"
        else:
            risk_level = "🔴 VERY HIGH RISK"
        
        return score, risk_level, factors
        
    except Exception as e:
        logger.error(f"Error scoring crypto: {e}")
        return 50, "🟡 MEDIUM RISK", ["⚠️ Error calculating complete score"]


def score_meme_coin(data: Dict[str, Any], dex_data: Dict[str, Any] = None) -> Tuple[int, str, List[str]]:
    """
    Special scoring for meme coins with emphasis on liquidity and rug pull risks.
    
    Args:
        data: CoinGecko data
        dex_data: Optional DexScreener data
    
    Returns:
        Tuple of (score, risk_level, factors)
    """
    score = 0
    factors = []
    
    try:
        # For meme coins, we weight differently
        # Liquidity and safety are MORE important than fundamentals
        
        # Liquidity (max 35 points - CRITICAL for meme coins)
        if dex_data:
            liquidity = dex_data.get('liquidity_usd', 0)
            if liquidity > 1e6:  # >$1M
                score += 35
                factors.append("✅ Excellent liquidity ($1M+)")
            elif liquidity > 500e3:  # >$500K
                score += 28
                factors.append("✅ Good liquidity ($500K+)")
            elif liquidity > 100e3:  # >$100K
                score += 20
                factors.append("⚠️ Moderate liquidity ($100K+)")
            elif liquidity > 50e3:  # >$50K
                score += 12
                factors.append("⚠️ Low liquidity ($50K+)")
            else:
                score += 5
                factors.append("❌ Very low liquidity (<$50K)")
        
        # Volume (max 20 points)
        volume = data.get("volume", 0)
        if volume > 10e6:
            score += 20
            factors.append("✅ High volume ($10M+)")
        elif volume > 1e6:
            score += 15
            factors.append("✅ Good volume ($1M+)")
        elif volume > 100e3:
            score += 10
            factors.append("⚠️ Moderate volume")
        else:
            score += 5
            factors.append("❌ Low volume")
        
        # Community (max 20 points - VITAL for meme coins)
        community_score = data.get("communityScore", 0)
        if community_score > 70:
            score += 20
            factors.append("✅ Strong community (70+)")
        elif community_score > 50:
            score += 15
            factors.append("✅ Active community (50+)")
        elif community_score > 30:
            score += 10
            factors.append("⚠️ Growing community")
        else:
            score += 5
            factors.append("❌ Weak community")
        
        # Age (max 15 points - newer = riskier for memes)
        if dex_data:
            age_hours = dex_data.get('age_hours', 0)
            if age_hours > 720:  # >30 days
                score += 15
                factors.append("✅ Established (30+ days)")
            elif age_hours > 168:  # >7 days
                score += 10
                factors.append("✅ Survived 1+ week")
            elif age_hours > 24:
                score += 5
                factors.append("⚠️ Very new (1-7 days)")
            else:
                score += 0
                factors.append("❌ Brand new (<24h) - HIGH RISK")
        
        # Buy/Sell pressure (max 10 points)
        if dex_data:
            buy_ratio = dex_data.get('buy_sell_ratio_1h', 0.5)
            if buy_ratio > 0.7:
                score += 10
                factors.append("✅ Strong buy pressure (70%+)")
            elif buy_ratio > 0.55:
                score += 7
                factors.append("✅ Positive buy pressure")
            elif buy_ratio > 0.45:
                score += 5
                factors.append("⚠️ Balanced pressure")
            else:
                score += 2
                factors.append("❌ Selling pressure dominant")
        
        # Market cap (relative to liquidity)
        market_cap = data.get("marketCap", 0)
        if dex_data and dex_data.get('liquidity_usd', 0) > 0:
            mcap_to_liq = market_cap / dex_data['liquidity_usd']
            if mcap_to_liq < 10:
                score += 5
                factors.append("✅ Good mcap/liquidity ratio")
            elif mcap_to_liq > 50:
                score -= 5
                factors.append("⚠️ High mcap vs liquidity - risk")
        
        # Ensure score is 0-100
        score = max(0, min(100, score))
        
        # Risk levels for meme coins (stricter thresholds)
        if score >= 75:
            risk_level = "🟢 LOWER RISK (for meme coin)"
        elif score >= 60:
            risk_level = "🟡 MODERATE RISK"
        elif score >= 45:
            risk_level = "🟠 HIGH RISK"
        else:
            risk_level = "🔴 VERY HIGH RISK"
        
        return score, risk_level, factors
        
    except Exception as e:
        logger.error(f"Error scoring meme coin: {e}")
        return 30, "🔴 VERY HIGH RISK", ["⚠️ Error calculating score - assume high risk"]


def get_recommendation(score: int, asset_type: str = "crypto") -> str:
    """
    Get investment recommendation based on score.
    
    Args:
        score: Risk score (0-100)
        asset_type: Type of asset
    
    Returns:
        Recommendation text
    """
    if asset_type == "crypto":
        if score >= 80:
            return "💚 STRONG BUY - Excellent fundamentals, low risk. Suitable for long-term holding."
        elif score >= 70:
            return "💙 BUY - Good opportunity with manageable risk. Consider for portfolio."
        elif score >= 60:
            return "💛 MODERATE BUY - Decent fundamentals but watch volatility. Suitable for balanced portfolios."
        elif score >= 50:
            return "🧡 HOLD/WATCH - Mixed signals. Monitor closely before investing."
        elif score >= 40:
            return "🧡 SPECULATIVE - Higher risk. Only for experienced traders with risk tolerance."
        elif score >= 30:
            return "❤️ HIGH RISK - Significant volatility and uncertainty. Small positions only."
        else:
            return "💔 AVOID - Too many risk factors. Consider safer alternatives."
    else:
        return "⚠️ PROCEED WITH CAUTION - Do your own research and never invest more than you can afford to lose."
def score_crypto(data: Dict[str, Any]) -> Tuple[int, str, list]:
    """
    Calculate risk score for a cryptocurrency (0-100, higher = better/safer).
    
    Args:
        data: Crypto data dictionary from data_fetcher
    
    Returns:
        Tuple of (score, risk_level, factors)
    """
    score = 0
    factors = []
    
    try:
        # Market Cap Score (max 30 points)
        market_cap = data.get("marketCap", 0)
        if market_cap > 50e9:  # >$50B
            score += 30
            factors.append("✅ Top-tier market cap ($50B+)")
        elif market_cap > 10e9:  # >$10B
            score += 25
            factors.append("✅ Large cap ($10B+)")
        elif market_cap > 1e9:  # >$1B
            score += 20
            factors.append("✅ Medium cap ($1B+)")
        elif market_cap > 100e6:  # >$100M
            score += 15
            factors.append("⚠️ Small cap ($100M+)")
        else:
            score += 5
            factors.append("❌ Micro cap (<$100M)")
        
        # Volume Score (max 20 points)
        volume = data.get("volume", 0)
        if volume > 1e9:  # >$1B
            score += 20
            factors.append("✅ High trading volume ($1B+)")
        elif volume > 100e6:  # >$100M
            score += 15
            factors.append("✅ Good volume ($100M+)")
        elif volume > 10e6:  # >$10M
            score += 10
            factors.append("⚠️ Moderate volume")
        else:
            score += 5
            factors.append("❌ Low volume")
        
        # Community Score (max 15 points)
        community_score = data.get("communityScore", 0)
        if community_score > 70:
            score += 15
            factors.append("✅ Strong community (70+)")
        elif community_score > 50:
            score += 12
            factors.append("✅ Good community (50+)")
        elif community_score > 30:
            score += 8
            factors.append("⚠️ Moderate community")
        else:
            score += 3
            factors.append("❌ Weak community")
        
        # Developer Score (max 15 points)
        dev_score = data.get("developerScore", 0)
        if dev_score > 70:
            score += 15
            factors.append("✅ Active development (70+)")
        elif dev_score > 50:
            score += 12
            factors.append("✅ Good development (50+)")
        elif dev_score > 30:
            score += 8
            factors.append("⚠️ Moderate development")
        else:
            score += 3
            factors.append("❌ Low development activity")
        
        # Price Volatility (max 20 points)
        price_change_24h = abs(data.get("priceChange24h", 0))
        price_change_7d = abs(data.get("priceChange7d", 0))
        
        if price_change_24h < 5 and price_change_7d < 15:
            score += 20
            factors.append("✅ Low volatility")
        elif price_change_24h < 10 and price_change_7d < 30:
            score += 15
            factors.append("✅ Moderate volatility")
        elif price_change_24h < 20:
            score += 10
            factors.append("⚠️ High volatility")
        else:
            score += 5
            factors.append("❌ Extreme volatility")
        
        # Add slight randomness for variability (±5 points)
        randomness = np.random.randint(-5, 6)
        score += randomness
        
        # Ensure score is between 0-100
        score = max(0, min(100, score))
        
        # Determine risk level
        if score >= 75:
            risk_level = "🟢 LOW RISK"
        elif score >= 50:
            risk_level = "🟡 MEDIUM RISK"
        elif score >= 30:
            risk_level = "🟠 HIGH RISK"
        else:
            risk_level = "🔴 VERY HIGH RISK"
        
        return score, risk_level, factors
        
    except Exception as e:
        logger.error(f"Error scoring crypto: {e}")
        return 50, "🟡 MEDIUM RISK", ["⚠️ Error calculating score"]


def get_recommendation(score: int, asset_type: str = "stock") -> str:
    """Get investment recommendation based on score"""
    if score >= 75:
        return f"💚 STRONG {asset_type.upper()} - Low risk, suitable for conservative portfolios"
    elif score >= 60:
        return f"💙 GOOD {asset_type.upper()} - Moderate risk, balanced opportunity"
    elif score >= 40:
        return f"💛 SPECULATIVE - Higher risk, potential rewards"
    else:
        return f"❤️ HIGH RISK - Only for experienced traders, high volatility"