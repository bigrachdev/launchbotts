-- LaunchBot Database Schema (FREE VERSION - No subscriptions/trials)
-- Compatible with SQLite (local) and PostgreSQL (Render)

-- ============== USERS TABLE ==============
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    language TEXT DEFAULT 'en',
    alerts_enabled INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============== WATCHLIST TABLE ==============
CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    asset_type TEXT DEFAULT 'crypto',
    is_meme_coin INTEGER DEFAULT 0,
    added_price REAL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id),
    UNIQUE(user_id, ticker)
);

-- ============== ANALYSIS HISTORY TABLE ==============
CREATE TABLE IF NOT EXISTS analysis_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    risk_score INTEGER NOT NULL,
    risk_level TEXT,
    analysis_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
);

-- ============== ALERTS LOG TABLE ==============
CREATE TABLE IF NOT EXISTS alerts_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    message TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
);

-- ============== PORTFOLIO TABLE (Simple Version) ==============
CREATE TABLE IF NOT EXISTS portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    asset TEXT NOT NULL,
    asset_type TEXT NOT NULL DEFAULT 'crypto',
    quantity REAL NOT NULL,
    entry_price REAL NOT NULL,
    current_price REAL,
    profit_loss REAL,
    profit_loss_pct REAL,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id),
    UNIQUE(user_id, asset)
);

-- ============== TRADE JOURNAL TABLE ==============
CREATE TABLE IF NOT EXISTS trade_journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    asset TEXT NOT NULL,
    asset_type TEXT NOT NULL DEFAULT 'crypto',
    trade_type TEXT NOT NULL,
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    total_value REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
);

-- ============== LAUNCH EVENTS TABLE ==============
CREATE TABLE IF NOT EXISTS launch_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset TEXT NOT NULL,
    asset_type TEXT NOT NULL DEFAULT 'crypto',
    event_type TEXT NOT NULL,
    event_date DATE NOT NULL,
    description TEXT,
    source TEXT,
    risk_score REAL,
    risk_level TEXT,
    confidence REAL,
    notified INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(asset, event_date, event_type)
);

-- ============== ALERT PREFERENCES TABLE ==============
CREATE TABLE IF NOT EXISTS alert_preferences (
    user_id INTEGER PRIMARY KEY,
    launch_alerts_enabled INTEGER DEFAULT 1,
    alert_frequency TEXT DEFAULT 'standard',
    min_risk_score INTEGER DEFAULT 70,
    last_alert_sent TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
);

-- ============== EVENT NOTIFICATIONS LOG ==============
CREATE TABLE IF NOT EXISTS event_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id),
    FOREIGN KEY (event_id) REFERENCES launch_events(id)
);

-- ============== INDEXES FOR PERFORMANCE ==============
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlist(user_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_ticker ON watchlist(ticker);
CREATE INDEX IF NOT EXISTS idx_watchlist_is_meme ON watchlist(is_meme_coin);
CREATE INDEX IF NOT EXISTS idx_analysis_user ON analysis_history(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_ticker ON analysis_history(ticker);
CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts_log(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_user ON portfolio(user_id);
CREATE INDEX IF NOT EXISTS idx_trade_journal_user ON trade_journal(user_id);
CREATE INDEX IF NOT EXISTS idx_launch_events_date ON launch_events(event_date);
CREATE INDEX IF NOT EXISTS idx_launch_events_asset ON launch_events(asset);
CREATE INDEX IF NOT EXISTS idx_event_notifications_user ON event_notifications(user_id);

-- ============== NOTES ==============
-- ✅ Removed: subscriptions, payments, trial_start, trial_end
-- ✅ Added: is_meme_coin to watchlist
-- ✅ Added: added_price, notes to watchlist
-- ✅ Simplified: portfolio (basic tracking only)
-- ✅ Compatible: Works with both SQLite and PostgreSQL