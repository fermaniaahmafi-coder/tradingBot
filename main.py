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
    Increment counter on loss with timestamp, reset on win.
    Returns True if token should be blacklisted.
    """
    now = time.time()
    if profit_usd > 0:
        # Win - reset counter
        if symbol in blacklist:
            del blacklist[symbol]
            save_blacklist(blacklist)
        return False
    else:
        # Loss - increment counter with timestamp
        entry = blacklist.get(symbol, {"losses": 0, "updated_at": now})
        if isinstance(entry, int):
            entry = {"losses": entry, "updated_at": now}
        entry["losses"] = entry.get("losses", 0) + 1
        entry["updated_at"] = now
        blacklist[symbol] = entry
        save_blacklist(blacklist)
        return entry["losses"] >= 3

def check_oversold_readiness(token_info):
    """
    Evaluasi teknikal apakah koin dalam pengamatan sudah memasuki
    fase oversold dan siap-siap beli dengan konfirmasi indikator kehati-hatian.
    Kombinasi:
    - Stochastic (5,3,3): Oversold (< 30) & mulai berbalik naik (%K > %D / bounce)
    - Bollinger Bands: Harga di dekat Lower Band atau memantul ke Inside Bands
    - RSI (14): Di zona diskon (25 - 48)
    - Kehati-hatian: Transaksi jual tidak brutal (bukan dump), perubahan harga stabil
    """
    if not token_info or not token_info.get("technicals"):
        return False, "Data teknikal belum lengkap"
        
    tech = token_info["technicals"]
    stoch = tech.get("stochastic") or {}
    bb = tech.get("bollinger_bands", {}).get("position", "")
    rsi = tech.get("rsi", 50)
    txns = token_info.get("txns_5m") or {}
    price_change = token_info.get("price_change_5m", 0)
    
    # 1. Kriteria Oversold / Diskon
    is_stoch_oversold = stoch.get("k", 50) < 30 or stoch.get("state") == "OVERSOLD"
    is_stoch_turning_up = stoch.get("trend") == "BULLISH" or stoch.get("bounce_signal", False)
    is_bb_discount = bb in ("NEAR_LOWER", "INSIDE_BANDS")
    is_rsi_discount = 25 <= rsi <= 48
    
    # 2. Kehati-hatian (Safety against dump / falling knife)
    buys = txns.get("buys", 0)
    sells = txns.get("sells", 0)
    not_dumping = sells == 0 or (buys / max(1, sells)) >= 0.5
    not_crashing = price_change >= -4.0
    
    score = 0
    reasons = []
    if is_stoch_oversold and is_stoch_turning_up:
        score += 2
        reasons.append("Stoch oversold bounce")
    elif is_stoch_turning_up:
        score += 1
        reasons.append("Stoch bullish cross")
        
    if is_bb_discount:
        score += 1
        reasons.append(f"BB {bb}")
        
    if is_rsi_discount:
        score += 1
        reasons.append(f"RSI {rsi} diskon")
        
    if not_dumping and not_crashing:
        score += 1
        reasons.append("Tekanan jual reda")
        
    ready = (score >= 3) and not_dumping and not_crashing
    return ready, ", ".join(reasons)

def is_blacklisted(symbol, blacklist, token_info=None):
    """
    Check if token is blacklisted (3+ consecutive losses).
    Menggunakan mode PENGAMATAN DINAMIS (bukan timer 1 jam statis):
    Token yang loss beruntun diawasi hingga memasuki kondisi oversold &
    terkonfirmasi pantulan indikator (Stochastic, BB, RSI, safety check).
    Saat siap-siap beli, token otomatis diloloskan ke AI untuk dieksekusi hati-hati.
    """
    entry = blacklist.get(symbol)
    if not entry:
        return False

    losses = entry.get("losses", 0) if isinstance(entry, dict) else entry
    if losses < 3:
        return False

    # Cek apakah token sudah memasuki area oversold & siap-siap beli
    if token_info:
        ready, reasons = check_oversold_readiness(token_info)
        if ready:
            return False  # Siap-siap beli! Loloskan ke AI

    return True  # Masih dalam masa pengamatan / belum ada konfirmasi oversold aman

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
    blacklisted_count = sum(1 for v in blacklist.values() if (v.get("losses", 0) if isinstance(v, dict) else v) >= 3)
    print(f"[{bot_id.upper()}] Loaded blacklist: {blacklisted_count} tokens blacklisted (dengan Cooldown & Momentum Override)")
    
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
                slots_info = f"Kas: ${portfolio.cash:.2f}" if bot_id == "bot7" else f"Sisa slot: {int(portfolio.cash // Config.POSITION_SIZE)}x"
                print(f"[{bot_id.upper()} {time.strftime('%H:%M:%S')}] Mencari token potensial di Solana...")
                log_event("SCAN", f"Memindai token ({slots_info})", bot_id=bot_id)
                
                # Fetch tokens (scanner uses shared cache across all bots)
                tokens = get_latest_tokens(limit=5)
                for token in tokens:
                    if not portfolio.can_buy():
                        break
                    
                    # Check blacklist: Pengamatan Dinamis (Menunggu Oversell Siap-siap Beli)
                    symbol = token.get("symbol", "UNKNOWN")
                    if is_blacklisted(symbol, blacklist, token_info=token):
                        loss_cnt = blacklist[symbol].get("losses", blacklist[symbol]) if isinstance(blacklist[symbol], dict) else blacklist[symbol]
                        print(f"[{bot_id.upper()} PENGAMATAN] ${symbol} ({loss_cnt}x loss) masih diobservasi: Menunggu kondisi oversell siap-siap beli...")
                        log_event("WATCHING", f"Observasi ${symbol} ({loss_cnt}x loss): Menunggu konfirmasi oversell & pantulan aman", bot_id=bot_id)
                        continue
                    elif symbol in blacklist:
                        loss_cnt = blacklist[symbol].get("losses", blacklist[symbol]) if isinstance(blacklist[symbol], dict) else blacklist[symbol]
                        if loss_cnt >= 3:
                            ready, reasons = check_oversold_readiness(token)
                            print(f"[{bot_id.upper()} SIAP-SIAP BELI] ${symbol} masuk area oversell ({reasons}), diteruskan ke AI untuk eksekusi hati-hati!")
                            log_event("OVERSOLD_READY", f"${symbol} siap beli dari oversell ({reasons})", bot_id=bot_id)

                    print(f"[{bot_id.upper()}] Menganalisis {symbol} (${token['price_usd']:.6f})...")
                    decision = analyze_token(token, bot_id=bot_id)
                    
                    if decision.get("action") == "BUY":
                        tp = decision.get("tp_multiplier", 1.25)
                        sl = decision.get("sl_multiplier", 0.85)
                        reason = decision.get("reason", "")
                        pos_size = decision.get("position_size", Config.POSITION_SIZE)
                        print(f"-> Sinyal AI [{bot_id.upper()}]: BUY (Size: ${pos_size:.2f}, TP: {tp}x, SL: {sl}x) Alasan: {reason}")
                        log_event("AI_BUY", f"Sinyal BUY pada ${symbol} @ ${token['price_usd']:.6f} | Size: ${pos_size:.2f} | TP: {tp}x, SL: {sl}x", {
                            "token": symbol,
                            "price": token["price_usd"],
                            "position_size": pos_size,
                            "tp": tp,
                            "sl": sl,
                            "reason": reason
                        }, bot_id=bot_id)
                        portfolio.buy(token, tp, sl, position_size=pos_size)
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
