"""
Market Intelligence handler for AI-powered crypto analysis.
CRYPTO ONLY - Stock support removed
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import asyncio
import database
from keyboards import get_intelligence_keyboard, get_alerts_toggle_keyboard, get_main_menu_keyboard
from utils.data_fetcher import get_crypto_data, format_large_number, get_price_change_emoji
from utils.dex_fetcher import get_dex_data, detect_rug_pull_signals, format_dex_data
from utils.ai_model import score_crypto, get_recommendation

router = Router()


async def _fetch_crypto_data(symbol: str):
    """Run blocking data fetch off the event loop."""
    return await asyncio.to_thread(get_crypto_data, symbol)


async def _fetch_dex_data(symbol: str):
    """Run blocking DEX fetch off the event loop."""
    return await asyncio.to_thread(get_dex_data, symbol)


# Define states for analysis flow
class AnalysisStates(StatesGroup):
    waiting_for_crypto_symbol = State()
    waiting_for_meme_coin_symbol = State()


# ============== MARKET INTELLIGENCE MENU ==============
@router.message(F.text == "📈 Market Intelligence")
@router.callback_query(F.data == "market_intelligence")
async def intelligence_menu(update: Message | CallbackQuery):
    """Display Market Intelligence menu"""
    if isinstance(update, CallbackQuery):
        user_id = update.from_user.id
        message = update.message
        await update.answer()
    else:
        user_id = update.from_user.id
        message = update
    
    alerts_enabled = await database.get_alerts_enabled(user_id)
    alerts_status = "✅ Enabled" if alerts_enabled else "❌ Disabled"
    
    msg = (
        "📈 Market Intelligence\n\n"
        "AI-powered crypto analysis at your fingertips!\n\n"
        "Features:\n"
        "💰 Analyze Crypto - Get instant risk scores\n"
        "🔥 Analyze Meme Coin - Special meme coin analysis\n"
        "📜 History - View your past analyses\n"
        f"🔔 Smart Alerts - {alerts_status}\n\n"
        "Choose an option:"
    )
    
    if isinstance(update, CallbackQuery):
        await message.edit_text(msg, reply_markup=get_intelligence_keyboard(), parse_mode="Markdown")
    else:
        await message.answer(msg, reply_markup=get_intelligence_keyboard(), parse_mode="Markdown")


# ============== ANALYZE CRYPTO ==============
@router.callback_query(F.data == "analyze_crypto")
async def analyze_crypto_prompt(callback: CallbackQuery, state: FSMContext):
    """Prompt user to enter crypto symbol"""
    await state.set_state(AnalysisStates.waiting_for_crypto_symbol)
    await callback.message.answer(
        "💰 Analyze Cryptocurrency\n\n"
        "Enter the crypto symbol or name:\n"
        "Examples: BTC, ETH, SOL, MATIC, LINK\n\n"
        "Send /cancel to abort.",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(AnalysisStates.waiting_for_crypto_symbol)
async def process_crypto_analysis(message: Message, state: FSMContext):
    """Process crypto symbol and perform analysis"""
    symbol = message.text.strip().upper()
    
    # Show processing message
    processing_msg = await message.answer("🔄 Analyzing... Please wait.")
    
    # Fetch data from CoinGecko
    data = await _fetch_crypto_data(symbol)
    
    if not data:
        await processing_msg.edit_text(
            f"❌ Could not find data for {symbol}\n\n"
            "Please check the symbol and try again.\n"
            "💡 Tip: Try using common symbols like BTC, ETH, SOL",
            parse_mode="Markdown"
        )
        await state.clear()
        return
    
    # Calculate risk score
    score, risk_level, factors = score_crypto(data)
    recommendation = get_recommendation(score, "crypto")
    
    # Price changes
    current_price = data.get("price", 0)
    price_change_24h = data.get("priceChange24h", 0)
    price_change_7d = data.get("priceChange7d", 0)
    price_emoji = get_price_change_emoji(price_change_24h)
    
    # Build analysis message
    factors_text = "\n".join([f"  • {factor}" for factor in factors[:5]])
    
    analysis_msg = (
        f"💰 {data['name']} ({symbol})\n"
        f"{'='*30}\n\n"
        f"AI Risk Score: {score}/100\n"
        f"Risk Level: {risk_level}\n\n"
        f"Market Data:\n"
        f"Price: ${current_price:,.8f} {price_emoji}\n"
        f"24h Change: {price_change_24h:+.2f}%\n"
        f"7d Change: {price_change_7d:+.2f}%\n"
        f"Market Cap: {format_large_number(data['marketCap'])}\n"
        f"24h Volume: {format_large_number(data['volume'])}\n\n"
        f"Community & Development:\n"
        f"Community Score: {data['communityScore']:.0f}/100\n"
        f"Developer Score: {data['developerScore']:.0f}/100\n\n"
        f"Key Factors:\n{factors_text}\n\n"
        f"💡 Recommendation:\n{recommendation}\n\n"
        f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"
    )
    
    # Save to history
    await database.save_analysis(
        message.from_user.id,
        symbol,
        'crypto',
        score,
        {
            'name': data['name'],
            'price': current_price,
            'risk_level': risk_level,
            'factors': factors
        }
    )
    
    # Send analysis
    await processing_msg.edit_text(analysis_msg, parse_mode="Markdown")
    await state.clear()


# ============== ANALYZE MEME COIN ==============
@router.callback_query(F.data == "analyze_meme_coin")
async def analyze_meme_coin_prompt(callback: CallbackQuery, state: FSMContext):
    """Prompt user to enter meme coin symbol"""
    await state.set_state(AnalysisStates.waiting_for_meme_coin_symbol)
    await callback.message.answer(
        "🔥 Analyze Meme Coin\n\n"
        "Enter the meme coin symbol:\n"
        "Examples: DOGE, SHIB, PEPE, FLOKI, BONK\n\n"
        "⚠️ Warning: Meme coins are highly volatile!\n\n"
        "Send /cancel to abort.",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(AnalysisStates.waiting_for_meme_coin_symbol)
async def process_meme_coin_analysis(message: Message, state: FSMContext):
    """Process meme coin with enhanced analysis"""
    symbol = message.text.strip().upper()
    
    # Show processing message
    processing_msg = await message.answer("🔄 Analyzing meme coin... Checking for rug pulls...")
    
    # Try DexScreener first (better for meme coins)
    dex_data = await _fetch_dex_data(symbol)
    
    # Also get CoinGecko data
    cg_data = await _fetch_crypto_data(symbol)
    
    if not dex_data and not cg_data:
        await processing_msg.edit_text(
            f"❌ Could not find data for {symbol}\n\n"
            "This could mean:\n"
            "• Coin doesn't exist\n"
            "• Not listed on major DEXs\n"
            "• Very new/unlisted token\n\n"
            "💡 Tip: Check the contract address",
            parse_mode="Markdown"
        )
        await state.clear()
        return
    
    # Build comprehensive analysis
    analysis_msg = f"🔥 {symbol} Meme Coin Analysis\n" + "="*30 + "\n\n"
    
    # CoinGecko data (if available)
    if cg_data:
        score, risk_level, factors = score_crypto(cg_data)
        
        price = cg_data.get('price', 0)
        change_24h = cg_data.get('priceChange24h', 0)
        market_cap = cg_data.get('marketCap', 0)
        volume = cg_data.get('volume', 0)
        
        emoji = get_price_change_emoji(change_24h)
        
        analysis_msg += (
            f"AI Risk Score: {score}/100 {risk_level}\n\n"
            f"Price: ${price:,.8f} {emoji}\n"
            f"24h Change: {change_24h:+.2f}%\n"
            f"Market Cap: {format_large_number(market_cap)}\n"
            f"Volume: {format_large_number(volume)}\n\n"
        )
    
    # DexScreener data (if available)
    if dex_data:
        liquidity = dex_data.get('liquidity_usd', 0)
        age_hours = dex_data.get('age_hours', 0)
        buy_ratio = dex_data.get('buy_sell_ratio_1h', 0.5)
        
        analysis_msg += (
            f"DEX Data:\n"
            f"💧 Liquidity: ${liquidity:,.0f}\n"
            f"⏰ Age: {age_hours:.1f} hours\n"
            f"📊 Buy/Sell (1h): {buy_ratio*100:.0f}% / {(1-buy_ratio)*100:.0f}%\n"
            f"🔗 Chain: {dex_data.get('chain', 'Unknown')}\n\n"
        )
        
        # RUG PULL DETECTION
        rug_check = detect_rug_pull_signals(dex_data)
        
        analysis_msg += (
            f"🚨 Rug Pull Risk Assessment:\n"
            f"{rug_check['risk_level']}\n"
            f"Risk Score: {rug_check['risk_score']}/100\n\n"
        )
        
        if rug_check['signals']:
            analysis_msg += "Warning Signals:\n"
            for signal in rug_check['signals']:
                analysis_msg += f"{signal}\n"
            analysis_msg += "\n"
    
    # General meme coin warning
    analysis_msg += (
        f"⚠️ MEME COIN WARNING:\n"
        f"• Extremely high volatility\n"
        f"• Price driven by hype & sentiment\n"
        f"• High risk of rug pulls\n"
        f"• Only invest what you can lose\n"
        f"• Always DYOR (Do Your Own Research)\n\n"
        f"📅 Analysis: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"
    )
    
    # Save to history
    await database.save_analysis(
        message.from_user.id,
        symbol,
        'crypto',
        score if cg_data else 50,
        {
            'name': symbol,
            'price': price if cg_data else dex_data.get('price_usd', 0),
            'risk_level': risk_level if cg_data else 'HIGH RISK',
            'is_meme': True,
            'rug_pull_risk': rug_check['risk_score'] if dex_data else 'Unknown'
        }
    )
    
    # Send analysis
    await processing_msg.edit_text(analysis_msg, parse_mode="Markdown")
    await state.clear()


# ============== ANALYSIS HISTORY ==============
@router.callback_query(F.data == "view_history")
async def view_analysis_history(callback: CallbackQuery):
    """View user's analysis history"""
    user_id = callback.from_user.id
    history = await database.get_analysis_history(user_id, limit=15)
    
    if not history:
        await callback.message.edit_text(
            "📜 Analysis History\n\n"
            "You haven't performed any analyses yet.\n\n"
            "Use 💰 Analyze Crypto or 🔥 Analyze Meme Coin to get started!",
            reply_markup=get_intelligence_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    # Build history message
    history_text = "📜 Your Recent Analyses\n" + "="*30 + "\n\n"
    
    for item in history[:15]:
        date = datetime.fromisoformat(item['created_at']).strftime('%m/%d %H:%M')
        ticker = item['ticker']
        score = item['risk_score']
        
        if score >= 75:
            emoji = "🟢"
        elif score >= 50:
            emoji = "🟡"
        elif score >= 30:
            emoji = "🟠"
        else:
            emoji = "🔴"
        
        history_text += f"{emoji} {ticker} - Score: {score}/100\n"
        history_text += f"   📅 {date}\n\n"
    
    history_text += "💡 Tap an option below to analyze more!"
    
    await callback.message.edit_text(
        history_text,
        reply_markup=get_intelligence_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ============== SMART ALERTS ==============
@router.callback_query(F.data == "toggle_alerts")
async def toggle_alerts_menu(callback: CallbackQuery):
    """Show alerts toggle menu"""
    user_id = callback.from_user.id
    alerts_enabled = await database.get_alerts_enabled(user_id)
    
    status_text = "enabled" if alerts_enabled else "disabled"
    status_emoji = "✅" if alerts_enabled else "❌"
    
    await callback.message.edit_text(
        f"🔔 Smart Alerts\n\n"
        f"Status: {status_emoji} Currently {status_text}\n\n"
        f"When enabled, you'll receive:\n"
        f"• High-score opportunities (70+ risk score)\n"
        f"• Updates for your watchlist\n"
        f"• Market trend alerts\n"
        f"• Launch event notifications\n\n"
        f"Alerts are sent every 2 hours.",
        reply_markup=get_alerts_toggle_keyboard(alerts_enabled),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "alert_frequency")
async def alert_frequency_placeholder(callback: CallbackQuery):
    """Temporary handler for alert frequency settings button."""
    await callback.answer("Alert frequency customization is coming soon.", show_alert=True)


@router.callback_query(F.data == "change_min_score")
async def change_min_score_placeholder(callback: CallbackQuery):
    """Temporary handler for min score settings button."""
    await callback.answer("Minimum score customization is coming soon.", show_alert=True)


@router.callback_query(F.data == "notification_times")
async def notification_times_placeholder(callback: CallbackQuery):
    """Temporary handler for notification time settings button."""
    await callback.answer("Notification schedule customization is coming soon.", show_alert=True)


@router.callback_query(F.data == "enable_alerts")
async def enable_alerts(callback: CallbackQuery):
    """Enable smart alerts for user"""
    user_id = callback.from_user.id
    await database.toggle_alerts(user_id, True)
    
    await callback.answer("✅ Smart Alerts Enabled!", show_alert=True)
    await callback.message.edit_text(
        "✅ Smart Alerts Enabled!\n\n"
        "You'll now receive:\n"
        "• Market intelligence updates every 2 hours\n"
        "• High-score opportunities (70+)\n"
        "• Watchlist updates\n"
        "• Launch event alerts\n\n"
        "You can disable them anytime from this menu.",
        reply_markup=get_intelligence_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "disable_alerts")
async def disable_alerts(callback: CallbackQuery):
    """Disable smart alerts for user"""
    user_id = callback.from_user.id
    await database.toggle_alerts(user_id, False)
    
    await callback.answer("🔕 Smart Alerts Disabled", show_alert=True)
    await callback.message.edit_text(
        "🔕 Smart Alerts Disabled\n\n"
        "You won't receive automatic market updates.\n\n"
        "You can re-enable them anytime!",
        reply_markup=get_intelligence_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "intelligence_menu")
async def back_to_intelligence(callback: CallbackQuery):
    """Return to intelligence menu"""
    await intelligence_menu(callback)


# ============== CANCEL ==============
@router.message(F.text == "/cancel")
async def cancel_analysis(message: Message, state: FSMContext):
    """Cancel analysis"""
    await state.clear()
    await message.answer(
        "❌ Analysis cancelled.",
        reply_markup=get_main_menu_keyboard()
    )
