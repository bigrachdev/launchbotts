"""
Menu handler - Settings and other menu options
Watchlist moved to watchlist.py
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from datetime import datetime
import database
from keyboards import (
    get_main_menu_keyboard,
    get_settings_keyboard,
    get_language_keyboard,
    get_delete_confirm_keyboard,
    get_meme_coins_keyboard
)
from handlers.donations import get_donation_keyboard, DONATION_WALLET_USDT, SHOW_DONATION_MESSAGE

router = Router()


# ============== MEME COINS MENU ==============
@router.message(F.text == "🔥 Meme Coins")
async def meme_coins_handler(message: Message):
    """Display meme coin tracking menu"""
    user_id = message.from_user.id
    
    watchlist = await database.get_watchlist(user_id)
    meme_coins = [item for item in watchlist if item.get('is_meme_coin')]
    
    await message.answer(
        "🔥 Meme Coin Tracker\n\n"
        f"You're tracking {len(meme_coins)} meme coins\n\n"
        "⚠️ Remember: Meme coins are highly volatile!\n"
        "• Always DYOR (Do Your Own Research)\n"
        "• Only invest what you can afford to lose\n"
        "• Beware of rug pulls and scams\n"
        "• Check liquidity before buying\n\n"
        "What would you like to do?",
        reply_markup=get_meme_coins_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "my_meme_coins")
async def show_my_meme_coins(callback: CallbackQuery):
    """Show user's meme coins from watchlist"""
    user_id = callback.from_user.id
    watchlist = await database.get_watchlist(user_id)
    meme_coins = [item for item in watchlist if item.get('is_meme_coin')]
    
    if not meme_coins:
        await callback.message.edit_text(
            "🔥 Your Meme Coins\n\n"
            "You haven't tracked any meme coins yet!\n\n"
            "Add some using:\n"
            "• ➕ Track Meme Coin button below\n"
            "• Or add via 📋 My Watchlist",
            reply_markup=get_meme_coins_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    msg = "🔥 Your Meme Coins\n" + "="*30 + "\n\n"
    
    for coin in meme_coins:
        ticker = coin['ticker']
        added = datetime.fromisoformat(coin['created_at']).strftime('%m/%d')
        msg += f"• {ticker} (added {added})\n"
    
    msg += f"\nTotal: {len(meme_coins)} meme coins tracked\n\n"
    msg += "💡 Use 📈 Market Intelligence to analyze them!"
    
    await callback.message.edit_text(
        msg,
        reply_markup=get_meme_coins_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "add_meme_coin")
async def add_meme_coin_redirect(callback: CallbackQuery):
    """Redirect to add coin flow"""
    await callback.message.answer(
        "➕ Add Meme Coin\n\n"
        "Use the ➕ Add Coin button in the main menu,\n"
        "then select 🔥 Meme Coin when asked!\n\n"
        "Or tap 📋 My Watchlist → ➕ Add Coin",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "trending_meme_coins")
async def show_trending_meme_coins(callback: CallbackQuery):
    """Show trending meme coins (mock data for now)"""
    await callback.answer("🔄 Fetching trending meme coins...", show_alert=False)
    
    # This would integrate with CoinGecko trending API or DexScreener
    trending = [
        ("DOGE", "+5.2%"),
        ("SHIB", "+12.8%"),
        ("PEPE", "+8.4%"),
        ("BONK", "+15.3%"),
        ("FLOKI", "+3.7%")
    ]
    
    msg = "🔥 Trending Meme Coins (24h)\n" + "="*30 + "\n\n"
    
    for coin, change in trending:
        emoji = "🚀" if "+" in change else "📉"
        msg += f"{emoji} {coin} - {change}\n"
    
    msg += (
        f"\n💡 Tip: Tap ➕ Track Meme Coin to add any of these\n"
        f"to your watchlist for monitoring!\n\n"
        f"⚠️ Trending ≠ Safe. Always check liquidity!"
    )
    
    await callback.message.edit_text(
        msg,
        reply_markup=get_meme_coins_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "rug_pull_check")
async def rug_pull_check_info(callback: CallbackQuery):
    """Show rug pull detection info"""
    msg = (
        "⚠️ Rug Pull Detector\n\n"
        "Our AI checks for these red flags:\n\n"
        "🚨 Critical Risks:\n"
        "• Very low liquidity (<$50K)\n"
        "• Token age <24 hours\n"
        "• Heavy selling pressure\n"
        "• Unverified contracts\n\n"
        "⚠️ Warning Signs:\n"
        "• No liquidity lock\n"
        "• Concentrated holdings (>70%)\n"
        "• No audit\n"
        "• Abnormal volume spikes\n\n"
        "💡 How to use:\n"
        "Use 🔥 Analyze Meme Coin in Market Intelligence\n"
        "and we'll automatically check for rug pull risks!\n\n"
        "Remember: No tool is 100% accurate.\n"
        "Always DYOR before investing!"
    )
    
    await callback.message.edit_text(
        msg,
        reply_markup=get_meme_coins_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "liquidity_analysis")
async def liquidity_analysis_info(callback: CallbackQuery):
    """Show liquidity analysis info"""
    msg = (
        "💧 Liquidity Analysis\n\n"
        "Why liquidity matters:\n\n"
        "✅ Good Liquidity ($1M+):\n"
        "• Easy to buy/sell\n"
        "• Less price slippage\n"
        "• Lower manipulation risk\n\n"
        "⚠️ Low Liquidity (<$100K):\n"
        "• Hard to exit positions\n"
        "• High price impact\n"
        "• Rug pull risk\n\n"
        "🔍 What we check:\n"
        "• Total liquidity (USD)\n"
        "• Liquidity to market cap ratio\n"
        "• Liquidity lock status\n"
        "• Recent liquidity changes\n\n"
        "💡 Minimum recommended:\n"
        "$100K for small trades\n"
        "$500K for medium trades\n"
        "$1M+ for larger positions\n\n"
        "Use 🔥 Analyze Meme Coin to check!"
    )
    
    await callback.message.edit_text(
        msg,
        reply_markup=get_meme_coins_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ============== SETTINGS ==============
@router.message(F.text == "⚙️ Settings")
async def settings_handler(message: Message):
    """Display settings menu"""
    user = await database.get_user(message.from_user.id)
    language = user.get('language', 'en') if user else 'en'
    alerts = "✅ Enabled" if user.get('alerts_enabled', 0) else "❌ Disabled"
    
    watchlist = await database.get_watchlist(message.from_user.id)
    
    await message.answer(
        "⚙️ Settings\n\n"
        f"Your Account:\n"
        f"🔔 Alerts: {alerts}\n"
        f"🌐 Language: {language.upper()}\n"
        f"👤 Username: @{message.from_user.username or 'Not set'}\n"
        f"🆔 User ID: {message.from_user.id}\n"
        f"📊 Tracked Coins: {len(watchlist)}\n\n"
        "What would you like to configure?",
        reply_markup=get_settings_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "settings_language")
async def settings_language_callback(callback: CallbackQuery):
    """Show language selection"""
    await callback.message.edit_text(
        "🌐 Choose Your Language\n\n"
        "Select your preferred language:\n\n"
        "⚠️ Note: Full translations coming soon!\n"
        "Currently all messages are in English.",
        reply_markup=get_language_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lang_"))
async def language_selection_callback(callback: CallbackQuery):
    """Handle language selection"""
    lang_code = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    await database.update_user_language(user_id, lang_code)
    
    lang_names = {"en": "English", "es": "Español", "fr": "Français"}
    await callback.answer(f"✅ Language changed to {lang_names.get(lang_code, lang_code)}")
    
    await callback.message.edit_text(
        f"✅ Language updated to {lang_names.get(lang_code, lang_code)}\n\n"
        "⚠️ Note: Full translation support coming soon!\n"
        "For now, all messages remain in English.",
        reply_markup=get_settings_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "settings_delete")
async def settings_delete_callback(callback: CallbackQuery):
    """Show delete account confirmation"""
    await callback.message.edit_text(
        "🗑️ Delete Account\n\n"
        "⚠️ WARNING: This action cannot be undone!\n\n"
        "All your data will be permanently deleted:\n"
        "• Watchlist\n"
        "• Portfolio\n"
        "• Trade history\n"
        "• Analysis history\n"
        "• Settings\n\n"
        "Are you absolutely sure?",
        reply_markup=get_delete_confirm_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "confirm_delete")
async def confirm_delete_callback(callback: CallbackQuery):
    """Delete user account"""
    user_id = callback.from_user.id
    await database.delete_user(user_id)
    
    await callback.message.edit_text(
        "✅ Account Deleted\n\n"
        "Your account and all data have been permanently deleted.\n\n"
        "Thank you for using LaunchBot! 👋\n\n"
        "If you change your mind, send /start to create a new account.",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "settings_back")
async def settings_back_callback(callback: CallbackQuery):
    """Return to settings menu"""
    user = await database.get_user(callback.from_user.id)
    language = user.get('language', 'en') if user else 'en'
    alerts = "✅ Enabled" if user.get('alerts_enabled', 0) else "❌ Disabled"
    
    watchlist = await database.get_watchlist(callback.from_user.id)
    
    await callback.message.edit_text(
        "⚙️ Settings\n\n"
        f"Your Account:\n"
        f"🔔 Alerts: {alerts}\n"
        f"🌐 Language: {language.upper()}\n"
        f"👤 Username: @{callback.from_user.username or 'Not set'}\n"
        f"🆔 User ID: {callback.from_user.id}\n"
        f"📊 Tracked Coins: {len(watchlist)}\n\n"
        "What would you like to configure?",
        reply_markup=get_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "usage_stats")
async def usage_stats_callback(callback: CallbackQuery):
    """Show user usage statistics"""
    user_id = callback.from_user.id
    
    watchlist = await database.get_watchlist(user_id)
    portfolio = await database.get_user_portfolio(user_id)
    history = await database.get_analysis_history(user_id, limit=1000)
    trades = await database.get_trade_history(user_id, limit=1000)
    
    # Separate by type
    regular_coins = [c for c in watchlist if not c.get('is_meme_coin')]
    meme_coins = [c for c in watchlist if c.get('is_meme_coin')]
    
    await callback.message.edit_text(
        "📊 Your Usage Statistics\n\n"
        f"Watchlist:\n"
        f"💎 Regular Crypto: {len(regular_coins)}\n"
        f"🔥 Meme Coins: {len(meme_coins)}\n"
        f"Total: {len(watchlist)}\n\n"
        f"Activity:\n"
        f"💰 Portfolio: {len(portfolio)} positions\n"
        f"📈 Analyses: {len(history)} total\n"
        f"💱 Trades: {len(trades)} recorded\n\n"
        f"🎉 Keep tracking and analyzing!",
        reply_markup=get_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "alert_settings")
async def alert_settings_callback(callback: CallbackQuery):
    """Show alert settings"""
    user_id = callback.from_user.id
    alerts_enabled = await database.get_alerts_enabled(user_id)
    
    status = "✅ Enabled" if alerts_enabled else "❌ Disabled"
    
    await callback.message.edit_text(
        "🔔 Alert Settings\n\n"
        f"Current Status: {status}\n\n"
        "What you'll receive:\n"
        "• High-score opportunities (70+)\n"
        "• Watchlist updates\n"
        "• Launch event notifications\n"
        "• Rug pull warnings\n\n"
        "Frequency: Every 2 hours\n\n"
        "💡 Enable/disable alerts via:\n"
        "📈 Market Intelligence → 🔔 Smart Alerts",
        reply_markup=get_settings_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_callback(callback: CallbackQuery):
    """Return to main menu"""
    await callback.message.delete()
    await callback.message.answer(
        "🏠 Main Menu",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()