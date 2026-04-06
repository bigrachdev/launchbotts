"""
Watchlist handler - Track crypto & meme coins
Replaces portfolio as the main tracking feature
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import asyncio
import database
from keyboards import (
    get_main_menu_keyboard,
    get_watchlist_keyboard,
    get_watchlist_actions_keyboard,
    get_coin_type_keyboard,
    get_meme_coins_keyboard
)
from utils.data_fetcher import get_crypto_data, format_large_number, get_price_change_emoji
from utils.dex_fetcher import get_dex_data, detect_rug_pull_signals

router = Router()


async def _fetch_crypto_data(symbol: str):
    """Run blocking data fetch off the event loop."""
    return await asyncio.to_thread(get_crypto_data, symbol)


async def _fetch_dex_data(symbol: str):
    """Run blocking DEX fetch off the event loop."""
    return await asyncio.to_thread(get_dex_data, symbol)


async def _detect_rug_pull(dex_data: dict):
    """Run blocking risk check off the event loop."""
    return await asyncio.to_thread(detect_rug_pull_signals, dex_data)


# ============== FSM STATES ==============
class WatchlistStates(StatesGroup):
    waiting_for_ticker = State()
    waiting_for_coin_type = State()
    waiting_for_notes = State()


# ============== MY WATCHLIST ==============
@router.message(F.text == "📋 My Watchlist")
async def show_watchlist(message: Message):
    """Display user's complete watchlist"""
    user_id = message.from_user.id
    watchlist = await database.get_watchlist(user_id)
    
    if not watchlist:
        await message.answer(
            "📋 Your Watchlist\n\n"
            "Your watchlist is empty!\n\n"
            "Add some coins to start tracking:\n"
            "• Tap ➕ Add Coin below\n"
            "• Or use /add command\n\n"
            "💡 Track both regular cryptos and meme coins!",
            reply_markup=get_watchlist_keyboard(watchlist),
            parse_mode="Markdown"
        )
        return
    
    # Separate by type
    regular_coins = [c for c in watchlist if not c.get('is_meme_coin')]
    meme_coins = [c for c in watchlist if c.get('is_meme_coin')]
    
    msg = "📋 Your Watchlist\n"
    msg += "=" * 30 + "\n\n"
    
    # Regular Cryptos
    if regular_coins:
        msg += "💎 Regular Crypto (" + str(len(regular_coins)) + "):\n"
        for coin in regular_coins:
            ticker = coin['ticker']
            added = datetime.fromisoformat(coin['created_at']).strftime('%m/%d')
            notes = f" - {coin['notes']}" if coin.get('notes') else ""
            msg += f"• {ticker} (added {added}){notes}\n"
        msg += "\n"
    
    # Meme Coins
    if meme_coins:
        msg += "🔥 Meme Coins (" + str(len(meme_coins)) + "):\n"
        for coin in meme_coins:
            ticker = coin['ticker']
            added = datetime.fromisoformat(coin['created_at']).strftime('%m/%d')
            notes = f" - {coin['notes']}" if coin.get('notes') else ""
            msg += f"• {ticker} (added {added}){notes}\n"
        msg += "\n"
    
    msg += f"Total: {len(watchlist)} coins tracked\n\n"
    msg += "💡 Tap a coin below to view details or remove"
    
    await message.answer(
        msg,
        reply_markup=get_watchlist_actions_keyboard([c['ticker'] for c in watchlist]),
        parse_mode="Markdown"
    )


# ============== ADD COIN ==============
@router.message(F.text == "➕ Add Coin")
@router.callback_query(F.data == "add_coin")
async def add_coin_start(update: Message | CallbackQuery, state: FSMContext):
    """Start add coin flow"""
    await state.set_state(WatchlistStates.waiting_for_ticker)
    
    msg = (
        "➕ Add Coin to Watchlist\n\n"
        "Enter the crypto symbol or name:\n\n"
        "Examples:\n"
        "• BTC, ETH, SOL (regular crypto)\n"
        "• DOGE, SHIB, PEPE (meme coins)\n"
        "• Any token symbol\n\n"
        "Send /cancel to abort."
    )
    
    if isinstance(update, CallbackQuery):
        await update.message.answer(msg, parse_mode="Markdown")
        await update.answer()
    else:
        await update.answer(msg, parse_mode="Markdown")


@router.message(WatchlistStates.waiting_for_ticker)
async def process_ticker_input(message: Message, state: FSMContext):
    """Process ticker and ask for coin type"""
    ticker = message.text.strip().upper()
    
    # Validation
    if len(ticker) > 20 or not ticker.replace('-', '').isalnum():
        await message.answer(
            "❌ Invalid ticker format.\n\n"
            "Please enter a valid crypto symbol (letters, numbers, hyphens only)."
        )
        return
    
    # Check if already in watchlist
    watchlist = await database.get_watchlist(message.from_user.id)
    if any(c['ticker'] == ticker for c in watchlist):
        await message.answer(
            f"⚠️ {ticker} is already in your watchlist!\n\n"
            "Try adding a different coin.",
            parse_mode="Markdown"
        )
        await state.clear()
        return
    
    # Save ticker and ask for type
    await state.update_data(ticker=ticker)
    await state.set_state(WatchlistStates.waiting_for_coin_type)
    
    await message.answer(
        f"{ticker} - What type of coin is this?",
        reply_markup=get_coin_type_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("coin_type_"))
