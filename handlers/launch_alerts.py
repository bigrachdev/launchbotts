"""
Launch alert system - CRYPTO ONLY
Sends AI-powered alerts before major crypto events.
"""

import asyncio
import logging
from aiogram import Router, Bot
from aiogram.types import CallbackQuery
from datetime import datetime
import database
from utils.ai_analysis import analyze_launch_event
from utils.sentiment_analyzer import sentiment_analyzer
from utils.event_tracker import event_tracker
from utils.data_fetcher import get_crypto_data
from keyboards import get_main_menu_keyboard
from config import LAUNCH_ALERT_DAYS_BEFORE, LAUNCH_CHECK_INTERVAL_HOURS

router = Router()
logger = logging.getLogger(__name__)


async def prepare_launch_data(event: dict) -> dict:
    """
    Gather all data needed for crypto launch analysis.
    
    Args:
        event: Event dictionary from database
    
    Returns:
        Comprehensive data dict for AI analysis
    """
    asset = event['asset']
    
    data = {
        'asset': asset,
        'asset_type': 'crypto',
        'event_type': event['event_type'],
        'event_date': event['event_date']
    }
    
    try:
        # Get market data
        crypto_data = get_crypto_data(asset)
        if crypto_data:
            data.update({
                'market_cap': crypto_data.get('marketCap', 0),
                'liquidity_usd': crypto_data.get('volume', 0),
                'price_change_7d': crypto_data.get('priceChange7d', 0),
                'community_members': crypto_data.get('communityScore', 0) * 1000,
                'team_transparency': 3,
                'audit_completed': True,  # Mock - would check from blockchain
                'tokenomics_rating': 3,
                'github_commits_30d': crypto_data.get('github_commits_4weeks', 0),
                'major_partnerships': 1
            })
        
        # Get sentiment data
        sentiment_data = sentiment_analyzer.analyze_asset_sentiment(asset, 'crypto')
        data.update(sentiment_data)
        
    except Exception as e:
        logger.error(f"Error preparing data for {asset}: {e}")
    
    return data


