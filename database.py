"""
Database operations with dual support: SQLite (local) + PostgreSQL (Render)
Subscriptions/trials REMOVED - 100% FREE bot
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

# Detect database type from environment
DB_TYPE = os.getenv('DB_TYPE', 'sqlite')  # 'sqlite' or 'postgresql'
DB_PATH = os.getenv('DB_PATH', 'launchbot.db')
DATABASE_URL = os.getenv('DATABASE_URL')  # Render provides this

# Import appropriate library
if DB_TYPE == 'postgresql':
    import asyncpg
    _pool = None
else:
    import aiosqlite


# ============== CONNECTION MANAGEMENT ==============

async def get_connection():
    """Get database connection based on DB_TYPE"""
    if DB_TYPE == 'postgresql':
        global _pool
        if _pool is None:
            _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
        return await _pool.acquire()
    else:
        return await aiosqlite.connect(DB_PATH)


async def release_connection(conn):
    """Release database connection"""
    if DB_TYPE == 'postgresql':
        await _pool.release(conn)
    else:
        await conn.close()


async def init_db():
    """Initialize the database with schema"""
    schema_path = os.path.join('models', 'schema.sql')
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = f.read()
    
    if DB_TYPE == 'postgresql':
        # PostgreSQL initialization
        conn = await get_connection()
        try:
            # Convert SQLite schema to PostgreSQL
            schema_pg = schema.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
            schema_pg = schema_pg.replace('TIMESTAMP DEFAULT CURRENT_TIMESTAMP', 
                                         'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            
            await conn.execute(schema_pg)
            logger.info("✅ PostgreSQL database initialized")
        finally:
            await release_connection(conn)
    else:
        # SQLite initialization
        conn = await get_connection()
        try:
            await conn.executescript(schema)
            await conn.commit()
            logger.info("✅ SQLite database initialized")
        finally:
            await release_connection(conn)


# ============== USER FUNCTIONS ==============

async def get_user(telegram_id: int) -> Optional[Dict]:
    """Get user by telegram_id"""
    conn = await get_connection()
    try:
        if DB_TYPE == 'postgresql':
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1", 
                telegram_id
            )
            return dict(row) if row else None
        else:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM users WHERE telegram_id = ?", 
                (telegram_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    finally:
        await release_connection(conn)


async def create_user(telegram_id: int, username: str = None) -> Dict:
    """Create a new user - NO TRIAL, 100% FREE"""
    conn = await get_connection()
    try:
        if DB_TYPE == 'postgresql':
            await conn.execute(
                """INSERT INTO users (telegram_id, username, status, alerts_enabled)
                   VALUES ($1, $2, 'active', 0)
                   ON CONFLICT (telegram_id) DO NOTHING""",
                telegram_id, username
            )
        else:
            await conn.execute(
                """INSERT OR IGNORE INTO users (telegram_id, username, status, alerts_enabled)
                   VALUES (?, ?, 'active', 0)""",
                (telegram_id, username)
            )
            await conn.commit()
    finally:
        await release_connection(conn)
    
    return await get_user(telegram_id)


async def update_user_language(telegram_id: int, language: str):
    """Update user language preference"""
    conn = await get_connection()
    try:
        if DB_TYPE == 'postgresql':
            await conn.execute(
                "UPDATE users SET language = $1 WHERE telegram_id = $2",
                language, telegram_id
            )
        else:
            await conn.execute(
                "UPDATE users SET language = ? WHERE telegram_id = ?",
                (language, telegram_id)
            )
            await conn.commit()
    finally:
        await release_connection(conn)


async def delete_user(telegram_id: int):
    """Delete user and all their data"""
    conn = await get_connection()
    try:
        if DB_TYPE == 'postgresql':
            await conn.execute("DELETE FROM watchlist WHERE user_id = $1", telegram_id)
            await conn.execute("DELETE FROM analysis_history WHERE user_id = $1", telegram_id)
            await conn.execute("DELETE FROM alerts_log WHERE user_id = $1", telegram_id)
            await conn.execute("DELETE FROM portfolio WHERE user_id = $1", telegram_id)
            await conn.execute("DELETE FROM trade_journal WHERE user_id = $1", telegram_id)
            await conn.execute("DELETE FROM users WHERE telegram_id = $1", telegram_id)
        else:
            await conn.execute("DELETE FROM watchlist WHERE user_id = ?", (telegram_id,))
            await conn.execute("DELETE FROM analysis_history WHERE user_id = ?", (telegram_id,))
            await conn.execute("DELETE FROM alerts_log WHERE user_id = ?", (telegram_id,))
            await conn.execute("DELETE FROM portfolio WHERE user_id = ?", (telegram_id,))
            await conn.execute("DELETE FROM trade_journal WHERE user_id = ?", (telegram_id,))
            await conn.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
            await conn.commit()
    finally:
        await release_connection(conn)


# ============== WATCHLIST FUNCTIONS ==============

async def add_crypto(user_id: int, ticker: str, is_meme: bool = False) -> bool:
    """Add a crypto ticker to user's watchlist"""
    ticker = ticker.upper().strip()
    conn = await get_connection()
    try:
        if DB_TYPE == 'postgresql':
            await conn.execute(
                """INSERT INTO watchlist (user_id, ticker, asset_type, is_meme_coin) 
                   VALUES ($1, $2, 'crypto', $3)
                   ON CONFLICT (user_id, ticker) DO NOTHING""",
                user_id, ticker, is_meme
            )
        else:
            await conn.execute(
                "INSERT OR IGNORE INTO watchlist (user_id, ticker, asset_type, is_meme_coin) VALUES (?, ?, 'crypto', ?)",
                (user_id, ticker, 1 if is_meme else 0)
            )
            await conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error adding crypto: {e}")
        return False
    finally:
        await release_connection(conn)


