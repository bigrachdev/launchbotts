"""
Hugging Face AI Integration for advanced NLP and sentiment analysis.
Replaces OpenAI with open-source models.
"""

import logging
from typing import Dict, List, Optional
from config import HUGGINGFACE_API_KEY, HUGGINGFACE_MODEL, USE_LOCAL_MODEL

logger = logging.getLogger(__name__)

# Try to import transformers for local model use
try:
    from transformers import (
        pipeline,
        AutoTokenizer,
        AutoModelForSequenceClassification,
        AutoModelForCausalLM
    )
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not installed. Install with: pip install transformers torch")

# Try to import huggingface_hub for API use
try:
    from huggingface_hub import InferenceClient
    HF_HUB_AVAILABLE = True
except ImportError:
    HF_HUB_AVAILABLE = False
    logger.warning("HF Hub not installed. Install with: pip install huggingface_hub")


class HuggingFaceAnalyzer:
    """Advanced AI analyzer using Hugging Face models"""
    
    def __init__(self):
        self.use_local = USE_LOCAL_MODEL and TRANSFORMERS_AVAILABLE
        self.sentiment_pipeline = None
        self.text_generator = None
        self.inference_client = None
        
        if self.use_local:
            self._initialize_local_models()
        elif HUGGINGFACE_API_KEY and HF_HUB_AVAILABLE:
            self._initialize_api_client()
        else:
            logger.warning("No Hugging Face setup available. Using fallback methods.")
    
    def _initialize_local_models(self):
        """Initialize local transformer models"""
        try:
            logger.info("Loading local Hugging Face models...")
            
            # Sentiment analysis model (FinBERT for financial sentiment)
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Text generation for insights (smaller model for speed)
            self.text_generator = pipeline(
                "text-generation",
                model="gpt2",  # Fast and efficient
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info("✅ Local models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading local models: {e}")
            self.use_local = False
    
    def _initialize_api_client(self):
        """Initialize Hugging Face API client"""
        try:
            self.inference_client = InferenceClient(token=HUGGINGFACE_API_KEY)
            logger.info("✅ Hugging Face API client initialized")
        except Exception as e:
            logger.error(f"Error initializing HF API: {e}")
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment of text using FinBERT or similar model.
        
        Args:
            text: Text to analyze (news, social media, etc.)
        
        Returns:
            Dict with sentiment score and label
        """
        try:
            if self.use_local and self.sentiment_pipeline:
                result = self.sentiment_pipeline(text[:512])[0]  # Limit length
                
                # Convert to normalized score (-1 to 1)
                label = result['label'].lower()
                confidence = result['score']
                
                if 'positive' in label:
                    score = confidence
                elif 'negative' in label:
                    score = -confidence
                else:
                    score = 0
                
                return {
                    'score': score,
                    'label': label,
                    'confidence': confidence
                }
            
            elif self.inference_client:
                # Use API
                result = self.inference_client.text_classification(
                    text[:512],
                    model="ProsusAI/finbert"
                )
                
                label = result[0]['label'].lower()
                confidence = result[0]['score']
                
                if 'positive' in label:
                    score = confidence
                elif 'negative' in label:
                    score = -confidence
                else:
                    score = 0
                
                return {
                    'score': score,
                    'label': label,
                    'confidence': confidence
                }
            
            else:
                # Fallback: Simple keyword-based sentiment
                return self._fallback_sentiment(text)
        
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return self._fallback_sentiment(text)
    
    def analyze_batch_sentiment(self, texts: List[str]) -> List[Dict]:
        """Analyze sentiment for multiple texts"""
        results = []
        
        for text in texts:
            results.append(self.analyze_sentiment(text))
        
        # Calculate aggregate
        if results:
            avg_score = sum(r['score'] for r in results) / len(results)
            avg_confidence = sum(r['confidence'] for r in results) / len(results)
            
            # Determine overall label
            if avg_score > 0.3:
                overall_label = "positive"
            elif avg_score < -0.3:
                overall_label = "negative"
            else:
                overall_label = "neutral"
            
            return {
                'individual_results': results,
                'aggregate_score': avg_score,
                'aggregate_confidence': avg_confidence,
                'overall_sentiment': overall_label,
                'total_analyzed': len(results)
            }
        
        return {'aggregate_score': 0, 'overall_sentiment': 'neutral'}
    
    def generate_market_insight(self, crypto_data: Dict) -> str:
        """
        Generate AI-powered market insight about a cryptocurrency.
        
        Args:
            crypto_data: Dictionary with crypto information
        
        Returns:
            Generated insight text
        """
        try:
            # Create prompt
            name = crypto_data.get('name', 'Unknown')
            market_cap = crypto_data.get('marketCap', 0)
            price_change = crypto_data.get('priceChange24h', 0)
            volume = crypto_data.get('volume', 0)
            
            prompt = f"""Analyze {name} cryptocurrency:
Market Cap: ${market_cap:,.0f}
24h Change: {price_change:+.2f}%
24h Volume: ${volume:,.0f}

Provide a brief 2-sentence market insight:"""
            
            if self.use_local and self.text_generator:
                result = self.text_generator(
                    prompt,
                    max_length=150,
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=True
                )[0]['generated_text']
                
                # Extract just the generated part
                insight = result.replace(prompt, "").strip()
                return insight
            
            elif self.inference_client:
                result = self.inference_client.text_generation(
                    prompt,
                    max_new_tokens=100,
                    temperature=0.7,
                    model="gpt2"
                )
                return result.strip()
            
            else:
                # Fallback: Template-based insight
                return self._generate_template_insight(crypto_data)
        
        except Exception as e:
            logger.error(f"Error generating insight: {e}")
            return self._generate_template_insight(crypto_data)
    
    def detect_rug_pull_risk(self, crypto_data: Dict) -> Dict:
        """
        Advanced rug pull detection using multiple signals.
        
        Args:
            crypto_data: Comprehensive crypto data
        
        Returns:
            Dict with risk score and factors
        """
        risk_score = 0
        risk_factors = []
        
        # Check liquidity lock
        if not crypto_data.get('liquidity_locked', False):
            risk_score += 30
            risk_factors.append("🚨 Liquidity not locked")
        
        # Check holder concentration
        top_holders_pct = crypto_data.get('top_10_holders_percentage', 0)
        if top_holders_pct > 70:
            risk_score += 25
            risk_factors.append(f"⚠️ Top 10 holders own {top_holders_pct}%")
        elif top_holders_pct > 50:
            risk_score += 15
            risk_factors.append(f"⚠️ Concentrated holdings ({top_holders_pct}%)")
        
        # Check contract verification
        if not crypto_data.get('contract_verified', False):
            risk_score += 20
            risk_factors.append("⚠️ Unverified contract")
        
        # Check audit status
        if not crypto_data.get('contract_audited', False):
            risk_score += 15
            risk_factors.append("⚠️ No security audit")
        
        # Check liquidity amount
        liquidity = crypto_data.get('liquidity_usd', 0)
        if liquidity < 50000:
            risk_score += 20
            risk_factors.append(f"🚨 Very low liquidity (${liquidity:,.0f})")
        elif liquidity < 100000:
            risk_score += 10
            risk_factors.append(f"⚠️ Low liquidity (${liquidity:,.0f})")
        
        # Check age
        days_old = crypto_data.get('days_since_launch', 999)
        if days_old < 7:
            risk_score += 15
            risk_factors.append("⚠️ Very new token (< 1 week)")
        elif days_old < 30:
            risk_score += 5
            risk_factors.append("⚠️ New token (< 1 month)")
        
        # Check transaction activity
        tx_24h = crypto_data.get('transactions_24h', 0)
        if tx_24h < 50:
            risk_score += 10
            risk_factors.append("⚠️ Low transaction activity")
        
        # Classify risk level
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
            'risk_factors': risk_factors
        }
    
    def analyze_whale_behavior(self, whale_transactions: List[Dict]) -> Dict:
        """
        Analyze whale transaction patterns.
        
        Args:
            whale_transactions: List of large transactions
        
        Returns:
            Analysis of whale behavior
        """
        if not whale_transactions:
            return {
                'pattern': 'no_activity',
                'signal': 'neutral',
                'description': 'No significant whale activity detected'
            }
        
        # Analyze buy vs sell
        buys = sum(1 for tx in whale_transactions if tx.get('type') == 'buy')
        sells = sum(1 for tx in whale_transactions if tx.get('type') == 'sell')
        
        buy_volume = sum(tx.get('amount_usd', 0) for tx in whale_transactions if tx.get('type') == 'buy')
        sell_volume = sum(tx.get('amount_usd', 0) for tx in whale_transactions if tx.get('type') == 'sell')
        
        # Determine pattern
        if buys > sells * 2:
            pattern = 'accumulation'
            signal = 'bullish'
            description = f"🐋 Whales accumulating - {buys} buys vs {sells} sells (${buy_volume:,.0f} bought)"
        elif sells > buys * 2:
            pattern = 'distribution'
            signal = 'bearish'
            description = f"⚠️ Whales distributing - {sells} sells vs {buys} buys (${sell_volume:,.0f} sold)"
        elif buy_volume > sell_volume * 1.5:
            pattern = 'strong_accumulation'
            signal = 'very_bullish'
            description = f"🐋🐋 Heavy whale accumulation - ${buy_volume:,.0f} vs ${sell_volume:,.0f}"
        elif sell_volume > buy_volume * 1.5:
            pattern = 'strong_distribution'
            signal = 'very_bearish'
            description = f"🚨 Heavy whale dumping - ${sell_volume:,.0f} vs ${buy_volume:,.0f}"
        else:
            pattern = 'balanced'
            signal = 'neutral'
            description = f"➡️ Balanced whale activity - {buys} buys, {sells} sells"
        
        return {
            'pattern': pattern,
            'signal': signal,
            'description': description,
            'buy_count': buys,
            'sell_count': sells,
            'buy_volume_usd': buy_volume,
            'sell_volume_usd': sell_volume
        }
    
    def _fallback_sentiment(self, text: str) -> Dict:
        """Fallback keyword-based sentiment analysis"""
        text_lower = text.lower()
        
        positive_words = [
            'bullish', 'moon', 'pump', 'buy', 'great', 'amazing', 'strong',
            'growth', 'profit', 'gain', 'up', 'surge', 'rocket', 'gem',
            'undervalued', 'potential', 'opportunity', 'breakout'
        ]
        
        negative_words = [
            'bearish', 'dump', 'sell', 'crash', 'scam', 'rug', 'weak',
            'loss', 'down', 'drop', 'avoid', 'warning', 'risk', 'bubble',
            'overvalued', 'concern', 'fraud', 'suspicious'
        ]
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        total = pos_count + neg_count
        if total == 0:
            score = 0
            label = 'neutral'
        else:
            score = (pos_count - neg_count) / total
            if score > 0.2:
                label = 'positive'
            elif score < -0.2:
                label = 'negative'
            else:
                label = 'neutral'
        
        return {
            'score': score,
            'label': label,
            'confidence': min(total / 10, 0.9)  # More keywords = higher confidence
        }
    
    def _generate_template_insight(self, crypto_data: Dict) -> str:
        """Generate template-based insight"""
        name = crypto_data.get('name', 'This cryptocurrency')
        price_change = crypto_data.get('priceChange24h', 0)
        volume = crypto_data.get('volume', 0)
        market_cap = crypto_data.get('marketCap', 0)
        
        if price_change > 10:
            trend = "showing strong bullish momentum"
        elif price_change > 5:
            trend = "trending upward"
        elif price_change < -10:
            trend = "under significant selling pressure"
        elif price_change < -5:
            trend = "experiencing a downturn"
        else:
            trend = "trading in a consolidation range"
        
        if volume > 10e6 and market_cap > 100e6:
            liquidity = "with healthy trading volume"
        elif volume < 1e6:
            liquidity = "but with limited liquidity"
        else:
            liquidity = "with moderate trading activity"
        
        return f"{name} is currently {trend} {liquidity}. Monitor closely for entry opportunities."


# Global instance
hf_analyzer = HuggingFaceAnalyzer()


def analyze_text_sentiment(text: str) -> Dict:
    """Quick access to sentiment analysis"""
    return hf_analyzer.analyze_sentiment(text)


def detect_rug_pull(crypto_data: Dict) -> Dict:
    """Quick access to rug pull detection"""
    return hf_analyzer.detect_rug_pull_risk(crypto_data)


def analyze_whales(whale_txs: List[Dict]) -> Dict:
    """Quick access to whale analysis"""
    return hf_analyzer.analyze_whale_behavior(whale_txs)


def generate_insight(crypto_data: Dict) -> str:
    """Quick access to insight generation"""
    return hf_analyzer.generate_market_insight(crypto_data)