async def process_coin_type(callback: CallbackQuery, state: FSMContext):
    """Process coin type selection"""
    coin_type = callback.data.split("_")[2]  # regular or meme
    is_meme = (coin_type == "meme")
    
    data = await state.get_data()
    ticker = data['ticker']
    
    # Try to fetch current price
    processing = await callback.message.answer("🔍 Fetching data...")
    
    current_price = 0
    try:
        if is_meme:
            # Try DexScreener for meme coins
            dex_data = await _fetch_dex_data(ticker)
            if dex_data:
                current_price = dex_data.get('price_usd', 0)
        
        # Fallback to CoinGecko
        if current_price == 0:
            crypto_data = await _fetch_crypto_data(ticker)
            if crypto_data:
                current_price = crypto_data.get('price', 0)
    except Exception as e:
        pass
    
    # Add to database
    user_id = callback.from_user.id
    success = await database.add_crypto(user_id, ticker, is_meme)
    
    await processing.delete()
    
    if success:
        coin_emoji = "🔥" if is_meme else "💎"
        coin_label = "Meme Coin" if is_meme else "Crypto"
        
        msg = (
            f"✅ {ticker} {coin_emoji} added to watchlist!\n\n"
            f"Type: {coin_label}\n"
        )
        
        if current_price > 0:
            msg += f"Current Price: ${current_price:,.8f}\n"
        
        msg += (
            f"\n💡 Tips:\n"
            f"• Use 📋 My Watchlist to view all coins\n"
            f"• Get AI analysis via 📈 Market Intelligence\n"
            f"• Enable 🔔 Smart Alerts for updates"
        )
        
        await callback.message.edit_text(msg, parse_mode="Markdown")
        
        # Show main menu after 2 seconds
        await callback.message.answer(
            "What would you like to do next?",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.message.edit_text(
            f"❌ Failed to add {ticker}\n\n"
            "This might happen if:\n"
            "• Coin is already in your watchlist\n"
            "• Database error occurred\n\n"
            "Please try again.",
            parse_mode="Markdown"
        )
    
    await state.clear()
    await callback.answer()


# ============== VIEW COIN DETAILS ==============
@router.callback_query(F.data.startswith("view_coin:"))
async def view_coin_details(callback: CallbackQuery):
    """Show detailed info about a coin"""
    ticker = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    # Get from watchlist
    watchlist = await database.get_watchlist(user_id)
    coin = next((c for c in watchlist if c['ticker'] == ticker), None)
    
    if not coin:
        await callback.answer("❌ Coin not found", show_alert=True)
        return
    
    await callback.answer("📊 Fetching data...")
    
    is_meme = coin.get('is_meme_coin', False)
    
    # Fetch current data
    msg = f"📊 {ticker} Details\n" + "=" * 30 + "\n\n"
    
    try:
        # Try CoinGecko first
        data = await _fetch_crypto_data(ticker)
        
        if data:
            price = data.get('price', 0)
            change_24h = data.get('priceChange24h', 0)
            market_cap = data.get('marketCap', 0)
            volume = data.get('volume', 0)
            
            emoji = get_price_change_emoji(change_24h)
            
            msg += f"Price: ${price:,.8f} {emoji}\n"
            msg += f"24h Change: {change_24h:+.2f}%\n"
            msg += f"Market Cap: {format_large_number(market_cap)}\n"
            msg += f"24h Volume: {format_large_number(volume)}\n"
            msg += f"Type: {'🔥 Meme Coin' if is_meme else '💎 Crypto'}\n\n"
        
        # If meme coin, get DexScreener data
        if is_meme:
            dex_data = await _fetch_dex_data(ticker)
            if dex_data:
                msg += "DEX Data:\n"
                msg += f"• Liquidity: ${dex_data.get('liquidity_usd', 0):,.0f}\n"
                msg += f"• Age: {dex_data.get('age_hours', 0):.1f} hours\n"
                msg += f"• Chain: {dex_data.get('chain', 'Unknown')}\n\n"
                
                # Rug pull check
                rug_check = await _detect_rug_pull(dex_data)
                msg += f"Safety Check:\n{rug_check['risk_level']}\n"
                if rug_check['signals']:
                    msg += "Signals:\n"
                    for signal in rug_check['signals'][:3]:
                        msg += f"• {signal}\n"
                msg += "\n"
        
        # Watchlist info
        added_date = datetime.fromisoformat(coin['created_at']).strftime('%B %d, %Y')
        msg += f"Added: {added_date}\n"
        
        if coin.get('notes'):
            msg += f"Notes: {coin['notes']}\n"
        
        msg += (
            f"\nActions:\n"
            f"• Tap 🗑️ Remove to delete from watchlist\n"
            f"• Use 📈 Market Intelligence for AI analysis"
        )
        
    except Exception as e:
        msg += f"⚠️ Could not fetch current data\n\n"
        msg += f"Type: {'🔥 Meme Coin' if is_meme else '💎 Crypto'}\n"
        msg += f"Added: {datetime.fromisoformat(coin['created_at']).strftime('%B %d, %Y')}\n"
    
    await callback.message.edit_text(
        msg,
        reply_markup=get_watchlist_actions_keyboard([ticker]),
        parse_mode="Markdown"
    )


# ============== REMOVE COIN ==============
@router.callback_query(F.data.startswith("remove_coin:"))
async def remove_coin(callback: CallbackQuery):
    """Remove coin from watchlist"""
    ticker = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    success = await database.remove_crypto(user_id, ticker)
    
    if success:
        await callback.answer(f"✅ {ticker} removed from watchlist", show_alert=True)
        
        # Refresh watchlist display
        watchlist = await database.get_watchlist(user_id)
        
        if not watchlist:
            await callback.message.edit_text(
                "📋 Your Watchlist\n\n"
                "Your watchlist is now empty!\n\n"
                "Add some coins to start tracking.",
                reply_markup=get_watchlist_keyboard([]),
                parse_mode="Markdown"
            )
        else:
            # Show updated list
            regular_coins = [c for c in watchlist if not c.get('is_meme_coin')]
            meme_coins = [c for c in watchlist if c.get('is_meme_coin')]
            
            msg = "📋 Your Watchlist\n" + "=" * 30 + "\n\n"
            
            if regular_coins:
                msg += f"💎 Regular Crypto ({len(regular_coins)}):\n"
                for coin in regular_coins:
                    msg += f"• {coin['ticker']}\n"
                msg += "\n"
            
            if meme_coins:
                msg += f"🔥 Meme Coins ({len(meme_coins)}):\n"
                for coin in meme_coins:
                    msg += f"• {coin['ticker']}\n"
                msg += "\n"
            
            msg += f"Total: {len(watchlist)} coins"
            
            await callback.message.edit_text(
                msg,
                reply_markup=get_watchlist_actions_keyboard([c['ticker'] for c in watchlist]),
                parse_mode="Markdown"
            )
    else:
        await callback.answer("❌ Failed to remove coin", show_alert=True)


# ============== REFRESH WATCHLIST ==============
@router.callback_query(F.data == "refresh_watchlist")
async def refresh_watchlist(callback: CallbackQuery):
    """Refresh all prices in watchlist"""
    user_id = callback.from_user.id
    watchlist = await database.get_watchlist(user_id)
    
    if not watchlist:
        await callback.answer("No coins to refresh", show_alert=True)
        return
    
    await callback.answer("🔄 Refreshing prices...", show_alert=False)
    
    updated_count = 0
    
    for coin in watchlist:
        ticker = coin['ticker']
        try:
            data = await _fetch_crypto_data(ticker)
            if data and data.get('price', 0) > 0:
                # Could store updated price in watchlist if needed
                updated_count += 1
        except Exception:
            continue
    
    await callback.answer(
        f"✅ Refreshed {updated_count}/{len(watchlist)} coins",
        show_alert=True
    )


# ============== CANCEL ==============
@router.message(F.text == "/cancel")
async def cancel_operation(message: Message, state: FSMContext):
    """Cancel current operation"""
    await state.clear()
    await message.answer(
        "❌ Cancelled. Returning to main menu.",
        reply_markup=get_main_menu_keyboard()
    )


# ============== BACK TO MENU ==============
@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Return to main menu"""
    await callback.message.delete()
    await callback.message.answer(
        "🏠 Main Menu",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "browse_meme_coins")
async def browse_meme_coins(callback: CallbackQuery):
    """Handle browse meme coins action from empty watchlist."""
    await callback.message.edit_text(
        "🔥 Meme Coin Tracker\n\nChoose an option below:",
        reply_markup=get_meme_coins_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_watchlist")
async def back_to_watchlist(callback: CallbackQuery):
    """Return user to watchlist view."""
    watchlist = await database.get_watchlist(callback.from_user.id)
    if not watchlist:
        await callback.message.edit_text(
            "📋 Your Watchlist\n\nYour watchlist is empty.",
            reply_markup=get_watchlist_keyboard(watchlist),
            parse_mode="Markdown"
        )
    else:
        tickers = [c['ticker'] for c in watchlist]
        await callback.message.edit_text(
            f"📋 Your Watchlist ({len(watchlist)} coins)",
            reply_markup=get_watchlist_actions_keyboard(tickers),
            parse_mode="Markdown"
        )
    await callback.answer()