async def get_watchlist(user_id: int) -> List[Dict]:
    """Get all tickers in user's watchlist"""
    conn = await get_connection()
    try:
        if DB_TYPE == 'postgresql':
            rows = await conn.fetch(
                "SELECT * FROM watchlist WHERE user_id = $1 ORDER BY created_at DESC",
                user_id
            )
            return [dict(row) for row in rows]
        else:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM watchlist WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    finally:
        await release_connection(conn)


async def remove_crypto(user_id: int, ticker: str) -> bool:
    """Remove a crypto ticker from user's watchlist"""
    ticker = ticker.upper().strip()
    conn = await get_connection()
    try:
        if DB_TYPE == 'postgresql':
            result = await conn.execute(
                "DELETE FROM watchlist WHERE user_id = $1 AND ticker = $2",
                user_id, ticker
            )
            return result != 'DELETE 0'
        else:
            cursor = await conn.execute(
                "DELETE FROM watchlist WHERE user_id = ? AND ticker = ?",
                (user_id, ticker)
            )
            await conn.commit()
            return cursor.rowcount > 0
    finally:
        await release_connection(conn)


# ============== ALERTS FUNCTIONS ==============

async def toggle_alerts(user_id: int, enabled: bool):
    """Enable or disable alerts for user"""
    conn = await get_connection()
    try:
        if DB_TYPE == 'postgresql':
            await conn.execute(
                "UPDATE users SET alerts_enabled = $1 WHERE telegram_id = $2",
                enabled, user_id
            )
        else:
            await conn.execute(
                "UPDATE users SET alerts_enabled = ? WHERE telegram_id = ?",
                (1 if enabled else 0, user_id)
            )
            await conn.commit()
    finally:
        await release_connection(conn)


async def get_alerts_enabled(user_id: int) -> bool:
    """Check if alerts are enabled for user"""
    user = await get_user(user_id)
    return bool(user.get('alerts_enabled', 0)) if user else False


async def get_all_active_users() -> List[int]:
    """Get all users with alerts enabled - NO TRIAL CHECKS (100% FREE)"""
    conn = await get_connection()
    try:
        if DB_TYPE == 'postgresql':
            rows = await conn.fetch(
                "SELECT telegram_id FROM users WHERE alerts_enabled = true"
            )
            return [row['telegram_id'] for row in rows]
        else:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT telegram_id FROM users WHERE alerts_enabled = 1"
            ) as cursor:
                rows = await cursor.fetchall()
                return [row['telegram_id'] for row in rows]
    finally:
        await release_connection(conn)


# ============== ANALYSIS HISTORY ==============

