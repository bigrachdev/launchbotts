"""
Launch event tracker and manager - CRYPTO ONLY
Monitors upcoming crypto launches, upgrades, and major events.
"""

import aiosqlite
import asyncpg
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from config import DB_PATH, DATABASE_URL

logger = logging.getLogger(__name__)

# Detect database type
DB_TYPE = os.getenv('DB_TYPE', 'sqlite')


class EventTracker:
    """Track and manage upcoming crypto launch events"""
    
    async def fetch_crypto_events(self, symbol: str) -> List[Dict]:
        """
        Fetch upcoming events for crypto (from multiple sources).
        
        Args:
            symbol: Crypto symbol
        
        Returns:
            List of event dictionaries
        """
        events = []
        
        try:
            # Method 1: Check hardcoded major events (for demo)
            major_events = {
                'BTC': [
                    {'type': 'halving', 'date': '2024-04-20', 'desc': 'Bitcoin Halving Event'},
                ],
                'ETH': [
                    {'type': 'upgrade', 'date': '2024-03-15', 'desc': 'Ethereum Dencun Upgrade'},
                ],
                'SOL': [
                    {'type': 'conference', 'date': '2024-09-20', 'desc': 'Solana Breakpoint 2024'},
                ],
                'ADA': [
                    {'type': 'upgrade', 'date': '2024-06-15', 'desc': 'Cardano Chang Hard Fork'},
                ],
                'MATIC': [
                    {'type': 'upgrade', 'date': '2024-05-10', 'desc': 'Polygon zkEVM Update'},
                ]
            }
            
            if symbol in major_events:
                for event in major_events[symbol]:
                    event_date = datetime.strptime(event['date'], '%Y-%m-%d')
                    if event_date > datetime.now():
                        events.append({
                            'asset': symbol,
                            'asset_type': 'crypto',
                            'event_type': event['type'],
                            'event_date': event['date'],
                            'description': event['desc'],
                            'source': 'Built-in Calendar'
                        })
            
            # Method 2: CoinGecko Events API (if available)
            # This would require CoinGecko Pro API
            # For now, using mock data above
            
            # Method 3: CoinMarketCal API (requires API key)
            # coinmarketcal_events = self._fetch_coinmarketcal(symbol)
            
        except Exception as e:
            logger.error(f"Error fetching crypto events for {symbol}: {e}")
        
        return events
    
    async def save_event(self, event: Dict):
        """Save event to database"""
        if DB_TYPE == 'postgresql':
            conn = await asyncpg.connect(DATABASE_URL)
            try:
                await conn.execute(
                    """INSERT INTO launch_events 
                       (asset, asset_type, event_type, event_date, description, source)
                       VALUES ($1, $2, $3, $4, $5, $6)
                       ON CONFLICT (asset, event_date, event_type) DO NOTHING""",
                    event['asset'],
                    'crypto',
                    event['event_type'],
                    event['event_date'],
                    event.get('description', ''),
                    event.get('source', 'Unknown')
                )
            finally:
                await conn.close()
        else:
            async with aiosqlite.connect(DB_PATH) as db:
                try:
                    await db.execute(
                        """INSERT OR IGNORE INTO launch_events 
                           (asset, asset_type, event_type, event_date, description, source)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            event['asset'],
                            'crypto',
                            event['event_type'],
                            event['event_date'],
                            event.get('description', ''),
                            event.get('source', 'Unknown')
                        )
                    )
                    await db.commit()
                except Exception as e:
                    logger.error(f"Error saving event: {e}")
    
    async def get_upcoming_events(self, days_ahead: int = 30) -> List[Dict]:
        """Get all upcoming crypto events in the next N days"""
        target_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        if DB_TYPE == 'postgresql':
            conn = await asyncpg.connect(DATABASE_URL)
            try:
                rows = await conn.fetch(
                    """SELECT * FROM launch_events 
                       WHERE asset_type = 'crypto'
                       AND event_date >= CURRENT_DATE 
                       AND event_date <= $1
                       ORDER BY event_date ASC""",
                    target_date
                )
                return [dict(row) for row in rows]
            finally:
                await conn.close()
        else:
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    """SELECT * FROM launch_events 
                       WHERE asset_type = 'crypto'
                       AND event_date >= DATE('now') 
                       AND event_date <= DATE(?)
                       ORDER BY event_date ASC""",
                    (target_date,)
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
    
    async def get_events_for_alert(self, days_before: int = 3) -> List[Dict]:
        """Get crypto events that need alerts (X days before event)"""
        target_date = (datetime.now() + timedelta(days=days_before)).strftime('%Y-%m-%d')
        
        if DB_TYPE == 'postgresql':
            conn = await asyncpg.connect(DATABASE_URL)
            try:
                rows = await conn.fetch(
                    """SELECT * FROM launch_events 
                       WHERE asset_type = 'crypto'
                       AND DATE(event_date) = $1
                       AND notified = 0
                       ORDER BY event_date ASC""",
                    target_date
                )
                return [dict(row) for row in rows]
            finally:
                await conn.close()
        else:
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    """SELECT * FROM launch_events 
                       WHERE asset_type = 'crypto'
                       AND DATE(event_date) = DATE(?)
                       AND notified = 0
                       ORDER BY event_date ASC""",
                    (target_date,)
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
    
    async def mark_event_notified(self, event_id: int):
        """Mark event as notified"""
        if DB_TYPE == 'postgresql':
            conn = await asyncpg.connect(DATABASE_URL)
            try:
                await conn.execute(
                    "UPDATE launch_events SET notified = 1 WHERE id = $1",
                    event_id
                )
            finally:
                await conn.close()
        else:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "UPDATE launch_events SET notified = 1 WHERE id = ?",
                    (event_id,)
                )
                await db.commit()
    
    async def update_event_analysis(self, event_id: int, risk_score: float, 
                                   risk_level: str, confidence: float):
        """Update event with AI analysis results"""
        if DB_TYPE == 'postgresql':
            conn = await asyncpg.connect(DATABASE_URL)
            try:
                await conn.execute(
                    """UPDATE launch_events 
                       SET risk_score = $1, risk_level = $2, confidence = $3
                       WHERE id = $4""",
                    risk_score, risk_level, confidence, event_id
                )
            finally:
                await conn.close()
        else:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    """UPDATE launch_events 
                       SET risk_score = ?, risk_level = ?, confidence = ?
                       WHERE id = ?""",
                    (risk_score, risk_level, confidence, event_id)
                )
                await db.commit()
    
    async def sync_watchlist_events(self, user_watchlists: List[Dict]):
        """
        Sync events for all users' watchlists - CRYPTO ONLY
        
        Args:
            user_watchlists: List of watchlist items with user_id, ticker, asset_type
        """
        logger.info(f"Syncing crypto events for {len(user_watchlists)} watchlist items")
        
        processed_assets = set()
        
        for item in user_watchlists:
            asset = item['ticker']
            
            # Skip if already processed
            if asset in processed_assets:
                continue
            
            processed_assets.add(asset)
            
            try:
                # Fetch crypto events
                events = await self.fetch_crypto_events(asset)
                
                # Save events
                for event in events:
                    await self.save_event(event)
                
                if events:
                    logger.info(f"Synced {len(events)} events for {asset}")
                
            except Exception as e:
                logger.error(f"Error syncing events for {asset}: {e}")
                continue


# Global instance
event_tracker = EventTracker()