"""
Portfolio management handler - CRYPTO ONLY (Simple Version)
Allows users to track holdings, log trades, and view positions.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import database
from keyboards import get_portfolio_keyboard, get_main_menu_keyboard
from utils.data_fetcher import get_crypto_data, format_large_number

router = Router()

# Define states for trade entry
class TradeStates(StatesGroup):
    waiting_for_asset = State()
    waiting_for_type = State()
    waiting_for_quantity = State()
    waiting_for_price = State()
    waiting_for_notes = State()


# ============== PORTFOLIO MAIN ==============
@router.message(F.text == "💰 Portfolio")
async def portfolio_main(message: Message):
    """Display portfolio main menu"""
    user_id = message.from_user.id
    
    portfolio = await database.get_user_portfolio(user_id)
    pnl_data = await database.get_portfolio_pnl(user_id)
    
    if not portfolio:
        await message.answer(
            "💼 Your Portfolio\n\n"
            "You haven't added any positions yet.\n\n"
            "Use the buttons below to get started:",
            reply_markup=get_portfolio_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    # Build portfolio summary
    total_value = pnl_data['current_value']
    total_pnl = pnl_data['profit_loss']
    pnl_pct = pnl_data['profit_loss_pct']
    pnl_emoji = "📈" if total_pnl >= 0 else "📉"
    pnl_color = "🟢" if total_pnl >= 0 else "🔴"
    
    msg = (
        f"💼 Your Portfolio\n"
        f"{'='*30}\n\n"
        f"Total Value: ${total_value:,.2f}\n"
        f"Total P/L: {pnl_emoji} ${total_pnl:,.2f} ({pnl_pct:+.2f}%) {pnl_color}\n\n"
        f"Holdings ({len(portfolio)} positions):\n\n"
    )
    
    for p in portfolio[:10]:  # Show first 10
        asset = p['asset']
        qty = p['quantity']
        entry = p['entry_price']
        current = p.get('current_price', entry)
        pnl_pct_pos = p.get('profit_loss_pct', 0)
        
        emoji = "📈" if pnl_pct_pos >= 0 else "📉"
        msg += f"{asset} - {qty} units\n"
        msg += f"  Entry: ${entry:.2f} → Now: ${current:.2f} {emoji} ({pnl_pct_pos:+.2f}%)\n\n"
    
    if len(portfolio) > 10:
        msg += f"\n_...and {len(portfolio) - 10} more positions_\n"
    
    await message.answer(
        msg,
        reply_markup=get_portfolio_keyboard(),
        parse_mode="Markdown"
    )


# ============== ADD TRADE ==============
@router.callback_query(F.data == "add_trade")
async def add_trade_start(callback: CallbackQuery, state: FSMContext):
    """Start add trade flow"""
    await state.set_state(TradeStates.waiting_for_asset)
    await callback.message.answer(
        "➕ Add Trade\n\n"
        "Enter the crypto ticker:\n"
        "Examples: BTC, ETH, SOL, DOGE, PEPE\n\n"
        "Send /cancel to abort.",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(TradeStates.waiting_for_asset)
async def process_asset_input(message: Message, state: FSMContext):
    """Process asset ticker"""
    asset = message.text.strip().upper()
    
    if len(asset) > 10 or not asset.replace('-', '').isalnum():
        await message.answer("❌ Invalid ticker format. Please enter a valid crypto symbol.")
        return
    
    # Save asset to state
    await state.update_data(asset=asset)
    await state.set_state(TradeStates.waiting_for_type)
    
    await message.answer(
        f"Asset: {asset}\n\n"
        "Is this a BUY or SELL?\n\n"
        "Reply with: `buy` or `sell`",
        parse_mode="Markdown"
    )

@router.message(TradeStates.waiting_for_type)
async def process_trade_type(message: Message, state: FSMContext):
    """Process trade type"""
    trade_type = message.text.strip().lower()
    
    if trade_type not in ['buy', 'sell']:
        await message.answer("❌ Please enter 'buy' or 'sell'")
        return
    
    await state.update_data(trade_type=trade_type)
    await state.set_state(TradeStates.waiting_for_quantity)
    
    await message.answer(
        f"Trade Type: {trade_type.upper()}\n\n"
        "Enter the quantity:\n"
        "Examples: 10, 0.5, 100",
        parse_mode="Markdown"
    )

@router.message(TradeStates.waiting_for_quantity)
async def process_quantity(message: Message, state: FSMContext):
    """Process quantity"""
    try:
        quantity = float(message.text.strip())
        if quantity <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Please enter a valid positive number")
        return
    
    await state.update_data(quantity=quantity)
    await state.set_state(TradeStates.waiting_for_price)
    
    await message.answer(
        f"Quantity: {quantity}\n\n"
        "Enter the price per unit:\n"
        "Examples: 150.50, 0.001",
        parse_mode="Markdown"
    )

@router.message(TradeStates.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    """Process price"""
    try:
        price = float(message.text.strip())
        if price <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Please enter a valid positive number")
        return
    
    await state.update_data(price=price)
    await state.set_state(TradeStates.waiting_for_notes)
    
    await message.answer(
        f"Price: ${price:.2f}\n\n"
        "Add any notes (optional)?\n\n"
        "Or send /skip to finish without notes.",
        parse_mode="Markdown"
    )

@router.message(TradeStates.waiting_for_notes)
async def process_notes(message: Message, state: FSMContext):
    """Process notes and save trade"""
    notes = message.text.strip() if message.text != "/skip" else ""
    
    # Get all data
    data = await state.get_data()
    asset = data['asset']
    trade_type = data['trade_type']
    quantity = data['quantity']
    price = data['price']
    
    # All trades are crypto now
    asset_type = 'crypto'
    
    # Save trade
    success = await database.add_trade(
        message.from_user.id,
        asset,
        asset_type,
        trade_type,
        quantity,
        price,
        notes
    )
    
    if success:
        total_value = quantity * price
        await message.answer(
            f"✅ Trade Added Successfully!\n\n"
            f"📊 {asset} (Crypto)\n"
            f"Type: {trade_type.upper()}\n"
            f"Quantity: {quantity}\n"
            f"Price: ${price:.2f}\n"
            f"Total Value: ${total_value:.2f}\n"
            + (f"Notes: {notes}\n" if notes else ""),
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "❌ Failed to add trade. Please try again.",
            reply_markup=get_main_menu_keyboard()
        )
    
    await state.clear()

@router.message(F.text == "/skip")
async def skip_notes(message: Message, state: FSMContext):
    """Skip notes and process trade"""
    await process_notes(message, state)


# ============== VIEW PORTFOLIO ==============
@router.callback_query(F.data == "view_portfolio")
async def view_portfolio_detailed(callback: CallbackQuery):
    """View detailed portfolio"""
    user_id = callback.from_user.id
    portfolio = await database.get_user_portfolio(user_id)
    
    if not portfolio:
        await callback.message.edit_text(
            "💼 Your Portfolio\n\n"
            "No positions found.\n\n"
            "Add your first trade to start tracking!",
            reply_markup=get_portfolio_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    # Build detailed view
    pnl_data = await database.get_portfolio_pnl(user_id)
    
    msg = (
        f"💼 Portfolio Details\n"
        f"{'='*30}\n\n"
        f"Summary:\n"
        f"Total Investment: ${pnl_data['total_investment']:,.2f}\n"
        f"Current Value: ${pnl_data['current_value']:,.2f}\n"
        f"P/L: ${pnl_data['profit_loss']:,.2f} ({pnl_data['profit_loss_pct']:+.2f}%)\n\n"
        f"Positions:\n\n"
    )
    
    for p in portfolio:
        asset = p['asset']
        qty = p['quantity']
        entry = p['entry_price']
        current = p.get('current_price', entry)
        pnl = p.get('profit_loss', 0)
        pnl_pct = p.get('profit_loss_pct', 0)
        
        emoji = "🟢" if pnl >= 0 else "🔴"
        msg += f"{emoji} {asset} (Crypto)\n"
        msg += f"  Qty: {qty} @ ${entry:.2f}\n"
        msg += f"  Current: ${current:.2f}\n"
        msg += f"  P/L: ${pnl:.2f} ({pnl_pct:+.2f}%)\n\n"
    
    await callback.message.edit_text(
        msg,
        reply_markup=get_portfolio_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ============== TRADE HISTORY ==============
@router.callback_query(F.data == "view_trades")
async def view_trade_history(callback: CallbackQuery):
    """View trade history"""
    user_id = callback.from_user.id
    trades = await database.get_trade_history(user_id, limit=20)
    
    if not trades:
        await callback.message.edit_text(
            "📜 Trade History\n\n"
            "No trades recorded yet.\n\n"
            "Add your first trade to start tracking!",
            reply_markup=get_portfolio_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    msg = f"📜 Trade History (Last {len(trades)} trades)\n" + "="*30 + "\n\n"
    
    for trade in trades[:20]:
        date = datetime.fromisoformat(trade['timestamp']).strftime('%m/%d %H:%M')
        asset = trade['asset']
        trade_type = trade['trade_type'].upper()
        qty = trade['quantity']
        price = trade['price']
        total = trade['total_value']
        
        emoji = "🟢" if trade_type == "BUY" else "🔴"
        msg += f"{emoji} {asset} - {trade_type}\n"
        msg += f"  {qty} @ ${price:.2f} = ${total:.2f}\n"
        msg += f"  📅 {date}\n\n"
    
    await callback.message.edit_text(
        msg,
        reply_markup=get_portfolio_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ============== REFRESH PRICES ==============
@router.callback_query(F.data == "refresh_prices")
async def refresh_portfolio_prices(callback: CallbackQuery):
    """Refresh all portfolio prices"""
    user_id = callback.from_user.id
    portfolio = await database.get_user_portfolio(user_id)
    
    if not portfolio:
        await callback.answer("No positions to update", show_alert=True)
        return
    
    await callback.answer("🔄 Updating prices...", show_alert=False)
    
    updated = 0
    for position in portfolio:
        asset = position['asset']
        
        try:
            # All assets are crypto
            data = get_crypto_data(asset)
            if data:
                current_price = data.get('price', position['entry_price'])
                await database.update_portfolio_price(user_id, asset, current_price)
                updated += 1
        except Exception as e:
            continue
    
    if updated > 0:
        # Show updated portfolio
        pnl_data = await database.get_portfolio_pnl(user_id)
        
        await callback.message.edit_text(
            f"✅ Prices Updated!\n\n"
            f"Updated {updated}/{len(portfolio)} positions\n\n"
            f"Current Portfolio:\n"
            f"Total Value: ${pnl_data['current_value']:,.2f}\n"
            f"P/L: ${pnl_data['profit_loss']:,.2f} ({pnl_data['profit_loss_pct']:+.2f}%)",
            reply_markup=get_portfolio_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await callback.message.answer("⚠️ Could not update prices. Please try again later.")