async def save_analysis(user_id: int, ticker: str, asset_type: str, risk_score: int, analysis_data: dict):
    """Save analysis to history"""
    conn = await get_connection()
    try:
        if DB_TYPE == 'postgresql':
            await conn.execute(
                """INSERT INTO analysis_history (user_id, ticker, asset_type, risk_score, analysis_data)
                   VALUES ($1, $2, $3, $4, $5)""",
                user_id, ticker, asset_type, risk_score, json.dumps(analysis_data)
            )
        else:
            await conn.execute(
                """INSERT INTO analysis_history (user_id, ticker, asset_type, risk_score, analysis_data)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, ticker, asset_type, risk_score, json.dumps(analysis_data))
            )
            await conn.commit()
    finally:
        await release_connection(conn)


async def get_analysis_history(user_id: int, limit: int = 10) -> List[Dict]:
    """Get recent analysis history for user"""
    conn = await get_connection()
    try:
        if DB_TYPE == 'postgresql':
            rows = await conn.fetch(
                """SELECT * FROM analysis_history 
                   WHERE user_id = $1 
                   ORDER BY created_at DESC 
                   LIMIT $2""",
                user_id, limit
            )
            return [dict(row) for row in rows]
        else:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                """SELECT * FROM analysis_history 
                   WHERE user_id = ? 
                   ORDER BY created_at DESC 
                   LIMIT ?""",
                (user_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    finally:
        await release_connection(conn)


# ============== ALERT LOG ==============

async def log_alert(user_id: int, ticker: str, alert_type: str, message: str):
    """Log an alert sent to user"""
    conn = await get_connection()
    try:
        if DB_TYPE == 'postgresql':
            await conn.execute(
                """INSERT INTO alerts_log (user_id, ticker, alert_type, message)
                   VALUES ($1, $2, $3, $4)""",
                user_id, ticker, alert_type, message
            )
        else:
            await conn.execute(
                """INSERT INTO alerts_log (user_id, ticker, alert_type, message)
                   VALUES (?, ?, ?, ?)""",
                (user_id, ticker, alert_type, message)
            )
            await conn.commit()
    finally:
        await release_connection(conn)


# ============== PORTFOLIO FUNCTIONS (SIMPLE VERSION) ==============

async def add_trade(user_id: int, asset: str, asset_type: str, trade_type: str, 
                    quantity: float, price: float, notes: str = "") -> bool:
    """Add a trade to journal and update portfolio"""
    asset = asset.upper().strip()
    total_value = quantity * price
    
    conn = await get_connection()
    try:
        if DB_TYPE == 'postgresql':
            # Add to trade journal
            await conn.execute(
                """INSERT INTO trade_journal (user_id, asset, asset_type, trade_type, quantity, price, total_value, notes)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                user_id, asset, asset_type, trade_type, quantity, price, total_value, notes
            )
            
            # Update portfolio
            if trade_type.lower() == 'buy':
                existing = await conn.fetchrow(
                    "SELECT * FROM portfolio WHERE user_id = $1 AND asset = $2",
                    user_id, asset
                )
                
                if existing:
                    old_qty = existing['quantity']
                    old_price = existing['entry_price']
                    new_qty = old_qty + quantity
                    new_avg_price = ((old_qty * old_price) + (quantity * price)) / new_qty
                    
                    await conn.execute(
                        """UPDATE portfolio 
                           SET quantity = $1, entry_price = $2, current_price = $3, last_updated = $4
                           WHERE user_id = $5 AND asset = $6""",
                        new_qty, new_avg_price, price, datetime.now(), user_id, asset
                    )
                else:
                    await conn.execute(
                        """INSERT INTO portfolio (user_id, asset, asset_type, quantity, entry_price, current_price)
                           VALUES ($1, $2, $3, $4, $5, $6)""",
                        user_id, asset, asset_type, quantity, price, price
                    )
            
            elif trade_type.lower() == 'sell':
                existing = await conn.fetchrow(
                    "SELECT * FROM portfolio WHERE user_id = $1 AND asset = $2",
                    user_id, asset
                )
                
                if existing:
                    old_qty = existing['quantity']
                    new_qty = old_qty - quantity
                    
                    if new_qty <= 0:
                        await conn.execute(
                            "DELETE FROM portfolio WHERE user_id = $1 AND asset = $2",
                            user_id, asset
                        )
                    else:
                        await conn.execute(
                            """UPDATE portfolio 
                               SET quantity = $1, current_price = $2, last_updated = $3
                               WHERE user_id = $4 AND asset = $5""",
                            new_qty, price, datetime.now(), user_id, asset
                        )
        
        else:
            # SQLite version (same logic, different syntax)
            await conn.execute(
                """INSERT INTO trade_journal (user_id, asset, asset_type, trade_type, quantity, price, total_value, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, asset, asset_type, trade_type, quantity, price, total_value, notes)
            )
            
            if trade_type.lower() == 'buy':
                async with conn.execute(
                    "SELECT * FROM portfolio WHERE user_id = ? AND asset = ?",
                    (user_id, asset)
                ) as cursor:
                    existing = await cursor.fetchone()
                
                if existing:
                    old_qty = existing[4]
                    old_price = existing[5]
                    new_qty = old_qty + quantity
                    new_avg_price = ((old_qty * old_price) + (quantity * price)) / new_qty
                    
                    await conn.execute(
                        """UPDATE portfolio 
                           SET quantity = ?, entry_price = ?, current_price = ?, last_updated = ?
                           WHERE user_id = ? AND asset = ?""",
                        (new_qty, new_avg_price, price, datetime.now(), user_id, asset)
                    )
                else:
                    await conn.execute(
                        """INSERT INTO portfolio (user_id, asset, asset_type, quantity, entry_price, current_price)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (user_id, asset, asset_type, quantity, price, price)
                    )
            
            elif trade_type.lower() == 'sell':
                async with conn.execute(
                    "SELECT * FROM portfolio WHERE user_id = ? AND asset = ?",
                    (user_id, asset)
                ) as cursor:
                    existing = await cursor.fetchone()
                
                if existing:
                    old_qty = existing[4]
                    new_qty = old_qty - quantity
                    
                    if new_qty <= 0:
                        await conn.execute(
                            "DELETE FROM portfolio WHERE user_id = ? AND asset = ?",
                            (user_id, asset)
                        )
                    else:
                        await conn.execute(
                            """UPDATE portfolio 
                               SET quantity = ?, current_price = ?, last_updated = ?
                               WHERE user_id = ? AND asset = ?""",
                            (new_qty, price, datetime.now(), user_id, asset)
                        )
            
            await conn.commit()
        
        return True
    except Exception as e:
        logger.error(f"Error adding trade: {e}")
        return False
    finally:
        await release_connection(conn)


