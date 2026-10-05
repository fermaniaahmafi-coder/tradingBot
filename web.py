import os
import json
import time
import subprocess
from flask import Flask, jsonify, request, render_template, send_file, redirect, make_response
from config import Config
from db_manager import get_wallet, set_wallet, get_positions, save_positions, get_trades, get_recent_activities, reset_db, get_stats, get_hourly_analytics
from bot_logger import log_event, get_recent_logs
from ai_engine import STRATEGIES
from scanner import get_token_details
from auth import create_token, verify_token, login_required

app = Flask(__name__)

BOT_STATE_FILE = "bot_state.json"
ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

# Default values matching config.py
ENV_DEFAULTS = {
    "INITIAL_BALANCE": "100.0",
    "POSITION_SIZE": "10.0",
    "MAX_POSITIONS": "10",
    "AI_BASE_URL": "http://127.0.0.1:20128/v1",
    "AI_API_KEY": "",
    "AI_MODEL": "trading",
    "NETWORK": "solana",
    "MIN_LIQUIDITY": "5000",
    "MIN_VOLUME_24H": "10000",
}


def read_env_file():
    """Read .env file and return dict of key=value pairs."""
    env_vars = dict(ENV_DEFAULTS)
    if os.path.exists(ENV_FILE):
        try:
            with open(ENV_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, _, val = line.partition("=")
                        env_vars[key.strip()] = val.strip()
        except Exception:
            pass
    return env_vars


def update_env_file(updates):
    """Update specific keys in .env file. Preserves comments and ordering."""
    # Read existing lines
    lines = []
    if os.path.exists(ENV_FILE):
        try:
            with open(ENV_FILE, "r") as f:
                lines = f.readlines()
        except Exception:
            pass

    # Parse existing keys and track which lines have which keys
    updated_keys = set()
    new_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue
        if "=" in stripped:
            key, _, val = stripped.partition("=")
            key = key.strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}\n")
                updated_keys.add(key)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    # Append any keys that weren't in the file
    for key, val in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={val}\n")

    try:
        with open(ENV_FILE, "w") as f:
            f.writelines(new_lines)
        return True
    except Exception as e:
        print(f"[Settings] Failed to write .env: {e}")
        return False

def get_bot_state():
    default_state = {
        "mode": "testing",
        "bot_status": "running"
    }
    if os.path.exists(BOT_STATE_FILE):
        try:
            with open(BOT_STATE_FILE, "r") as f:
                return {**default_state, **json.load(f)}
        except Exception:
            pass
    return default_state

