"""
Automated alert system for market intelligence.
Sends periodic updates to users with alerts enabled.
100% FREE - No subscription checks
"""

import asyncio
import logging
from aiogram import Bot
from datetime import datetime
import database
from utils.data_fetcher import get_crypto_data, format_large_number
from utils.ai_model import score_crypto
from config import ALERT_INTERVAL_HOURS, ALERT_RISK_THRESHOLD

logger = logging.getLogger(__name__)


async def analyze_watchlist_for_user(bot: Bot, user_id: int):
    """Analyze user's watchlist and send alerts for high-score assets"""
    try:
        watchlist = await database.get_watchlist(user_id)
        
        if not watchlist:
            return
        
        alerts_sent = 0
        
        for item in watchlist:
            ticker = item['ticker']
            is_meme = item.get('is_meme_coin', False)
            
            try:
                # Fetch and analyze crypto
                data = get_crypto_data(ticker)
                if data:
                    score, risk_level, factors = score_crypto(data)
                    
                    if score >= ALERT_RISK_THRESHOLD:
                        price = data.get('price', 0)
                        change_24h = data.get('priceChange24h', 0)
                        
                        coin_type = "🔥 Meme Coin" if is_meme else "💎 Crypto"
                        
                        message = (
                            f"🚨 Strong Signal: {ticker} {coin_type}\n\n"
                            f"Risk Score: {score}/100 {risk_level}\n"
                            f"Price: ${price:,.8f} ({change_24h:+.2f}% 24h)\n"
                            f"Market Cap: {format_large_number(data['marketCap'])}\n"
                            f"Community: {data['communityScore']:.0f}/100\n\n"
                            f"Top Factor: {factors[0] if factors else 'N/A'}\n\n"
                            f"💡 This crypto is showing strong fundamentals!"
                        )
                        
                        await bot.send_message(user_id, message, parse_mode="Markdown")
                        await database.log_alert(user_id, ticker, 'high_score', message)
                        alerts_sent += 1
                
                # Add delay to avoid rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error analyzing {ticker} for user {user_id}: {e}")
                continue
        
        if alerts_sent > 0:
            logger.info(f"Sent {alerts_sent} alerts to user {user_id}")
            
    except Exception as e:
        logger.error(f"Error analyzing watchlist for user {user_id}: {e}")


async def send_market_alerts(bot: Bot):
    """
    Main alert loop - runs periodically to send market intelligence alerts.
    100% FREE - No subscription/trial checks
    """
    logger.info("🔔 Starting market alerts system...")
    
    while True:
        try:
            # Get all users with alerts enabled (NO SUBSCRIPTION CHECKS)
            active_users = await database.get_all_active_users()
            
            if not active_users:
                logger.info("No active users with alerts enabled")
            else:
                logger.info(f"Checking alerts for {len(active_users)} users...")
                
                for user_id in active_users:
                    try:
                        await analyze_watchlist_for_user(bot, user_id)
                        # Small delay between users
                        await asyncio.sleep(2)
                    except Exception as e:
                        logger.error(f"Error processing alerts for user {user_id}: {e}")
                        continue
            
            # Wait for next interval
            logger.info(f"✅ Alert cycle complete. Waiting {ALERT_INTERVAL_HOURS} hour(s)...")
            await asyncio.sleep(ALERT_INTERVAL_HOURS * 3600)
            
        except Exception as e:
            logger.error(f"❌ Error in market alerts loop: {e}")
            # Wait 5 minutes before retrying on error
            await asyncio.sleep(300)


async def send_trending_alert(bot: Bot):
    """
    Send trending market opportunities to all users with alerts enabled.
    This is a separate function for general market trends (not watchlist-specific).
    """
    try:
        # Trending cryptos to analyze
        trending_crypto = ["BTC", "ETH", "SOL", "MATIC", "LINK", "AVAX"]
        
        # Get all active users (NO SUBSCRIPTION CHECKS)
        active_users = await database.get_all_active_users()
        
        if not active_users:
            return
        
        high_score_alerts = []
        
        # Analyze trending cryptos
        for symbol in trending_crypto:
            data = get_crypto_data(symbol)
            if data:
                score, risk_level, factors = score_crypto(data)
                if score >= ALERT_RISK_THRESHOLD:
                    high_score_alerts.append({
                        'ticker': symbol,
                        'score': score,
                        'data': data
                    })
        
        # Send alerts to users
        if high_score_alerts:
            for user_id in active_users:
                try:
                    alert_msg = "🔥 Trending Opportunities\n\n"
                    
                    for alert in high_score_alerts[:3]:  # Top 3 only
                        ticker = alert['ticker']
                        score = alert['score']
                        alert_msg += f"• {ticker} - Score: {score}/100\n"
                    
                    alert_msg += "\n💡 Tap 📈 Market Intelligence to analyze!"
                    
                    await bot.send_message(user_id, alert_msg, parse_mode="Markdown")
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error sending trending alert to {user_id}: {e}")
                    
    except Exception as e:
        logger.error(f"Error in send_trending_alert: {e}")