async def send_launch_alert(bot: Bot, user_id: int, event: dict, analysis: dict):
    """
    Send formatted launch alert to user.
    
    Args:
        bot: Bot instance
        user_id: User Telegram ID
        event: Event data
        analysis: AI analysis results
    """
    try:
        asset = event['asset']
        event_type = event['event_type'].replace('_', ' ').title()
        event_date = datetime.strptime(event['event_date'], '%Y-%m-%d').strftime('%b %d, %Y')
        description = event.get('description', f'{asset} {event_type}')
        
        # Build alert message
        alert_msg = (
            f"🚀 Upcoming Crypto Event: {asset}\n"
            f"{'='*40}\n\n"
            f"📅 {event_type}: {event_date}\n"
            f"📊 Risk Level: {analysis['risk_emoji']} {analysis['risk_level']}\n\n"
            f"💬 Summary: {analysis['summary']}\n\n"
            f"📈 Confidence: {analysis['confidence']}%\n\n"
            f"Risk Breakdown:\n"
            f"• Fundamentals: {analysis['scores']['fundamentals']:.1f}/5.0\n"
            f"• Technical: {analysis['scores']['technical']:.1f}/5.0\n"
            f"• Sentiment: {analysis['scores']['sentiment']:.1f}/5.0\n"
            f"• Event Timing: {analysis['scores']['event']:.1f}/5.0\n\n"
            f"💡 Suggestion: {analysis['suggestion']}\n\n"
            f"⚠️ *This is AI-generated analysis. Always DYOR.*"
        )
        
        await bot.send_message(
            user_id,
            alert_msg,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        
        logger.info(f"Sent launch alert for {asset} to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error sending alert to user {user_id}: {e}")


async def process_launch_alerts(bot: Bot):
    """
    Main launch alert processing system - CRYPTO ONLY
    Runs periodically to check for upcoming events and send alerts.
    """
    logger.info("🚀 Starting crypto launch alert system...")
    
    while True:
        try:
            # Step 1: Sync events from all users' watchlists
            all_watchlists = []
            active_users = await database.get_all_active_users()
            
            for user_id in active_users:
                watchlist = await database.get_watchlist(user_id)
                all_watchlists.extend(watchlist)
            
            if all_watchlists:
                await event_tracker.sync_watchlist_events(all_watchlists)
                logger.info(f"Synced events for {len(all_watchlists)} watchlist items")
            
            # Step 2: Get events that need alerts (X days before)
            events_to_alert = await event_tracker.get_events_for_alert(LAUNCH_ALERT_DAYS_BEFORE)
            
            if not events_to_alert:
                logger.info("No crypto events need alerts at this time")
            else:
                logger.info(f"Found {len(events_to_alert)} crypto events needing alerts")
                
                for event in events_to_alert:
                    try:
                        # Step 3: Prepare data for analysis
                        launch_data = await prepare_launch_data(event)
                        
                        # Step 4: Run AI analysis
                        analysis = analyze_launch_event('crypto', launch_data)
                        
                        # Step 5: Update event with analysis
                        await event_tracker.update_event_analysis(
                            event['id'],
                            analysis['final_score'],
                            analysis['risk_level'],
                            analysis['confidence']
                        )
                        
                        # Step 6: Find users watching this asset
                        asset = event['asset']
                        users_watching = []
                        
                        for user_id in active_users:
                            watchlist = await database.get_watchlist(user_id)
                            if any(item['ticker'] == asset for item in watchlist):
                                users_watching.append(user_id)
                        
                        # Step 7: Send alerts to all watching users
                        for user_id in users_watching:
                            await send_launch_alert(bot, user_id, event, analysis)
                            await asyncio.sleep(1)  # Rate limiting
                        
                        # Step 8: Mark event as notified
                        await event_tracker.mark_event_notified(event['id'])
                        
                        logger.info(f"Processed alert for {asset}, sent to {len(users_watching)} users")
                        
                    except Exception as e:
                        logger.error(f"Error processing event {event['id']}: {e}")
                        continue
            
            # Wait for next check
            logger.info(f"Launch alert check complete. Next check in {LAUNCH_CHECK_INTERVAL_HOURS} hours")
            await asyncio.sleep(LAUNCH_CHECK_INTERVAL_HOURS * 3600)
            
        except Exception as e:
            logger.error(f"Error in launch alert system: {e}")
            # Wait 1 hour on error
            await asyncio.sleep(3600)


# ============== MANUAL ALERT CHECK ==============
@router.callback_query(lambda c: c.data == "check_upcoming_events")
async def check_upcoming_events_manual(callback: CallbackQuery):
    """Manually check upcoming crypto events"""
    user_id = callback.from_user.id
    
    await callback.answer("🔍 Checking upcoming crypto events...", show_alert=False)
    
    # Get user's watchlist
    watchlist = await database.get_watchlist(user_id)
    
    if not watchlist:
        await callback.message.answer(
            "📋 No Watchlist\n\n"
            "Add cryptos to your watchlist to receive launch alerts!",
            parse_mode="Markdown"
        )
        return
    
    # Get upcoming events
    events = await event_tracker.get_upcoming_events(days_ahead=30)
    
    # Filter to user's watchlist
    user_assets = [item['ticker'] for item in watchlist]
    user_events = [e for e in events if e['asset'] in user_assets]
    
    if not user_events:
        await callback.message.answer(
            "📅 No Upcoming Events\n\n"
            "No scheduled crypto events found for your watchlist in the next 30 days.",
            parse_mode="Markdown"
        )
        return
    
    # Build events message
    msg = f"📅 Upcoming Crypto Events ({len(user_events)} found)\n" + "="*40 + "\n\n"
    
    for event in user_events[:10]:  # Show first 10
        asset = event['asset']
        event_type = event['event_type'].replace('_', ' ').title()
        event_date = datetime.strptime(event['event_date'], '%Y-%m-%d').strftime('%b %d')
        
        risk_emoji = '🟢' if event.get('risk_level') == 'Low Risk' else '🟡' if event.get('risk_level') == 'Medium Risk' else '🔴' if event.get('risk_level') else '⚪'
        
        msg += f"{risk_emoji} {asset} - {event_type}\n"
        msg += f"   📅 {event_date}\n"
        if event.get('risk_level'):
            msg += f"   Risk: {event['risk_level']} ({event.get('confidence', 0):.0f}%)\n"
        msg += "\n"
    
    msg += "\n🔔 You'll receive automatic alerts 3 days before each event!"
    
    await callback.message.answer(msg, parse_mode="Markdown")