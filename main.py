import time
import argparse
import json
import os
from collections import defaultdict
from config import Config
from scanner import get_latest_tokens
from ai_engine import analyze_token, STRATEGIES
from portfolio import Portfolio
from bot_logger import log_event

# Token Blacklist System
# Track consecutive losses per token, skip if >= 3 losses in a row
BLACKLIST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "token_blacklist.json")

def load_blacklist():
    """Load blacklist from file, return dict of {symbol: consecutive_losses}"""
    if os.path.exists(BLACKLIST_FILE):
        try:
            with open(BLACKLIST_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_blacklist(blacklist):
    """Save blacklist to file"""
    try:
        with open(BLACKLIST_FILE, "w") as f:
            json.dump(blacklist, f, indent=2)
    except Exception as e:
        print(f"[BLACKLIST] Failed to save: {e}")

def update_blacklist_after_trade(symbol, profit_usd, blacklist):
    """
    Update blacklist after a trade completes.
    Increment counter on loss, reset on win.
    Returns True if token should be blacklisted.
    """
    if profit_usd > 0:
        # Win - reset counter
        if symbol in blacklist:
            del blacklist[symbol]
            save_blacklist(blacklist)
        return False
    else:
        # Loss - increment counter
        blacklist[symbol] = blacklist.get(symbol, 0) + 1
        save_blacklist(blacklist)
        if blacklist[symbol] >= 3:
            return True
        return False

def is_blacklisted(symbol, blacklist):
    """Check if token is blacklisted (3+ consecutive losses)"""
    return blacklist.get(symbol, 0) >= 3

# Track trade outcomes per bot session (for real-time blacklist updates)
recent_trades = defaultdict(list)  # {bot_id: [(symbol, profit_usd), ...]}

def run_bot(bot_id="bot1", iterations=None, delay=15):
    # Stagger startup slightly based on bot_id (bot1=0s, bot2=5s, bot3=10s...)
    bot_index = int(bot_id.replace("bot", ""))
    startup_delay = (bot_index - 1) * 2
    if startup_delay > 0:
        print(f"[{bot_id.upper()}] Menunggu {startup_delay} detik untuk staggering (Mencegah rate limit bersamaan)...")
        time.sleep(startup_delay)

    strat_name = STRATEGIES.get(bot_id, STRATEGIES["bot1"])["name"]
    print("=" * 60)
    print(f"  HERMES SOLANA SNIPER - {bot_id.upper()} ({strat_name})  ")
    print("=" * 60)
    
    portfolio = Portfolio(bot_id)
    portfolio.print_summary()
    
    # Load blacklist
    blacklist = load_blacklist()
    blacklisted_count = sum(1 for v in blacklist.values() if v >= 3)
    print(f"[{bot_id.upper()}] Loaded blacklist: {blacklisted_count} tokens blacklisted")
    
    count = 0
    last_position_count = len(portfolio.positions)
    
    while True:
        try:
            count += 1
            print(f"[{bot_id.upper()} {time.strftime('%H:%M:%S')}] Siklus #{count}: Memeriksa pasar & posisi...")
            
            # 1. Update status posisi yang sedang berjalan (cek TP/SL)
            portfolio.check_and_update_positions()
            
            # Check if any positions closed since last loop, update blacklist
            current_position_count = len(portfolio.positions)
            if current_position_count < last_position_count:
                # Position(s) closed, check recent trades and update blacklist
                recent_history = portfolio.history[-5:] if len(portfolio.history) >= 5 else portfolio.history
                for trade in recent_history:
                    symbol = trade.get("symbol")
                    profit = trade.get("profit_usd", 0)
                    if update_blacklist_after_trade(symbol, profit, blacklist):
                        print(f"[{bot_id.upper()} BLACKLIST] Token ${symbol} added to blacklist (3+ consecutive losses)")
                        log_event("BLACKLIST", f"Token ${symbol} blacklisted after 3+ consecutive losses", bot_id=bot_id)
            last_position_count = current_position_count
            
            # 2. Jika masih ada slot beli, scan token baru
            if portfolio.can_buy():
                print(f"[{bot_id.upper()} {time.strftime('%H:%M:%S')}] Mencari token potensial di Solana...")
                log_event("SCAN", f"Memindai token (Sisa slot: {int(portfolio.cash // Config.POSITION_SIZE)}x)", bot_id=bot_id)
                
                # Fetch tokens (scanner uses shared cache across all bots)
                tokens = get_latest_tokens(limit=5)
                for token in tokens:
                    if not portfolio.can_buy():
                        break
                    
                    # Check blacklist FIRST before AI analysis
                    symbol = token.get("symbol", "UNKNOWN")
                    if is_blacklisted(symbol, blacklist):
                        print(f"[{bot_id.upper()}] SKIP ${symbol} - Token blacklisted ({blacklist[symbol]} consecutive losses)")
                        log_event("BLACKLIST", f"Skipped ${symbol} (blacklisted: {blacklist[symbol]} losses)", bot_id=bot_id)
                        continue
                    
                    print(f"[{bot_id.upper()}] Menganalisis {symbol} (${token['price_usd']:.6f})...")
                    decision = analyze_token(token, bot_id=bot_id)
                    
                    if decision.get("action") == "BUY":
                        tp = decision.get("tp_multiplier", 1.25)
                        sl = decision.get("sl_multiplier", 0.85)
                        reason = decision.get("reason", "")
                        print(f"-> Sinyal AI [{bot_id.upper()}]: BUY (TP: {tp}x, SL: {sl}x) Alasan: {reason}")
                        log_event("AI_BUY", f"Sinyal BUY pada ${symbol} @ ${token['price_usd']:.6f} | TP: {tp}x, SL: {sl}x", {
                            "token": symbol,
                            "price": token["price_usd"],
                            "tp": tp,
                            "sl": sl,
                            "reason": reason
                        }, bot_id=bot_id)
                        portfolio.buy(token, tp, sl)
                    else:
                        reason = decision.get('reason', 'Tidak memenuhi kriteria persona')
                        print(f"-> Sinyal AI [{bot_id.upper()}]: SKIP ({reason})")
                        log_event("AI_SKIP", f"Lewatkan ${symbol} @ ${token['price_usd']:.6f} - {reason}", {
                            "token": symbol,
                            "price": token["price_usd"],
                            "reason": reason
                        }, bot_id=bot_id)
            else:
                print(f"[{bot_id.upper()}] Slot beli penuh atau kas tidak mencukupi.")
                
            portfolio.print_summary()
            
            if iterations and count >= iterations:
                break
                
            time.sleep(delay)
            
        except KeyboardInterrupt:
            print(f"\n[{bot_id.upper()}] Bot dihentikan oleh user.")
            break
        except Exception as e:
            print(f"[{bot_id.upper()}] Error pada loop utama: {e}")
            time.sleep(5)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Hermes Trading Bot")
    parser.add_argument("--bot-id", type=str, default="bot1", help="Bot identifier (e.g. bot1, bot2)")
    args = parser.parse_args()
    run_bot(bot_id=args.bot_id)
