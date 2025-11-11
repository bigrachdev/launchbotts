"""
Chart generation utilities for portfolio analytics.
Creates performance charts, P/L visualizations, and portfolio composition.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

# Create charts directory if it doesn't exist
CHARTS_DIR = 'charts'
os.makedirs(CHARTS_DIR, exist_ok=True)


def generate_pnl_chart(user_id: int, trades_data: list) -> str:
    """
    Generate profit/loss chart over time from trade history.
    
    Args:
        user_id: User ID for filename
        trades_data: List of dicts with 'timestamp' and 'pnl' keys
    
    Returns:
        Path to generated chart image
    """
    try:
        if not trades_data:
            return None
        
        # Extract data
        timestamps = [datetime.fromisoformat(t['timestamp']) for t in trades_data]
        pnl_values = [t['pnl'] for t in trades_data]
        
        # Calculate cumulative P/L
        cumulative_pnl = []
        total = 0
        for pnl in pnl_values:
            total += pnl
            cumulative_pnl.append(total)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot cumulative P/L
        ax.plot(timestamps, cumulative_pnl, marker='o', linewidth=2, 
                color='#2ecc71' if cumulative_pnl[-1] >= 0 else '#e74c3c', 
                markersize=4)
        
        # Add zero line
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        
        # Formatting
        ax.set_title('Portfolio P/L Over Time', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date', fontsize=11)
        ax.set_ylabel('Cumulative P/L (%)', fontsize=11)
        ax.grid(True, alpha=0.3)
        
        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.xticks(rotation=45)
        
        # Tight layout
        plt.tight_layout()
        
        # Save
        file_path = os.path.join(CHARTS_DIR, f'user_{user_id}_pnl.png')
        plt.savefig(file_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Generated P/L chart for user {user_id}")
        return file_path
        
    except Exception as e:
        logger.error(f"Error generating P/L chart: {e}")
        return None


def generate_portfolio_pie_chart(user_id: int, holdings: list) -> str:
    """
    Generate portfolio composition pie chart.
    
    Args:
        user_id: User ID for filename
        holdings: List of dicts with 'asset' and 'value' keys
    
    Returns:
        Path to generated chart image
    """
    try:
        if not holdings:
            return None
        
        # Extract data
        labels = [h['asset'] for h in holdings]
        values = [h['value'] for h in holdings]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Color palette
        colors = plt.cm.Set3(range(len(labels)))
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            values, 
            labels=labels, 
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            textprops={'fontsize': 10}
        )
        
        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title('Portfolio Composition', fontsize=14, fontweight='bold')
        
        # Equal aspect ratio ensures circular pie
        ax.axis('equal')
        
        # Save
        file_path = os.path.join(CHARTS_DIR, f'user_{user_id}_portfolio.png')
        plt.savefig(file_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Generated portfolio pie chart for user {user_id}")
        return file_path
        
    except Exception as e:
        logger.error(f"Error generating portfolio pie chart: {e}")
        return None


def generate_winrate_chart(user_id: int, trades_summary: dict) -> str:
    """
    Generate win rate bar chart.
    
    Args:
        user_id: User ID for filename
        trades_summary: Dict with 'wins', 'losses', 'total' keys
    
    Returns:
        Path to generated chart image
    """
    try:
        wins = trades_summary.get('wins', 0)
        losses = trades_summary.get('losses', 0)
        
        if wins == 0 and losses == 0:
            return None
        
        # Create figure
        fig, ax = plt.subplots(figsize=(8, 6))
        
        categories = ['Wins', 'Losses']
        values = [wins, losses]
        colors = ['#2ecc71', '#e74c3c']
        
        # Create bar chart
        bars = ax.bar(categories, values, color=colors, alpha=0.8, edgecolor='black')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        # Formatting
        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        ax.set_title(f'Trading Win Rate: {win_rate:.1f}%', fontsize=14, fontweight='bold')
        ax.set_ylabel('Number of Trades', fontsize=11)
        ax.grid(axis='y', alpha=0.3)
        
        # Tight layout
        plt.tight_layout()
        
        # Save
        file_path = os.path.join(CHARTS_DIR, f'user_{user_id}_winrate.png')
        plt.savefig(file_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Generated win rate chart for user {user_id}")
        return file_path
        
    except Exception as e:
        logger.error(f"Error generating win rate chart: {e}")
        return None


def generate_performance_summary_chart(user_id: int, metrics: dict) -> str:
    """
    Generate comprehensive performance summary chart.
    
    Args:
        user_id: User ID for filename
        metrics: Dict with various performance metrics
    
    Returns:
        Path to generated chart image
    """
    try:
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Portfolio Performance Summary', fontsize=16, fontweight='bold')
        
        # 1. Total P/L
        total_pnl = metrics.get('total_pnl', 0)
        color = '#2ecc71' if total_pnl >= 0 else '#e74c3c'
        ax1.bar(['Total P/L'], [total_pnl], color=color, alpha=0.8)
        ax1.set_title('Total Profit/Loss', fontweight='bold')
        ax1.set_ylabel('P/L (%)')
        ax1.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax1.grid(axis='y', alpha=0.3)
        
        # 2. Win Rate
        win_rate = metrics.get('win_rate', 0)
        ax2.bar(['Win Rate'], [win_rate], color='#3498db', alpha=0.8)
        ax2.set_title('Win Rate', fontweight='bold')
        ax2.set_ylabel('Percentage (%)')
        ax2.set_ylim(0, 100)
        ax2.grid(axis='y', alpha=0.3)
        
        # 3. Average Return
        avg_return = metrics.get('avg_return', 0)
        color = '#2ecc71' if avg_return >= 0 else '#e74c3c'
        ax3.bar(['Avg Return'], [avg_return], color=color, alpha=0.8)
        ax3.set_title('Average Return per Trade', fontweight='bold')
        ax3.set_ylabel('Return (%)')
        ax3.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax3.grid(axis='y', alpha=0.3)
        
        # 4. Total Trades
        total_trades = metrics.get('total_trades', 0)
        ax4.bar(['Total Trades'], [total_trades], color='#9b59b6', alpha=0.8)
        ax4.set_title('Total Trades', fontweight='bold')
        ax4.set_ylabel('Count')
        ax4.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        # Save
        file_path = os.path.join(CHARTS_DIR, f'user_{user_id}_summary.png')
        plt.savefig(file_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Generated performance summary chart for user {user_id}")
        return file_path
        
    except Exception as e:
        logger.error(f"Error generating performance summary chart: {e}")
        return None