async def get_user_portfolio(user_id: int) -> List[Dict]:
    """Get all holdings for a user"""
    conn = await get_connection()
    try:
        if DB_TYPE == 'postgresql':
            rows = await conn.fetch(
                "SELECT * FROM portfolio WHERE user_id = $1 ORDER BY date_added DESC",
                user_id
            )
            return [dict(row) for row in rows]
        else:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM portfolio WHERE user_id = ? ORDER BY date_added DESC",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    finally:
        await release_connection(conn)


async def get_trade_history(user_id: int, limit: int = 50) -> List[Dict]:
    """Get trade journal entries"""
    conn = await get_connection()
    try:
        if DB_TYPE == 'postgresql':
            rows = await conn.fetch(
                """SELECT * FROM trade_journal 
                   WHERE user_id = $1 
                   ORDER BY timestamp DESC 
                   LIMIT $2""",
                user_id, limit
            )
            return [dict(row) for row in rows]
        else:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                """SELECT * FROM trade_journal 
                   WHERE user_id = ? 
                   ORDER BY timestamp DESC 
                   LIMIT ?""",
                (user_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    finally:
        await release_connection(conn)


async def update_portfolio_price(user_id: int, asset: str, current_price: float) -> bool:
    """Update current price and calculate P/L for an asset"""
    conn = await get_connection()
    try:
        if DB_TYPE == 'postgresql':
            position = await conn.fetchrow(
                "SELECT * FROM portfolio WHERE user_id = $1 AND asset = $2",
                user_id, asset
            )
            
            if not position:
                return False
            
            entry_price = position['entry_price']
            quantity = position['quantity']
            
            profit_loss = (current_price - entry_price) * quantity
            profit_loss_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
            
            await conn.execute(
                """UPDATE portfolio 
                   SET current_price = $1, profit_loss = $2, profit_loss_pct = $3, last_updated = $4
                   WHERE user_id = $5 AND asset = $6""",
                current_price, profit_loss, profit_loss_pct, datetime.now(), user_id, asset
            )
        else:
            async with conn.execute(
                "SELECT * FROM portfolio WHERE user_id = ? AND asset = ?",
                (user_id, asset)
            ) as cursor:
                position = await cursor.fetchone()
            
            if not position:
                return False
            
            entry_price = position[5]
            quantity = position[4]
            
            profit_loss = (current_price - entry_price) * quantity
            profit_loss_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
            
            await conn.execute(
                """UPDATE portfolio 
                   SET current_price = ?, profit_loss = ?, profit_loss_pct = ?, last_updated = ?
                   WHERE user_id = ? AND asset = ?""",
                (current_price, profit_loss, profit_loss_pct, datetime.now(), user_id, asset)
            )
            await conn.commit()
        
        return True
    except Exception as e:
        logger.error(f"Error updating portfolio price: {e}")
        return False
    finally:
        await release_connection(conn)


async def get_portfolio_pnl(user_id: int) -> Dict:
    """Get total P/L for portfolio"""
    portfolio = await get_user_portfolio(user_id)
    
    total_investment = sum(p.get('entry_price', 0) * p.get('quantity', 0) for p in portfolio)
    current_value = sum(p.get('current_price', 0) * p.get('quantity', 0) for p in portfolio)
    
    profit_loss = current_value - total_investment
    profit_loss_pct = (profit_loss / total_investment * 100) if total_investment > 0 else 0
    
    return {
        'total_investment': total_investment,
        'current_value': current_value,
        'profit_loss': profit_loss,
        'profit_loss_pct': profit_loss_pct
    }

async def get_portfolio_snapshot(user_id: int) -> Dict:
    """Get portfolio snapshot for reports"""
    portfolio = await get_user_portfolio(user_id)
    pnl = await get_portfolio_pnl(user_id)
    
    return {
        'positions': portfolio,
        'total_value': pnl['current_value'],
        'total_pnl': pnl['profit_loss'],
        'total_pnl_pct': pnl['profit_loss_pct']
    }