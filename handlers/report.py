"""
Automated portfolio performance reports.
Generates weekly summaries and performance analytics.
"""

import asyncio
import logging
from aiogram import Router, Bot
from aiogram.types import CallbackQuery, Message
from datetime import datetime, timedelta
import database
from keyboards import get_portfolio_keyboard, get_main_menu_keyboard
from config import (
    WEEKLY_REPORT_DAY,
    WEEKLY_REPORT_HOUR,
    PRICE_DROP_ALERT_THRESHOLD
)

router = Router()
logger = logging.getLogger(__name__)


class PerformanceReportGenerator:
    """Generate portfolio performance reports"""
    
    def __init__(self):
        pass
    
    async def generate_weekly_report(self, user_id: int) -> dict:
        """
        Generate comprehensive weekly performance report.
        
        Args:
            user_id: User Telegram ID
        
        Returns:
            Report data dictionary
        """
        # Get portfolio snapshot
        snapshot = await database.get_portfolio_snapshot(user_id)
        
        if not snapshot['positions']:
            return {
                'has_portfolio': False,
                'message': "You don't have any positions to report on."
            }
        
        # Analyze performance
        analysis = await self._analyze_portfolio_performance(snapshot)
        
        # Build report message
        report_msg = self._format_weekly_report(snapshot, analysis)
        
        return {
            'has_portfolio': True,
            'message': report_msg,
            'analysis': analysis,
            'snapshot': snapshot
        }
    
    async def _analyze_portfolio_performance(self, snapshot: dict) -> dict:
        """Analyze portfolio performance metrics"""
        positions = snapshot['positions']
        
        # Sort by performance
        sorted_positions = sorted(
            positions,
            key=lambda p: p.get('profit_loss_pct', 0),
            reverse=True
        )
        
        # Get top performers
        top_performers = sorted_positions[:3]
        worst_performers = sorted_positions[-3:]
        
        # Calculate metrics
        total_positions = len(positions)
        profitable_positions = sum(1 for p in positions if p.get('profit_loss_pct', 0) > 0)
        losing_positions = sum(1 for p in positions if p.get('profit_loss_pct', 0) < 0)
        
        win_rate = (profitable_positions / total_positions * 100) if total_positions > 0 else 0
        
        return {
            'top_performers': top_performers,
            'worst_performers': worst_performers,
            'total_positions': total_positions,
            'profitable_positions': profitable_positions,
            'losing_positions': losing_positions,
            'win_rate': win_rate
        }
    
    def _format_weekly_report(self, snapshot: dict, analysis: dict) -> str:
        """Format weekly report message"""
        total_value = snapshot['total_value']
        total_pnl = snapshot['total_pnl']
        total_pnl_pct = snapshot['total_pnl_pct']
        
        # Header
        msg = (
            f"📊 Weekly Portfolio Report\n"
            f"{'='*40}\n"
            f"📅 Week of {datetime.now().strftime('%B %d, %Y')}\n\n"
        )
        
        # Overall Performance
        pnl_emoji = "📈" if total_pnl >= 0 else "📉"
        pnl_color = "🟢" if total_pnl >= 0 else "🔴"
        
        msg += (
            f"Portfolio Overview:\n"
            f"💼 Total Value: ${total_value:,.2f}\n"
            f"{pnl_emoji} Total P/L: ${total_pnl:,.2f} ({total_pnl_pct:+.2f}%) {pnl_color}\n"
            f"📊 Positions: {analysis['total_positions']}\n"
            f"✅ Profitable: {analysis['profitable_positions']}\n"
            f"❌ Losing: {analysis['losing_positions']}\n"
            f"🎯 Win Rate: {analysis['win_rate']:.1f}%\n\n"
        )
        
        # Top Performers
        msg += "🏆 Top Performers:\n"
        for i, pos in enumerate(analysis['top_performers'], 1):
            asset = pos['asset']
            pnl_pct = pos.get('profit_loss_pct', 0)
            pnl = pos.get('profit_loss', 0)
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
            msg += f"{emoji} {asset}: +{pnl_pct:.2f}% (${pnl:,.2f})\n"
        
        msg += "\n"
        
        # Worst Performers (if any losing positions)
        if analysis['losing_positions'] > 0:
            msg += "⚠️ Needs Attention:\n"
            for pos in analysis['worst_performers']:
                if pos.get('profit_loss_pct', 0) < 0:
                    asset = pos['asset']
                    pnl_pct = pos.get('profit_loss_pct', 0)
                    pnl = pos.get('profit_loss', 0)
                    msg += f"📉 {asset}: {pnl_pct:.2f}% (${pnl:,.2f})\n"
            msg += "\n"
        
        # Footer
        next_report = self._get_next_report_date()
        msg += (
            f"📅 Next Report: {next_report}\n\n"
            f"💡 *Tip: Review underperforming assets and consider rebalancing.*"
        )
        
        return msg
    
    def _get_next_report_date(self) -> str:
        """Calculate next weekly report date"""
        today = datetime.now()
        days_ahead = WEEKLY_REPORT_DAY - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        
        next_date = today + timedelta(days=days_ahead)
        return next_date.strftime('%A, %B %d at %I %p UTC').replace(' 0', ' ')


# Global instance
report_generator = PerformanceReportGenerator()


