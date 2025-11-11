"""
LaunchBot - AI-Powered Crypto & Meme Coin Analyzer
100% FREE - No subscriptions, no limits
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
import database

# Import handlers
from handlers import (
    start, 
    watchlist,  # NEW - Main feature now
    intelligence, 
    portfolio, 
    analytics, 
    launch_alerts,
    donations  # NEW - Donation support
)
from handlers.alerts import send_market_alerts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main bot entry point"""
    # Initialize database
    logger.info("🔧 Initializing database...")
    await database.init_db()
    logger.info("✅ Database initialized successfully")
    
    # Initialize bot and dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()
    
    # Register routers in order (IMPORTANT: Order matters!)
    dp.include_router(start.router)          # Welcome screen
    dp.include_router(watchlist.router)      # Main watchlist feature
    dp.include_router(intelligence.router)   # AI analysis
    dp.include_router(portfolio.router)      # Simple portfolio
    dp.include_router(analytics.router)      # Charts & stats
    dp.include_router(launch_alerts.router)  # Event tracking
    
    logger.info("🚀 Starting LaunchBot - FREE Crypto & Meme Coin Analyzer")
    logger.info("=" * 60)
    logger.info("✅ Watchlist system initialized (Main feature)")
    logger.info("✅ AI Market Intelligence system initialized")
    logger.info("✅ Portfolio tracking initialized (Simple version)")
    logger.info("✅ Analytics & Charts system initialized")
    logger.info("✅ Launch Alert system initialized")
    logger.info("💎 100% FREE - No payments, no limits!")
    logger.info("=" * 60)
    
    # Start background systems
    logger.info("🔄 Starting background tasks...")
    
    # Smart alerts system
    asyncio.create_task(send_market_alerts(bot))
    logger.info("✅ Smart alerts system started (every 2 hours)")
    
    # Launch alert processing
    asyncio.create_task(launch_alerts.process_launch_alerts(bot))
    logger.info("✅ Launch alert processing started")
    
    logger.info("=" * 60)
    logger.info("🤖 Bot is now running!")
    logger.info("📱 Users can start chatting at t.me/YourBotUsername")
    logger.info("=" * 60)
    
    # Start polling
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("👋 Bot stopped gracefully")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚠️  Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}", exc_info=True)