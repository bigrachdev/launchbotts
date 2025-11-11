"""
AI-powered risk analysis engine - CRYPTO ONLY
Uses Hugging Face instead of OpenAI
Analyzes market data, sentiment, and fundamentals for crypto launches.
"""

import numpy as np
from typing import Dict, Any, Tuple
import logging
from config import RISK_THRESHOLDS

logger = logging.getLogger(__name__)


class RiskAnalyzer:
    """AI-powered risk analyzer for crypto launches"""
    
    def __init__(self):
        self.weights = {
            'fundamentals': 0.35,
            'technical': 0.25,
            'sentiment': 0.25,
            'event': 0.15
        }
    
    def analyze_crypto_launch(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze cryptocurrency launch or major event.
        
        Args:
            data: Dict with crypto-specific data
        
        Returns:
            Risk analysis result
        """
        scores = {}
        
        # 1. Project Fundamentals
        fundamentals_score = self._score_crypto_fundamentals(data)
        scores['fundamentals'] = fundamentals_score
        
        # 2. Technical Indicators
        technical_score = self._score_crypto_technicals(data)
        scores['technical'] = technical_score
        
        # 3. Community Sentiment
        sentiment_score = self._score_crypto_sentiment(data)
        scores['sentiment'] = sentiment_score
        
        # 4. Launch/Event Factors
        event_score = self._score_crypto_event(data)
        scores['event'] = event_score
        
        # Calculate weighted average
        final_score = sum(scores[k] * self.weights[k] for k in scores.keys())
        
        # Classify risk
        risk_level, risk_emoji = self._classify_risk(final_score)
        
        # Calculate confidence
        confidence = self._calculate_confidence(scores, data)
        
        # Generate summary
        summary = self._generate_crypto_summary(data, scores, risk_level)
        
        # Generate suggestion
        suggestion = self._generate_suggestion(final_score, risk_level, data)
        
        return {
            'final_score': round(final_score, 2),
            'risk_level': risk_level,
            'risk_emoji': risk_emoji,
            'confidence': round(confidence, 1),
            'scores': scores,
            'summary': summary,
            'suggestion': suggestion
        }
    
    def _score_crypto_fundamentals(self, data: Dict) -> float:
        """Score crypto project fundamentals (1-5)"""
        score = 2.5  # Default cautious
        
        # Team transparency
        team_score = data.get('team_transparency', 3)
        score += (team_score - 3) * 0.3
        
        # Audit status
        if data.get('audit_completed', False):
            score += 1.0
            if data.get('audit_firm', '') in ['CertiK', 'PeckShield', 'Quantstamp']:
                score += 0.5
        else:
            score -= 0.5
        
        # Tokenomics
        tokenomics_score = data.get('tokenomics_rating', 3)
        score += (tokenomics_score - 3) * 0.4
        
        # GitHub activity
        github_commits = data.get('github_commits_30d', 0)
        if github_commits > 50:
            score += 0.8
        elif github_commits > 20:
            score += 0.4
        elif github_commits == 0:
            score -= 0.5
        
        # Partnerships
        partnerships = data.get('major_partnerships', 0)
        score += min(partnerships * 0.3, 1.0)
        
        # Market cap (reasonable for launch)
        market_cap = data.get('market_cap', 0)
        if 1000000 < market_cap < 100000000:  # $1M - $100M sweet spot
            score += 0.5
        elif market_cap > 500000000:  # Too high for "launch"
            score -= 0.3
        
        return np.clip(score, 1.0, 5.0)
    
    def _score_crypto_technicals(self, data: Dict) -> float:
        """Score crypto technical indicators (1-5)"""
        score = 3.0
        
        # Liquidity (CRITICAL for crypto)
        liquidity = data.get('liquidity_usd', 0)
        if liquidity > 10000000:  # >$10M
            score += 1.5
        elif liquidity > 1000000:  # >$1M
            score += 1.0
        elif liquidity > 100000:  # >$100K
            score += 0.5
        elif liquidity < 50000:  # <$50K
            score -= 1.5
        
        # Wallet accumulation
        whale_activity = data.get('whale_accumulation', 'neutral')
        if whale_activity == 'accumulating':
            score += 0.8
        elif whale_activity == 'distributing':
            score -= 0.8
        
        # Price action
        price_change_7d = data.get('price_change_7d', 0)
        if 0 < price_change_7d < 50:
            score += 0.5
        elif price_change_7d > 100:
            score -= 0.5  # Too hot
        elif price_change_7d < -30:
            score -= 0.5
        
        # Holder distribution
        holder_concentration = data.get('top_10_holders_percentage', 0)
        if holder_concentration > 0:
            if holder_concentration < 30:
                score += 0.8
            elif holder_concentration < 50:
                score += 0.4
            elif holder_concentration > 70:
                score -= 1.0
        
        return np.clip(score, 1.0, 5.0)
    
    def _score_crypto_sentiment(self, data: Dict) -> float:
        """Score crypto community sentiment (1-5)"""
        score = 3.0
        
        # Community size
        community_size = data.get('community_members', 0)
        if community_size > 100000:
            score += 1.0
        elif community_size > 10000:
            score += 0.5
        elif community_size < 1000:
            score -= 0.5
        
        # Engagement rate
        engagement = data.get('engagement_rate', 0)
        if engagement > 10:
            score += 0.8
        elif engagement < 2:
            score -= 0.4
        
        # Sentiment tone
        sentiment = data.get('community_sentiment', 'neutral')
        if sentiment == 'very_positive':
            score += 1.0
        elif sentiment == 'positive':
            score += 0.6
        elif sentiment == 'negative':
            score -= 0.6
        elif sentiment == 'very_negative':
            score -= 1.0
        
        # Social mentions
        social_mentions = data.get('social_mentions', 0)
        if social_mentions > 10000:
            score += 0.5
        elif social_mentions > 1000:
            score += 0.3
        
        return np.clip(score, 1.0, 5.0)
    
    def _score_crypto_event(self, data: Dict) -> float:
        """Score crypto launch/event factors (1-5)"""
        score = 3.0
        
        # Launch type
        launch_type = data.get('event_type', 'unknown')
        if launch_type == 'mainnet_launch':
            score += 1.0
        elif launch_type == 'token_listing':
            score += 0.8
        elif launch_type == 'upgrade':
            score += 0.6
        elif launch_type == 'ido':
            score += 0.4
        
        # Vesting schedule (good tokenomics)
        if data.get('has_vesting', False):
            score += 0.8
        else:
            score -= 0.3
        
        # Initial market cap
        initial_mcap = data.get('initial_mcap_usd', 0)
        if 1000000 < initial_mcap < 50000000:
            score += 0.6
        elif initial_mcap > 100000000:
            score -= 0.4  # Too high for entry
        
        # Listing exchanges
        exchange_tier = data.get('exchange_tier', 'unknown')
        if exchange_tier == 'tier1':  # Binance, Coinbase, etc.
            score += 1.0
        elif exchange_tier == 'tier2':
            score += 0.5
        
        # Market timing
        market_condition = data.get('market_condition', 'neutral')
        if market_condition == 'bull':
            score += 0.5
        elif market_condition == 'bear':
            score -= 0.5
        
        return np.clip(score, 1.0, 5.0)
    
    def _classify_risk(self, score: float) -> Tuple[str, str]:
        """Classify risk level based on score"""
        if score >= 4.2:
            return 'Very Low Risk', '🟢'
        elif score >= 3.8:
            return 'Low Risk', '🟢'
        elif score >= 3.2:
            return 'Medium Risk', '🟡'
        elif score >= 2.5:
            return 'Medium-High Risk', '🟠'
        else:
            return 'High Risk', '🔴'
    
    def _calculate_confidence(self, scores: Dict, data: Dict) -> float:
        """Calculate confidence level based on data completeness"""
        # Base confidence
        confidence = 70.0
        
        # Check data completeness
        available_data = sum(1 for v in data.values() if v is not None and v != 0 and v != '')
        total_expected = len(data)
        data_completeness = (available_data / total_expected) * 100 if total_expected > 0 else 50
        
        # Adjust confidence based on score consistency
        score_values = list(scores.values())
        score_std = np.std(score_values)
        if score_std < 0.5:
            confidence += 15  # Very consistent
        elif score_std < 1.0:
            confidence += 10  # Consistent
        else:
            confidence += 5  # Some variance
        
        # Factor in data completeness
        confidence = (confidence + data_completeness) / 2
        
        return np.clip(confidence, 50.0, 95.0)
    
    def _generate_crypto_summary(self, data: Dict, scores: Dict, risk_level: str) -> str:
        """Generate crypto-specific summary"""
        summaries = []
        
        if data.get('audit_completed'):
            summaries.append("audited contract")
        
        if scores['fundamentals'] >= 4.0:
            summaries.append("strong project fundamentals")
        
        if data.get('major_partnerships', 0) > 0:
            summaries.append("notable partnerships")
        
        if scores['sentiment'] >= 4.0:
            summaries.append("positive community sentiment")
        
        liquidity = data.get('liquidity_usd', 0)
        if liquidity > 1000000:
            summaries.append("sufficient liquidity")
        elif liquidity < 100000:
            summaries.append("low liquidity warning")
        
        return ", ".join(summaries).capitalize() + "." if summaries else "Exercise caution with this launch."
    
    def _generate_suggestion(self, score: float, risk_level: str, data: Dict) -> str:
        """Generate actionable investment suggestion"""
        if score >= 4.5:
            return "Strong launch opportunity. Consider entry with majority position."
        elif score >= 4.0:
            return "Favorable launch signals. Consider partial position with room to add."
        elif score >= 3.5:
            return "Moderate opportunity. Small position or wait for post-launch confirmation."
        elif score >= 3.0:
            return "Mixed signals. Proceed with caution, small position only."
        elif score >= 2.5:
            return "High uncertainty. Wait for better setup or more data."
        else:
            return "Avoid. Multiple red flags present. Consider alternative opportunities."


# Helper function for easy access
def analyze_launch_event(asset_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for launch analysis - CRYPTO ONLY
    
    Args:
        asset_type: Should always be 'crypto'
        data: Market and sentiment data
    
    Returns:
        Complete risk analysis
    """
    analyzer = RiskAnalyzer()
    
    if asset_type == 'crypto':
        return analyzer.analyze_crypto_launch(data)
    else:
        # Fallback for any legacy calls
        logger.warning(f"Non-crypto asset type received: {asset_type}, treating as crypto")
        return analyzer.analyze_crypto_launch(data)