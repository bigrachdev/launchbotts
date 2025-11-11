"""
Portfolio analytics handler with AI-powered insights.
Generates performance metrics, charts, and trading statistics.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from datetime import datetime
import numpy as np
import database
from keyboards import get_analytics_keyboard, get_main_menu_keyboard
from utils.charting import (
    generate_pnl_chart,
    generate_portfolio_pie_chart,
    generate_winrate_chart,
    generate_performance_summary_chart
)
import os

router = Router()


# ============== ANALYTICS MAIN ==============
@router.callback_query(F.data == "view_analytics")
async def analytics_main(callback: CallbackQuery):
    """Display analytics menu"""
    user_id = callback.from_user.id
    
    await callback.message.edit_text(
        "📊 Portfolio Analytics\n\n"
        "Choose what you'd like to analyze:\n\n"
        "📈 Performance - Overall trading performance\n"
        "🥧 Composition - Portfolio breakdown\n"
        "📉 P/L Chart - Profit/Loss over time\n"
        "🎯 Win Rate - Success rate analysis",
        reply_markup=get_analytics_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ============== CALCULATE PERFORMANCE ==============
def calculate_performance(trades: list) -> dict:
    """
    Calculate comprehensive trading performance metrics.
    
    Args:
        trades: List of trade dictionaries
    
    Returns:
        Dict with performance metrics
    """
    if not trades:
        return {
            "total_pnl": 0,
            "win_rate": 0,
            "avg_return": 0,
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "best_trade": 0,
            "worst_trade": 0
        }
    
    # Build position tracking
    positions = {}  # {asset: {'qty': x, 'entry_price': y}}
    pnl_list = []
    wins = 0
    losses = 0
    
    for trade in trades:
        asset = trade['asset']
        trade_type = trade['trade_type'].lower()
        quantity = trade['quantity']
        price = trade['price']
        
        if trade_type == 'buy':
            if asset not in positions:
                positions[asset] = {'qty': 0, 'total_cost': 0}
            
            positions[asset]['qty'] += quantity
            positions[asset]['total_cost'] += (quantity * price)
            positions[asset]['entry_price'] = positions[asset]['total_cost'] / positions[asset]['qty']
            
        elif trade_type == 'sell':
            if asset in positions and positions[asset]['qty'] > 0:
                entry_price = positions[asset]['entry_price']
                profit_pct = ((price - entry_price) / entry_price) * 100
                
                pnl_list.append(profit_pct)
                
                if profit_pct > 0:
                    wins += 1
                else:
                    losses += 1
                
                # Update position
                positions[asset]['qty'] -= quantity
                if positions[asset]['qty'] <= 0:
                    del positions[asset]
    
    # Calculate metrics
    total_pnl = np.sum(pnl_list) if pnl_list else 0
    win_rate = (wins / len(pnl_list) * 100) if pnl_list else 0
    avg_return = np.mean(pnl_list) if pnl_list else 0
    best_trade = max(pnl_list) if pnl_list else 0
    worst_trade = min(pnl_list) if pnl_list else 0
    
    return {
        "total_pnl": round(total_pnl, 2),
        "win_rate": round(win_rate, 2),
        "avg_return": round(avg_return, 2),
        "total_trades": len(pnl_list),
        "wins": wins,
        "losses": losses,
        "best_trade": round(best_trade, 2),
        "worst_trade": round(worst_trade, 2)
    }


# ============== PERFORMANCE ANALYSIS ==============
@router.callback_query(F.data == "analytics_performance")
async def show_performance(callback: CallbackQuery):
    """Show overall performance metrics"""
    user_id = callback.from_user.id
    
    await callback.answer("📊 Calculating performance...", show_alert=False)
    
    trades = await database.get_trade_history(user_id, limit=100)
    
    if not trades:
        await callback.message.edit_text(
            "📊 Performance Analysis\n\n"
            "No completed trades yet.\n\n"
            "Add some trades to see your performance!",
            reply_markup=get_analytics_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    metrics = calculate_performance(trades)
    
    # Generate summary chart
    chart_path = generate_performance_summary_chart(user_id, metrics)
    
    msg = (
        f"📊 Performance Analysis\n"
        f"{'='*30}\n\n"
        f"Overall Metrics:\n"
        f"Total Trades: {metrics['total_trades']}\n"
        f"Total P/L: {metrics['total_pnl']:+.2f}%\n"
        f"Win Rate: {metrics['win_rate']:.1f}%\n"
        f"Avg Return: {metrics['avg_return']:+.2f}%\n\n"
        f"Best Trade: +{metrics['best_trade']:.2f}%\n"
        f"Worst Trade: {metrics['worst_trade']:.2f}%\n\n"
        f"Win/Loss Record:\n"
        f"✅ Wins: {metrics['wins']}\n"
        f"❌ Losses: {metrics['losses']}\n\n"
        f"📈 Chart generated below!"
    )
    
    await callback.message.answer(msg, parse_mode="Markdown")
    
    if chart_path and os.path.exists(chart_path):
        photo = FSInputFile(chart_path)
        await callback.message.answer_photo(
            photo,
            caption="📊 Your Performance Summary",
            reply_markup=get_analytics_keyboard()
        )
    else:
        await callback.message.answer(
            "⚠️ Could not generate chart",
            reply_markup=get_analytics_keyboard()
        )


# ============== P/L CHART ==============
@router.callback_query(F.data == "analytics_pnl_chart")
async def show_pnl_chart(callback: CallbackQuery):
    """Generate and show P/L chart"""
    user_id = callback.from_user.id
    
    await callback.answer("📈 Generating P/L chart...", show_alert=False)
    
    trades = await database.get_trade_history(user_id, limit=100)
    
    if not trades:
        await callback.message.edit_text(
            "📈 P/L Chart\n\n"
            "No trades to chart yet.",
            reply_markup=get_analytics_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    # Prepare data for charting
    chart_data = []
    positions = {}
    
    for trade in trades:
        asset = trade['asset']
        trade_type = trade['trade_type'].lower()
        quantity = trade['quantity']
        price = trade['price']
        timestamp = trade['timestamp']
        
        if trade_type == 'buy':
            if asset not in positions:
                positions[asset] = {'qty': 0, 'total_cost': 0}
            positions[asset]['qty'] += quantity
            positions[asset]['total_cost'] += (quantity * price)
            positions[asset]['entry_price'] = positions[asset]['total_cost'] / positions[asset]['qty']
            
        elif trade_type == 'sell':
            if asset in positions and positions[asset]['qty'] > 0:
                entry_price = positions[asset]['entry_price']
                pnl_pct = ((price - entry_price) / entry_price) * 100
                
                chart_data.append({
                    'timestamp': timestamp,
                    'pnl': pnl_pct
                })
                
                positions[asset]['qty'] -= quantity
    
    if not chart_data:
        await callback.message.edit_text(
            "📈 P/L Chart\n\n"
            "Not enough completed trades to generate chart.\n"
            "Complete some sell trades first!",
            reply_markup=get_analytics_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    # Generate chart
    chart_path = generate_pnl_chart(user_id, chart_data)
    
    if chart_path and os.path.exists(chart_path):
        photo = FSInputFile(chart_path)
        await callback.message.answer_photo(
            photo,
            caption=f"📈 P/L Over Time\n\nTotal trades: {len(chart_data)}",
            reply_markup=get_analytics_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await callback.message.answer(
            "⚠️ Could not generate chart",
            reply_markup=get_analytics_keyboard()
        )


# ============== PORTFOLIO COMPOSITION ==============
@router.callback_query(F.data == "analytics_composition")
async def show_composition(callback: CallbackQuery):
    """Show portfolio composition pie chart"""
    user_id = callback.from_user.id
    
    await callback.answer("🥧 Generating composition chart...", show_alert=False)
    
    portfolio = await database.get_user_portfolio(user_id)
    
    if not portfolio:
        await callback.message.edit_text(
            "🥧 Portfolio Composition\n\n"
            "No positions to analyze.",
            reply_markup=get_analytics_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    # Prepare data
    holdings = []
    for p in portfolio:
        value = p['current_price'] * p['quantity']
        holdings.append({
            'asset': p['asset'],
            'value': value
        })
    
    # Generate chart
    chart_path = generate_portfolio_pie_chart(user_id, holdings)
    
    if chart_path and os.path.exists(chart_path):
        photo = FSInputFile(chart_path)
        
        total_value = sum(h['value'] for h in holdings)
        msg = f"🥧 Portfolio Composition\n\nTotal Value: ${total_value:,.2f}\n{len(holdings)} positions"
        
        await callback.message.answer_photo(
            photo,
            caption=msg,
            reply_markup=get_analytics_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await callback.message.answer(
            "⚠️ Could not generate chart",
            reply_markup=get_analytics_keyboard()
        )


# ============== WIN RATE ANALYSIS ==============
@router.callback_query(F.data == "analytics_winrate")
async def show_winrate(callback: CallbackQuery):
    """Show win rate analysis"""
    user_id = callback.from_user.id
    
    await callback.answer("🎯 Analyzing win rate...", show_alert=False)
    
    trades = await database.get_trade_history(user_id, limit=100)
    
    if not trades:
        await callback.message.edit_text(
            "🎯 Win Rate Analysis\n\n"
            "No trades to analyze yet.",
            reply_markup=get_analytics_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    metrics = calculate_performance(trades)
    
    # Generate chart
    chart_path = generate_winrate_chart(user_id, metrics)
    
    msg = (
        f"🎯 Win Rate Analysis\n"
        f"{'='*30}\n\n"
        f"Overall Win Rate: {metrics['win_rate']:.1f}%\n\n"
        f"✅ Winning Trades: {metrics['wins']}\n"
        f"❌ Losing Trades: {metrics['losses']}\n"
        f"📊 Total Trades: {metrics['total_trades']}\n\n"
        f"Performance:\n"
        f"Average Return: {metrics['avg_return']:+.2f}%\n"
        f"Best Trade: +{metrics['best_trade']:.2f}%\n"
        f"Worst Trade: {metrics['worst_trade']:.2f}%"
    )
    
    await callback.message.answer(msg, parse_mode="Markdown")
    
    if chart_path and os.path.exists(chart_path):
        photo = FSInputFile(chart_path)
        await callback.message.answer_photo(
            photo,
            caption="🎯 Your Win/Loss Distribution",
            reply_markup=get_analytics_keyboard()
        )
    else:
        await callback.message.answer(
            "⚠️ Could not generate chart",
            reply_markup=get_analytics_keyboard()
        )


# ============== BACK TO ANALYTICS ==============
@router.callback_query(F.data == "back_to_analytics")
async def back_to_analytics(callback: CallbackQuery):
    """Return to analytics menu"""
    await analytics_main(callback)