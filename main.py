import time
import argparse
from config import Config
from scanner import get_latest_tokens
from ai_engine import analyze_token, STRATEGIES
from portfolio import Portfolio
from bot_logger import log_event

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
    
    count = 0
    while True:
        try:
            count += 1
            print(f"[{bot_id.upper()} {time.strftime('%H:%M:%S')}] Siklus #{count}: Memeriksa pasar & posisi...")
            
            # 1. Update status posisi yang sedang berjalan (cek TP/SL)
            portfolio.check_and_update_positions()
            
            # 2. Jika masih ada slot beli, scan token baru
            if portfolio.can_buy():
                print(f"[{bot_id.upper()} {time.strftime('%H:%M:%S')}] Mencari token potensial di Solana...")
                log_event("SCAN", f"Memindai token (Sisa slot: {int(portfolio.cash // Config.POSITION_SIZE)}x)", bot_id=bot_id)
                
                # Fetch tokens (scanner uses shared cache across all 5 bots)
                tokens = get_latest_tokens(limit=5)
                for token in tokens:
                    if not portfolio.can_buy():
                        break
                    
                    print(f"[{bot_id.upper()}] Menganalisis {token['symbol']} (${token['price_usd']:.6f})...")
                    decision = analyze_token(token, bot_id=bot_id)
                    
                    if decision.get("action") == "BUY":
                        tp = decision.get("tp_multiplier", 1.25)
                        sl = decision.get("sl_multiplier", 0.85)
                        reason = decision.get("reason", "")
                        print(f"-> Sinyal AI [{bot_id.upper()}]: BUY (TP: {tp}x, SL: {sl}x) Alasan: {reason}")
                        log_event("AI_BUY", f"Sinyal BUY pada ${token['symbol']} @ ${token['price_usd']:.6f} | TP: {tp}x, SL: {sl}x", {
                            "token": token["symbol"],
                            "price": token["price_usd"],
                            "tp": tp,
                            "sl": sl,
                            "reason": reason
                        }, bot_id=bot_id)
                        portfolio.buy(token, tp, sl)
                    else:
                        reason = decision.get('reason', 'Tidak memenuhi kriteria persona')
                        print(f"-> Sinyal AI [{bot_id.upper()}]: SKIP ({reason})")
                        log_event("AI_SKIP", f"Lewatkan ${token['symbol']} @ ${token['price_usd']:.6f} - {reason}", {
                            "token": token["symbol"],
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
