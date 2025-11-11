"""
Telegram keyboards for LaunchBot
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Main menu keyboard - crypto/meme coin focused"""
    keyboard = [
        [KeyboardButton(text="📋 My Watchlist"), KeyboardButton(text="➕ Add Coin")],
        [KeyboardButton(text="🔥 Meme Coins"), KeyboardButton(text="📈 Market Intelligence")],
        [KeyboardButton(text="💰 Portfolio"), KeyboardButton(text="📊 Analytics")],
        [KeyboardButton(text="⚙️ Settings"), KeyboardButton(text="💙 Support Us")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_watchlist_keyboard(watchlist: list) -> InlineKeyboardMarkup:
    """Keyboard for empty watchlist"""
    keyboard = [
        [InlineKeyboardButton(text="➕ Add Your First Coin", callback_data="add_coin")],
        [InlineKeyboardButton(text="🔥 Browse Meme Coins", callback_data="browse_meme_coins")],
        [InlineKeyboardButton(text="📈 Market Intelligence", callback_data="market_intelligence")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_watchlist_actions_keyboard(tickers: list) -> InlineKeyboardMarkup:
    """Keyboard for watchlist with coins"""
    keyboard = []
    
    # Show up to 10 coins with view/remove buttons
    for ticker in tickers[:10]:
        keyboard.append([
            InlineKeyboardButton(
                text=f"📊 {ticker}",
                callback_data=f"view_coin:{ticker}"
            ),
            InlineKeyboardButton(
                text="🗑️",
                callback_data=f"remove_coin:{ticker}"
            )
        ])
    
    # Action buttons
    keyboard.append([
        InlineKeyboardButton(text="➕ Add More", callback_data="add_coin"),
        InlineKeyboardButton(text="🔄 Refresh", callback_data="refresh_watchlist")
    ])
    
    keyboard.append([
        InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_to_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_coin_type_keyboard() -> InlineKeyboardMarkup:
    """Keyboard to choose coin type"""
    keyboard = [
        [InlineKeyboardButton(text="💎 Regular Crypto", callback_data="coin_type_regular")],
        [InlineKeyboardButton(text="🔥 Meme Coin", callback_data="coin_type_meme")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_intelligence_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for Market Intelligence menu"""
    keyboard = [
        [InlineKeyboardButton(text="💰 Analyze Crypto", callback_data="analyze_crypto")],
        [InlineKeyboardButton(text="🔥 Analyze Meme Coin", callback_data="analyze_meme_coin")],
        [InlineKeyboardButton(text="📜 Analysis History", callback_data="view_history")],
        [InlineKeyboardButton(text="🔔 Smart Alerts", callback_data="toggle_alerts")],
        [InlineKeyboardButton(text="🚀 Upcoming Events", callback_data="check_upcoming_events")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_meme_coins_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for meme coin tracking"""
    keyboard = [
        [InlineKeyboardButton(text="🔥 Trending Meme Coins", callback_data="trending_meme_coins")],
        [InlineKeyboardButton(text="➕ Track Meme Coin", callback_data="add_meme_coin")],
        [InlineKeyboardButton(text="📊 My Meme Coins", callback_data="my_meme_coins")],
        [InlineKeyboardButton(text="⚠️ Rug Pull Detector", callback_data="rug_pull_check")],
        [InlineKeyboardButton(text="💧 Liquidity Analysis", callback_data="liquidity_analysis")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_portfolio_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for portfolio management (simple version)"""
    keyboard = [
        [InlineKeyboardButton(text="📊 View Portfolio", callback_data="view_portfolio")],
        [InlineKeyboardButton(text="➕ Add Trade", callback_data="add_trade")],
        [InlineKeyboardButton(text="📜 Trade History", callback_data="view_trades")],
        [InlineKeyboardButton(text="🔄 Refresh Prices", callback_data="refresh_prices")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_analytics_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for analytics options"""
    keyboard = [
        [InlineKeyboardButton(text="📊 Performance", callback_data="analytics_performance")],
        [InlineKeyboardButton(text="📈 P/L Chart", callback_data="analytics_pnl_chart")],
        [InlineKeyboardButton(text="🥧 Composition", callback_data="analytics_composition")],
        [InlineKeyboardButton(text="🎯 Win Rate", callback_data="analytics_winrate")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for settings options"""
    keyboard = [
        [InlineKeyboardButton(text="🔔 Alert Settings", callback_data="alert_settings")],
        [InlineKeyboardButton(text="🌐 Language", callback_data="settings_language")],
        [InlineKeyboardButton(text="📊 Usage Stats", callback_data="usage_stats")],
        [InlineKeyboardButton(text="🗑️ Delete Account", callback_data="settings_delete")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for language selection"""
    keyboard = [
        [InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en")],
        [InlineKeyboardButton(text="🇪🇸 Español", callback_data="lang_es")],
        [InlineKeyboardButton(text="🇫🇷 Français", callback_data="lang_fr")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="settings_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_delete_confirm_keyboard() -> InlineKeyboardMarkup:
    """Keyboard to confirm account deletion"""
    keyboard = [
        [InlineKeyboardButton(text="✅ Yes, Delete My Account", callback_data="confirm_delete")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="settings_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_alerts_toggle_keyboard(enabled: bool) -> InlineKeyboardMarkup:
    """Keyboard for toggling alerts"""
    action_text = "🔕 Disable Alerts" if enabled else "🔔 Enable Alerts"
    action_callback = "disable_alerts" if enabled else "enable_alerts"
    
    keyboard = [
        [InlineKeyboardButton(text=action_text, callback_data=action_callback)],
        [InlineKeyboardButton(text="⚙️ Alert Settings", callback_data="alert_frequency")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="intelligence_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_rug_pull_check_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for rug pull checker"""
    keyboard = [
        [InlineKeyboardButton(text="🔍 Check Another Coin", callback_data="rug_pull_check")],
        [InlineKeyboardButton(text="📋 Back to Watchlist", callback_data="back_to_watchlist")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_alert_settings_keyboard(current_min_score: int) -> InlineKeyboardMarkup:
    """Keyboard for alert settings"""
    keyboard = [
        [InlineKeyboardButton(text=f"📊 Min Score: {current_min_score}", callback_data="change_min_score")],
        [InlineKeyboardButton(text="🔔 Notification Times", callback_data="notification_times")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="intelligence_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)