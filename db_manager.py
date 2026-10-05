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

def get_hourly_analytics(bot_id="bot7", tz_offset=7):
    """
    Analisis performa & tren pasar berdasarkan jam eksekusi trade (WIB / UTC+7).
    Mengidentifikasi Golden Hours (Jam Tren Naik) & Danger Hours (Jam Rawan Dump).
    """
    from datetime import datetime, timezone
    import glob

    hourly = {}
    for h in range(24):
        hourly[h] = {
            "hour": h,
            "label": f"{h:02d}:00 - {h:02d}:59 WIB",
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "profit": 0.0,
            "win_rate": 0.0,
            "trend": "BELUM ADA DATA",
            "is_golden": False,
            "is_danger": False
        }

    targets = [bot_id] if bot_id != "all" else ["bot1", "bot2", "bot3", "bot4", "bot5", "bot6", "bot7"]
    for b in targets:
        db_path = Config.get_db_path(b)
        if not os.path.exists(db_path):
            continue
        try:
            with get_conn(b) as conn:
                rows = conn.execute("SELECT opened_at, profit_usd, pnl_pct FROM trades").fetchall()
                for r in rows:
                    opened_at = r["opened_at"]
                    if not opened_at:
                        continue
                    dt = datetime.fromtimestamp(opened_at, timezone.utc)
                    h = (dt.hour + tz_offset) % 24
                    profit = float(r["profit_usd"] or 0)
                    pnl = float(r["pnl_pct"] or 0)
                    hourly[h]["trades"] += 1
                    if pnl > 0:
                        hourly[h]["wins"] += 1
                    else:
                        hourly[h]["losses"] += 1
                    hourly[h]["profit"] = round(hourly[h]["profit"] + profit, 2)
        except Exception:
            pass

    for h in range(24):
        t = hourly[h]["trades"]
        if t > 0:
            wr = round((hourly[h]["wins"] / t) * 100, 1)
            hourly[h]["win_rate"] = wr
            p = hourly[h]["profit"]
            if wr >= 50.0 and p > 0:
                hourly[h]["trend"] = "TREN NAIK"
                hourly[h]["is_golden"] = True
            elif wr < 42.0 or p < -5.0:
                hourly[h]["trend"] = "RAWAN DUMP"
                hourly[h]["is_danger"] = True
            else:
                hourly[h]["trend"] = "NETRAL"

    golden_hours = [d["label"] for d in hourly.values() if d["is_golden"]]
    danger_hours = [d["label"] for d in hourly.values() if d["is_danger"]]
    active_hours = [d for d in hourly.values() if d["trades"] > 0]
    best_hour = max(active_hours, key=lambda x: x["profit"])["label"] if active_hours else "Belum cukup data"

    return {
        "bot_id": bot_id,
        "timezone": "WIB (UTC+7)",
        "golden_hours": golden_hours,
        "danger_hours": danger_hours,
        "best_hour": best_hour,
        "hourly_data": list(hourly.values())
    }

def get_current_hourly_context(bot_id="bot7", tz_offset=7):
    """
    Mengambil ringkasan tren pada jam saat ini untuk di-inject ke prompt AI.
    """
    from datetime import datetime, timezone
    now_utc = datetime.now(timezone.utc)
    current_hour_wib = (now_utc.hour + tz_offset) % 24
    
    analytics = get_hourly_analytics(bot_id=bot_id, tz_offset=tz_offset)
    hr_data = analytics["hourly_data"][current_hour_wib]
    
    if hr_data["trades"] == 0:
        return f"Jam {current_hour_wib:02d}:00 WIB | Belum ada riwayat trade pada jam ini. Mode eksplorasi hati-hati."
        
    trend_tag = hr_data["trend"]
    advice = "Tren historis jam ini cenderung BULLISH/NAIK. Boleh lebih optimis mengejar TP." if hr_data["is_golden"] else (
             "Tren historis jam ini RAWAN DUMP/VOLATILITAS TINGGI. Wajib SL ketat & utamakan TP kilat." if hr_data["is_danger"] else
             "Tren historis jam ini NETRAL/KONSOLIDASI. Fokus pada pantulan oversold yang jelas."
    )
    return (
        f"Jam Saat Ini: {current_hour_wib:02d}:00 WIB ({hr_data['trades']} trades historis, "
        f"Win Rate: {hr_data['win_rate']}%, Net: ${hr_data['profit']:+.2f}). "
        f"Status: {trend_tag}. {advice}"
    )