def save_bot_state(state):
    try:
        with open(BOT_STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass

def load_data_with_fallback(bot_id="bot1", mode=None):
    """Load positions, history, cash, and logs for a specific bot."""
    state = get_bot_state()
    if mode is None:
        mode = state.get("mode", "testing")

    portfolio_file = Config.get_data_file(bot_id)
    history_file = Config.get_history_file(bot_id)
    default_cash = 100.00

    try:
        db_path = Config.get_db_path(bot_id)
        if os.path.exists(db_path):
            db_cash = get_wallet(bot_id)
            db_positions = get_positions(bot_id)
            db_history = get_trades(500, bot_id)
            db_logs = get_recent_activities(40, bot_id)
            if db_history or db_positions or db_cash > 0:
                for idx, t in enumerate(db_history, 1):
                    if not t.get("id"):
                        t["id"] = idx
                return db_cash, db_positions, db_history, db_logs
    except Exception as e:
        pass

    cash = default_cash
    positions = []
    history = []
    logs = []

    if os.path.exists(portfolio_file):
        try:
            with open(portfolio_file, "r") as f:
                port_data = json.load(f)
                cash = float(port_data.get("cash", default_cash))
                positions = port_data.get("positions", [])
        except Exception:
            pass

    if os.path.exists(history_file):
        try:
            with open(history_file, "r") as f:
                history = json.load(f)
                for idx, t in enumerate(history, 1):
                    if not t.get("id"):
                        t["id"] = idx
        except Exception:
            pass

    return cash, positions, history, logs


@app.route("/login")
def login_page():
    token = request.cookies.get("auth_token")
    if token and verify_token(token):
        return redirect("/")
    return render_template("login.html")


@app.route("/api/auth/login", methods=["POST"])
def api_auth_login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    remember = data.get("remember", True)

    if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
        token = create_token(username)
        max_age = (Config.JWT_EXPIRY_HOURS * 3600) if remember else None

        resp = make_response(jsonify({
            "success": True,
            "message": "Login berhasil!",
            "token": token,
            "username": username
        }))
        resp.set_cookie(
            "auth_token",
            token,
            max_age=max_age,
            httponly=True,
            samesite="Lax"
        )
        return resp

    return jsonify({
        "success": False,
        "error": "Username atau password salah!"
    }), 401


@app.route("/logout")
@app.route("/api/auth/logout")
def logout():
    resp = make_response(redirect("/login"))
    resp.delete_cookie("auth_token")
    return resp


@app.route("/")
@login_required
def index():
    return render_template("dashboard.html")


@app.route("/analytics")
@login_required
def analytics_page():
    return render_template("analytics.html")


@app.route("/transactions")
@login_required
def transactions_page():
    return render_template("transactions.html")


@app.route("/coin/<address>")
@login_required
def coin_detail(address):
    return render_template("coin.html")


@app.route("/settings")
@login_required
def settings_page():
    return render_template("settings.html")


@app.route("/api/settings")
@login_required
def api_settings_get():
    """Return current settings from .env file."""
    env_vars = read_env_file()
    return jsonify({
        "ai_base_url": env_vars.get("AI_BASE_URL", ""),
        "ai_model": env_vars.get("AI_MODEL", ""),
        "ai_api_key": env_vars.get("AI_API_KEY", ""),
        "position_size": float(env_vars.get("POSITION_SIZE", "10.0")),
        "initial_balance": float(env_vars.get("INITIAL_BALANCE", "100.0")),
        "min_liquidity": float(env_vars.get("MIN_LIQUIDITY", "5000")),
        "min_volume_24h": float(env_vars.get("MIN_VOLUME_24H", "10000")),
    })


@app.route("/api/settings/ai", methods=["POST"])
@login_required
def api_settings_ai():
    """Update AI configuration in .env file."""
    data = request.get_json(silent=True) or {}
    
    updates = {}
    if "ai_base_url" in data:
        updates["AI_BASE_URL"] = data["ai_base_url"].strip()
    if "ai_model" in data:
        updates["AI_MODEL"] = data["ai_model"].strip()
    if "ai_api_key" in data:
        updates["AI_API_KEY"] = data["ai_api_key"].strip()
    
    if not updates:
        return jsonify({"success": False, "error": "Tidak ada data untuk disimpan"}), 400
    
    success = update_env_file(updates)
    if success:
        log_event("CONFIG", f"Pengaturan AI diubah: {', '.join(updates.keys())}", bot_id="system")
        return jsonify({
            "success": True,
            "message": "Pengaturan AI berhasil disimpan. Restart bot untuk menerapkan perubahan.",
            "updated": list(updates.keys())
        })
    else:
        return jsonify({"success": False, "error": "Gagal menyimpan ke file .env"}), 500


@app.route("/api/settings/trading", methods=["POST"])
@login_required
def api_settings_trading():
    """Update trading parameters in .env file."""
    data = request.get_json(silent=True) or {}
    
    updates = {}
    if "position_size" in data:
        updates["POSITION_SIZE"] = str(float(data["position_size"]))
    if "initial_balance" in data:
        updates["INITIAL_BALANCE"] = str(float(data["initial_balance"]))
    if "min_liquidity" in data:
        updates["MIN_LIQUIDITY"] = str(float(data["min_liquidity"]))
    if "min_volume_24h" in data:
        updates["MIN_VOLUME_24H"] = str(float(data["min_volume_24h"]))
    
    if not updates:
        return jsonify({"success": False, "error": "Tidak ada data untuk disimpan"}), 400
    
    success = update_env_file(updates)
    if success:
        log_event("CONFIG", f"Parameter trading diubah: {', '.join(updates.keys())}", bot_id="system")
        return jsonify({
            "success": True,
            "message": "Parameter trading berhasil disimpan!",
            "updated": list(updates.keys())
        })
    else:
        return jsonify({"success": False, "error": "Gagal menyimpan ke file .env"}), 500


@app.route("/api/bots")
@login_required
def api_bots():
    """List summary for all 5 bots"""
    bots = []
    for bot_id, strat in STRATEGIES.items():
        cash, positions, history, _ = load_data_with_fallback(bot_id)
        coin_val = sum([p.get("current_val", 0) for p in positions])
        total_portfolio = cash + coin_val
        wins = [h for h in history if (h.get("profit_usd") or 0) > 0]
        win_rate = (len(wins) / len(history) * 100) if history else 0.0
        total_profit = sum([h.get("profit_usd", 0) for h in history]) + sum([p.get("pnl_usd", p.get("profit_usd", 0)) for p in positions])
        net_roi = (total_profit / Config.INITIAL_BALANCE * 100)
        
        # Check service status
        is_active = False
        try:
            res = subprocess.run(["systemctl", "is-active", f"trading-bot@{bot_id}"], capture_output=True, text=True, timeout=1)
            is_active = (res.stdout.strip() == "active")
        except Exception:
            pass

        bots.append({
            "id": bot_id,
            "name": strat["name"],
            "desc": strat["desc"],
            "active": is_active,
            "cash": round(cash, 2),
            "total_portfolio": round(total_portfolio, 2),
            "total_profit": round(total_profit, 2),
            "net_roi": round(net_roi, 2),
            "win_rate": round(win_rate, 1),
            "total_trades": len(history),
            "open_positions": len(positions)
        })
    return jsonify({"bots": bots})


@app.route("/api/status")
@login_required
def api_status():
    bot_id = request.args.get("bot", "bot1").lower()
    if bot_id not in STRATEGIES:
        bot_id = "bot1"
        
    state = get_bot_state()
    mode = request.args.get("mode", state.get("mode", "testing")).lower()
    bot_status = state.get("bot_status", "running")
    
    try:
        check = subprocess.run(["systemctl", "is-active", f"trading-bot@{bot_id}"], capture_output=True, text=True, timeout=1)
        if check.returncode == 0:
            if check.stdout.strip() == "active":
                bot_status = "running"
            elif bot_status != "paused":
                bot_status = "stopped"
    except Exception:
        pass

    cash, positions, history, logs = load_data_with_fallback(bot_id, mode)
    coin_val = sum([p.get("current_val", 0) for p in positions])
    total_portfolio = cash + coin_val

    bot_active = (bot_status == "running")

    wins = [h for h in history if (h.get("profit_usd") or 0) > 0]
    losses = [h for h in history if (h.get("profit_usd") or 0) <= 0]
    win_rate = (len(wins) / len(history) * 100) if history else 0.0
    realised_pnl = sum([h.get("profit_usd", 0) for h in history])
    unrealised_pnl = sum([p.get("pnl_usd", p.get("profit_usd", 0)) for p in positions])
    total_profit = realised_pnl + unrealised_pnl

    init_bal = Config.INITIAL_BALANCE
    net_roi = (total_profit / init_bal * 100) if init_bal > 0 else 0.0

    return jsonify({
        "bot_id": bot_id,
        "bot_name": STRATEGIES[bot_id]["name"],
        "bot_desc": STRATEGIES[bot_id]["desc"],
        "mode": mode,
        "bot_status": bot_status,
        "bot_active": bot_active,
        "cash": round(cash, 2),
        "coin_value": round(coin_val, 2),
        "total_portfolio": round(total_portfolio, 2),
        "total_profit": round(total_profit, 2),
        "net_roi": round(net_roi, 2),
        "win_rate": round(win_rate, 1),
        "wins_count": len(wins),
        "losses_count": len(losses),
        "positions": positions,
        "history": history,
        "logs": logs,
        "can_buy_slots": max(0, int(cash // (5.0 if bot_id == "bot7" else Config.POSITION_SIZE))),
        "can_reset": True,
        "config": {
            "initial_balance": init_bal,
            "position_size": "Dynamic ($5-$25)" if bot_id == "bot7" else Config.POSITION_SIZE,
            "mode": mode
        }
    })


@app.route("/api/analytics")
@login_required
def api_analytics():
    bot_id = request.args.get("bot", "bot1").lower()
    if bot_id not in STRATEGIES:
        bot_id = "bot1"
        
    timeframe = request.args.get("timeframe", "all").lower()
    cash, positions, all_history, _ = load_data_with_fallback(bot_id)
    coin_val = sum([p.get("current_val", 0) for p in positions])
    current_balance = cash + coin_val
    init_balance = Config.INITIAL_BALANCE

    now = time.time()
    history = all_history
    if timeframe == "today":
        history = [h for h in all_history if (h.get("closed_at") or now) >= (now - 86400)]
    elif timeframe == "week":
        history = [h for h in all_history if (h.get("closed_at") or now) >= (now - 7 * 86400)]
    elif timeframe == "month":
        history = [h for h in all_history if (h.get("closed_at") or now) >= (now - 30 * 86400)]

    total_trades = len(history)
    wins = [h for h in history if (h.get("profit_usd") or 0) > 0]
    losses = [h for h in history if (h.get("profit_usd") or 0) <= 0]
    
    win_count = len(wins)
    loss_count = len(losses)
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0

    gross_profit = sum([h.get("profit_usd", 0) for h in wins])
    gross_loss = abs(sum([h.get("profit_usd", 0) for h in losses]))

    if timeframe == "all":
        net_profit = current_balance - init_balance
    else:
        net_profit = sum([h.get("profit_usd", 0) for h in history])
    net_roi = (net_profit / init_balance * 100) if init_balance > 0 else 0

    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (99.9 if gross_profit > 0 else 0.0)

    avg_trade_pnl = (net_profit / total_trades) if total_trades > 0 else 0
    avg_trade_pct = (sum([h.get("pnl_pct", 0) for h in history]) / total_trades) if total_trades > 0 else 0

    best = max(history, key=lambda x: x.get("profit_usd", 0), default={})
    worst = min(history, key=lambda x: x.get("profit_usd", 0), default={})

    best_trade = {
        "symbol": best.get("symbol", "-"),
        "profit_usd": best.get("profit_usd", 0),
        "pnl_pct": best.get("pnl_pct", 0)
    }
    worst_trade = {
        "symbol": worst.get("symbol", "-"),
        "profit_usd": worst.get("profit_usd", 0),
        "pnl_pct": worst.get("pnl_pct", 0)
    }

    total_volume = sum([h.get("cost_usd", Config.POSITION_SIZE) for h in history])
    
    hold_times = []
    for h in history:
        opened = h.get("opened_at")
        closed = h.get("closed_at")
        if opened and closed and closed > opened:
            hold_times.append((closed - opened) / 60)
        else:
            hold_times.append(1.5)
    avg_hold_mins = (sum(hold_times) / len(hold_times)) if hold_times else 1.5

    tp_count = sum(1 for h in history if h.get("reason") == "TAKE_PROFIT" or (h.get("profit_usd") or 0) > 0)
    sl_count = sum(1 for h in history if h.get("reason") == "STOP_LOSS" or (h.get("profit_usd") or 0) <= 0)

    equity_curve = [{"cum_pnl": 0.0, "symbol": "START"}]
    running_pnl = 0.0
    for h in history:
        running_pnl += h.get("profit_usd", 0)
        equity_curve.append({
            "cum_pnl": round(running_pnl, 2),
            "symbol": h.get("symbol", "SOL"),
            "trade_id": h.get("id"),
            "closed_at": h.get("closed_at")
        })

    token_map = {}
    for h in history:
        sym = h.get("symbol", "UNKNOWN")
        if sym not in token_map:
            token_map[sym] = {"symbol": sym, "count": 0, "wins": 0, "total_profit": 0.0}
        token_map[sym]["count"] += 1
        p_usd = h.get("profit_usd", 0)
        token_map[sym]["total_profit"] += p_usd
        if p_usd > 0:
            token_map[sym]["wins"] += 1

    token_stats = []
    for sym, t in token_map.items():
        t["win_rate"] = (t["wins"] / t["count"] * 100) if t["count"] > 0 else 0
        t["total_profit"] = round(t["total_profit"], 2)
        token_stats.append(t)
    token_stats.sort(key=lambda x: x["total_profit"], reverse=True)

    return jsonify({
        "bot_id": bot_id,
        "bot_name": STRATEGIES[bot_id]["name"],
        "current_balance": current_balance,
        "initial_balance": init_balance,
        "net_profit": net_profit,
        "net_roi": net_roi,
        "total_trades": total_trades,
        "win_count": win_count,
        "loss_count": loss_count,
        "win_rate": win_rate,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "profit_factor": profit_factor,
        "avg_trade_pnl": avg_trade_pnl,
        "avg_trade_pct": avg_trade_pct,
        "best_trade": best_trade,
        "worst_trade": worst_trade,
        "total_volume": total_volume,
        "avg_hold_mins": avg_hold_mins,
        "tp_count": tp_count,
        "sl_count": sl_count,
        "equity_curve": equity_curve,
        "token_stats": token_stats,
        "hourly_analytics": get_hourly_analytics(bot_id=bot_id),
        "recent_trades": list(reversed(history))[:10],
        "recent_trades_all": all_history
    })


@app.route("/api/analytics/hourly")
@login_required
def api_hourly_analytics():
    bot_id = request.args.get("bot", "bot7").lower()
    return jsonify(get_hourly_analytics(bot_id=bot_id))


@app.route("/api/export/transactions")
@login_required
def api_export_transactions():
    bot_id = request.args.get("bot", "bot1").lower()
    filter_type = request.args.get("filter", "all")
    search_query = request.args.get("search", "").strip().lower()

    _, _, history, _ = load_data_with_fallback(bot_id)

    if filter_type == "TP":
        history = [h for h in history if (h.get("profit_usd") or 0) > 0 or h.get("reason") == "TAKE_PROFIT"]
    elif filter_type == "SL":
        history = [h for h in history if (h.get("profit_usd") or 0) <= 0 or h.get("reason") == "STOP_LOSS"]

    if search_query:
        history = [
            h for h in history
            if search_query in str(h.get("symbol", "")).lower()
            or search_query in str(h.get("address", "")).lower()
            or search_query in str(h.get("id", "")).lower()
        ]

    sorted_history = sorted(history, key=lambda x: x.get("id", 0), reverse=True)

    rows = []
    for h in sorted_history:
        opened_ts = h.get("opened_at")
        closed_ts = h.get("closed_at")
        opened_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(opened_ts)) if opened_ts else "-"
        closed_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(closed_ts)) if closed_ts else "-"
        hold_sec = (closed_ts - opened_ts) if (closed_ts and opened_ts and closed_ts > opened_ts) else 0
        hold_min = round(hold_sec / 60, 1) if hold_sec > 0 else 0

        cost = h.get("cost_usd", Config.POSITION_SIZE)
        profit = h.get("profit_usd", 0)
        proceeds = h.get("proceeds", round(cost + profit, 4))
        pnl_pct = round(h.get("pnl_pct", 0), 2)
        reason = h.get("reason", "TAKE_PROFIT" if profit > 0 else "STOP_LOSS")

        rows.append({
            "Bot": bot_id.upper(),
            "Trade ID": h.get("id", "-"),
            "Symbol": f"${h.get('symbol', 'UNKNOWN')}",
            "Contract Address": h.get("address", "-"),
            "Trigger / Reason": reason,
            "Buy Price ($)": h.get("buy_price", 0),
            "Sell Price ($)": h.get("sell_price", 0),
            "Position Size ($)": cost,
            "Proceeds ($)": proceeds,
            "Net Profit/Loss ($)": profit,
            "ROI (%)": pnl_pct,
            "Hold Duration (Min)": hold_min,
            "Buy Time": opened_str,
            "Sell Time": closed_str
        })

    import io
    import csv
    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    mem = io.BytesIO(buf.getvalue().encode('utf-8'))
    filename = f"Monetra_{bot_id.upper()}_Trades_{time.strftime('%Y%m%d_%H%M%S')}.csv"
    return send_file(
        mem,
        as_attachment=True,
        download_name=filename,
        mimetype="text/csv"
    )


@app.route("/api/coin/<address>")
@login_required
def api_coin(address):
    bot_id = request.args.get("bot", "bot1").lower()
    _, positions, history, _ = load_data_with_fallback(bot_id)

    pos = next((p for p in positions if p.get("address") == address), None)
    hist = next((h for h in reversed(history) if h.get("address") == address), None)
    
    live_data = get_token_details(address)
    
    result = {
        "address": address,
        "symbol": "Unknown",
        "current_price": 0,
    }
    
    if live_data:
        result.update({
            "pair_address": live_data.get("pair_address"),
            "current_price": live_data.get("price_usd", 0),
            "symbol": live_data.get("symbol", "UNKNOWN"),
            "dex_url": live_data.get("dex_url"),
            "volume_24h": live_data.get("volume_24h"),
            "liquidity_usd": live_data.get("liquidity_usd"),
        })
        
    if pos:
        result.update(pos)
        if live_data:
            result["current_val"] = pos.get("tokens_count", 0) * live_data.get("price_usd", 0)
        result["status"] = "ACTIVE"
    elif hist:
        result.update(hist)
        result["status"] = "CLOSED"
        if not live_data:
            result["pair_address"] = address
    else:
        result["status"] = "NOT_OWNED"
        if not live_data:
            result["pair_address"] = address
        
    return jsonify(result)


@app.route("/api/control/<action>", methods=["POST"])
@login_required
def api_control(action):
    bot_id = request.args.get("bot", "all").lower()
    targets = [bot_id] if bot_id in STRATEGIES else list(STRATEGIES.keys())

    if action == "start":
        for b in targets:
            try: subprocess.run(["systemctl", "start", f"trading-bot@{b}"])
            except Exception: pass
            log_event("STATUS", f"Bot {b.upper()} dimulai.", bot_id=b)
        return jsonify({"success": True, "message": f"Bot ({', '.join(targets)}) berhasil dimulai!"})

    elif action == "stop":
        for b in targets:
            try: subprocess.run(["systemctl", "stop", f"trading-bot@{b}"])
            except Exception: pass
            log_event("STATUS", f"Bot {b.upper()} dihentikan.", bot_id=b)
        return jsonify({"success": True, "message": f"Bot ({', '.join(targets)}) berhasil dihentikan!"})

    elif action == "reset":
        default_test_cash = 100.00
        for b in targets:
            try: reset_db(default_test_cash, bot_id=b)
            except Exception: pass
            try:
                with open(Config.get_data_file(b), "w") as f:
                    json.dump({"cash": default_test_cash, "positions": []}, f, indent=2)
                with open(Config.get_history_file(b), "w") as f:
                    json.dump([], f, indent=2)
            except Exception: pass
            log_event("STATUS", f"Portofolio {b.upper()} direset ke ${default_test_cash:.2f}.", bot_id=b)
        return jsonify({"success": True, "message": f"Portofolio ({', '.join(targets)}) berhasil direset!"})

    return jsonify({"error": "Unknown action"}), 400


@app.route("/api/control/sell/<address>", methods=["POST"])
@login_required
def api_control_sell(address):
    bot_id = request.args.get("bot", "bot1").lower()
    try:
        positions = get_positions(bot_id)
        found = False
        for p in positions:
            if p["address"] == address:
                p["target_sl_price"] = 9999999999
                p["target_tp_price"] = 0
                found = True
        if found:
            save_positions(positions, bot_id)
            with open(Config.get_data_file(bot_id), "w") as f:
                json.dump({"cash": get_wallet(bot_id), "positions": positions}, f, indent=2)
            return jsonify({"success": True, "message": f"Perintah jual dikirim ke {bot_id.upper()}!"})
        return jsonify({"error": "Posisi tidak ditemukan"}), 404
    except Exception as e:
        return jsonify({"error": f"Gagal update posisi: {e}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
