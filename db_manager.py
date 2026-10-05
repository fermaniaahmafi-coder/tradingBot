import sqlite3
import json
import time
import os
from config import Config

def get_conn(bot_id="bot1"):
    db_path = Config.get_db_path(bot_id)
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def init_db(bot_id="bot1"):
    with get_conn(bot_id) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS wallet (
            id INTEGER PRIMARY KEY, cash REAL, updated_at REAL
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS positions (
            address TEXT PRIMARY KEY, name TEXT, symbol TEXT, buy_price REAL, tokens_count REAL, cost_usd REAL, current_price REAL, current_val REAL, target_tp_price REAL, target_sl_price REAL, opened_at REAL
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, address TEXT, buy_price REAL, sell_price REAL, cost_usd REAL, proceeds REAL, profit_usd REAL, pnl_pct REAL, reason TEXT, opened_at REAL, closed_at REAL
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, time_raw REAL, type TEXT, message TEXT, details TEXT
        )''')
        conn.execute("CREATE INDEX IF NOT EXISTS idx_trades_closed_at ON trades(closed_at);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_activities_time ON activities(time_raw DESC);")
        
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM wallet WHERE id = 1")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO wallet (id, cash, updated_at) VALUES (1, ?, ?)", (Config.INITIAL_BALANCE, time.time()))
        conn.commit()

def get_wallet(bot_id="bot1"):
    with get_conn(bot_id) as conn:
        row = conn.execute("SELECT cash FROM wallet WHERE id = 1").fetchone()
        if row: return float(row["cash"])
        return Config.INITIAL_BALANCE

def set_wallet(cash, bot_id="bot1"):
    with get_conn(bot_id) as conn:
        conn.execute("INSERT OR REPLACE INTO wallet (id, cash, updated_at) VALUES (1, ?, ?)", (cash, time.time()))
        conn.commit()

def get_positions(bot_id="bot1"):
    with get_conn(bot_id) as conn:
        rows = conn.execute("SELECT * FROM positions").fetchall()
        return [dict(r) for r in rows]

def save_positions(positions, bot_id="bot1"):
    with get_conn(bot_id) as conn:
        conn.execute("DELETE FROM positions")
        for p in positions:
            conn.execute('''INSERT INTO positions 
                (address, name, symbol, buy_price, tokens_count, cost_usd, current_price, current_val, target_tp_price, target_sl_price, opened_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                p.get("address"), p.get("name"), p.get("symbol"),
                p.get("buy_price"), p.get("tokens_count"), p.get("cost_usd"),
                p.get("current_price"), p.get("current_val"),
                p.get("target_tp_price"), p.get("target_sl_price"),
                p.get("opened_at", time.time())
            ))
        conn.commit()

def add_trade(record, bot_id="bot1"):
    with get_conn(bot_id) as conn:
        conn.execute('''INSERT INTO trades 
            (symbol, address, buy_price, sell_price, cost_usd, proceeds, profit_usd, pnl_pct, reason, opened_at, closed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
            record.get("symbol"), record.get("address"), record.get("buy_price"),
            record.get("sell_price"), record.get("cost_usd"), record.get("proceeds"),
            record.get("profit_usd"), record.get("pnl_pct"), record.get("reason"),
            record.get("opened_at"), record.get("closed_at", time.time())
        ))
        conn.commit()

def get_trades(limit=500, bot_id="bot1"):
    with get_conn(bot_id) as conn:
        rows = conn.execute(f"SELECT * FROM trades ORDER BY id DESC LIMIT {limit}").fetchall()
        res = [dict(r) for r in rows]
        res.reverse()
        return res

def add_activity(event_type, message, details=None, bot_id="bot1"):
    entry = {
        "timestamp": time.strftime("%H:%M:%S"),
        "time_raw": time.time(),
        "type": event_type,
        "message": message,
        "details": json.dumps(details or {})
    }
    with get_conn(bot_id) as conn:
        conn.execute('''INSERT INTO activities (timestamp, time_raw, type, message, details)
            VALUES (?, ?, ?, ?, ?)''', (entry["timestamp"], entry["time_raw"], entry["type"], entry["message"], entry["details"]))
        conn.execute("DELETE FROM activities WHERE id NOT IN (SELECT id FROM activities ORDER BY id DESC LIMIT 5000)")
        conn.commit()

def get_recent_activities(limit=50, bot_id="bot1"):
    with get_conn(bot_id) as conn:
        rows = conn.execute(f"SELECT * FROM activities ORDER BY id DESC LIMIT {limit}").fetchall()
        res = []
        for r in rows:
            d = dict(r)
            try: d["details"] = json.loads(d["details"]) if d.get("details") else {}
            except: d["details"] = {}
            res.append(d)
        return res

def get_stats(bot_id="bot1"):
    with get_conn(bot_id) as conn:
        total = conn.execute("SELECT COUNT(*) as count, SUM(profit_usd) as total_profit, MAX(profit_usd) as max_profit, MIN(profit_usd) as min_profit FROM trades").fetchone()
        wins = conn.execute("SELECT COUNT(*) as count FROM trades WHERE pnl_pct > 0").fetchone()["count"]
        losses = conn.execute("SELECT COUNT(*) as count FROM trades WHERE pnl_pct <= 0").fetchone()["count"]
        return {
            "total_trades": total["count"] or 0,
            "total_profit": float(total["total_profit"] or 0),
            "win_count": wins,
            "loss_count": losses,
            "best_trade": float(total["max_profit"] or 0),
            "worst_trade": float(total["min_profit"] or 0)
        }

def reset_db(initial_balance=100.0, bot_id="bot1"):
    with get_conn(bot_id) as conn:
        conn.execute("DELETE FROM positions")
        conn.execute("DELETE FROM trades")
        conn.execute("DELETE FROM activities")
        conn.execute("INSERT OR REPLACE INTO wallet (id, cash, updated_at) VALUES (1, ?, ?)", (initial_balance, time.time()))
        conn.commit()