# ============== MANUAL REPORT GENERATION ==============
@router.callback_query(lambda c: c.data == "generate_report")
async def generate_manual_report(callback: CallbackQuery):
    """Manually generate performance report"""
    user_id = callback.from_user.id
    
    await callback.answer("📊 Generating report...", show_alert=False)
    
    # Generate report
    report = await report_generator.generate_weekly_report(user_id)
    
    if not report['has_portfolio']:
        await callback.message.answer(
            "📊 No Portfolio Data\n\n"
            "Add positions to your portfolio to see performance reports!",
            reply_markup=get_portfolio_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    # Send report
    await callback.message.answer(
        report['message'],
        reply_markup=get_portfolio_keyboard(),
        parse_mode="Markdown"
    )


# ============== AUTOMATED WEEKLY REPORTS ==============
async def send_weekly_reports(bot: Bot):
    """
    Background task to send weekly portfolio reports.
    Runs every day and checks if it's report day/time.
    """
    logger.info("Starting weekly report system...")
    
    while True:
        try:
            now = datetime.now()
            
            # Check if it's report day and time
            if now.weekday() == WEEKLY_REPORT_DAY and now.hour == WEEKLY_REPORT_HOUR:
                logger.info("Starting weekly report generation...")
                
                # Get all active premium users
                active_users = await database.get_all_active_users()
                
                reports_sent = 0
                
                for user_id in active_users:
                    try:
                        # Check if report already sent today
                        last_report = await database.get_last_report_date(user_id)
                        if last_report:
                            last_date = datetime.fromisoformat(last_report).date()
                            if last_date == now.date():
                                continue  # Already sent today
                        
                        # Generate report
                        report = await report_generator.generate_weekly_report(user_id)
                        
                        if not report['has_portfolio']:
                            continue  # Skip users without portfolio
                        
                        # Send report
                        await bot.send_message(
                            user_id,
                            report['message'],
                            reply_markup=get_main_menu_keyboard(),
                            parse_mode="Markdown"
                        )
                        
                        # Mark as sent
                        await database.mark_weekly_report_sent(user_id)
                        
                        reports_sent += 1
                        logger.info(f"Sent weekly report to user {user_id}")
                        
                        # Rate limiting
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"Error sending report to user {user_id}: {e}")
                        continue
                
                logger.info(f"Weekly report cycle complete. Sent {reports_sent} reports.")
                
                # Sleep for 1 hour to avoid duplicate sends
                await asyncio.sleep(3600)
            else:
                # Check every hour
                await asyncio.sleep(3600)
            
        except Exception as e:
            logger.error(f"Error in weekly report system: {e}")
            await asyncio.sleep(3600)


# ============== PRICE DROP ALERTS ==============
async def monitor_price_drops(bot: Bot):
    """
    Monitor portfolio for significant price drops.
    Sends immediate alerts for drops > threshold.
    """
    logger.info("Starting price drop monitoring...")
    
    while True:
        try:
            # Get all active users with portfolios
            active_users = await database.get_all_active_users()
            
            for user_id in active_users:
                try:
                    # Check for price drops
                    drop_alerts = await database.track_price_changes(user_id)
                    
                    if drop_alerts:
                        for alert in drop_alerts:
                            asset = alert['asset']
                            change_pct = alert['change_pct']
                            current_price = alert['current_price']
                            
                            alert_msg = (
                                f"🚨 Price Drop Alert\n\n"
                                f"{asset} has dropped significantly!\n\n"
                                f"📉 Change: {change_pct:.2f}%\n"
                                f"💰 Current Price: ${current_price:,.2f}\n\n"
                                f"⚠️ Consider reviewing this position."
                            )
                            
                            await bot.send_message(
                                user_id,
                                alert_msg,
                                parse_mode="Markdown"
                            )
                            
                            logger.info(f"Sent drop alert for {asset} to user {user_id}")
                            await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error checking drops for user {user_id}: {e}")
                    continue
            
            # Check every 30 minutes
            await asyncio.sleep(1800)
            
        except Exception as e:
            logger.error(f"Error in price drop monitoring: {e}")
            await asyncio.sleep(1800)


# ============== PORTFOLIO SUMMARY ==============
@router.callback_query(lambda c: c.data == "portfolio_summary")
async def show_portfolio_summary(callback: CallbackQuery):
    """Show detailed portfolio summary"""
    user_id = callback.from_user.id
    
    snapshot = await database.get_portfolio_snapshot(user_id)
    
    if not snapshot['positions']:
        await callback.message.edit_text(
            "💼 Your Portfolio\n\n"
            "No positions yet. Add your first position to start tracking!",
            reply_markup=get_portfolio_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    total_value = snapshot['total_value']
    total_pnl = snapshot['total_pnl']
    total_pnl_pct = snapshot['total_pnl_pct']
    
    # Build summary
    pnl_emoji = "📈" if total_pnl >= 0 else "📉"
    pnl_color = "🟢" if total_pnl >= 0 else "🔴"
    
    msg = (
        f"💼 Your Portfolio Summary\n"
        f"{'─'*40}\n\n"
        f"Overview:\n"
        f"💰 Total Value: ${total_value:,.2f}\n"
        f"{pnl_emoji} Total P/L: ${total_pnl:,.2f} ({total_pnl_pct:+.2f}%) {pnl_color}\n"
        f"📊 Positions: {len(snapshot['positions'])}\n\n"
        f"Holdings:\n\n"
    )
    
    for pos in snapshot['positions'][:10]:
        asset = pos['asset']
        pnl_pct = pos.get('profit_loss_pct', 0)
        
        emoji = "📈" if pnl_pct >= 0 else "📉"
        msg += f"{asset}: {pnl_pct:+.1f}% {emoji}\n"
    
    msg += f"\n📅 Next Report: {report_generator._get_next_report_date()}"
    
    await callback.message.edit_text(
        msg,
        reply_markup=get_portfolio_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()