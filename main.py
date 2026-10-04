import time
from config import Config
from scanner import get_latest_tokens
from ai_engine import analyze_token
from portfolio import Portfolio
from bot_logger import log_event

def run_bot(iterations=None, delay=15):
    print("=" * 45)
    print("      HERMES SOLANA SNIPER BOT (PAPER TRADING)      ")
    print("=" * 45)
    
    portfolio = Portfolio()
    portfolio.print_summary()
    
    count = 0
    while True:
        try:
            count += 1
            print(f"[{time.strftime('%H:%M:%S')}] Siklus #{count}: Memeriksa pasar & posisi...")
            
            # 1. Update status posisi yang sedang berjalan (cek TP/SL)
            portfolio.check_and_update_positions()
            
            # 2. Jika masih ada slot beli, scan token baru
            if portfolio.can_buy():
                print(f"[{time.strftime('%H:%M:%S')}] Mencari token potensial di Solana...")
                log_event("SCAN", f"Memindai token Solana baru di DexScreener (Sisa slot: {int(portfolio.cash // Config.POSITION_SIZE)}x)...")
                tokens = get_latest_tokens(limit=5)
                for token in tokens:
                    if not portfolio.can_buy():
                        break
                    
                    print(f"Menganalisis {token['symbol']} (${token['price_usd']:.6f})...")
                    decision = analyze_token(token)
                    
                    if decision.get("action") == "BUY":
                        tp = decision.get("tp_multiplier", 1.25)
                        sl = decision.get("sl_multiplier", 0.85)
                        reason = decision.get("reason", "")
                        print(f"-> Sinyal AI: BUY (TP: {tp}x, SL: {sl}x) Alasan: {reason}")
                        log_event("AI_BUY", f"Sinyal BUY pada ${token['symbol']} @ ${token['price_usd']:.6f} | TP: {tp}x, SL: {sl}x", {
                            "token": token["symbol"],
                            "price": token["price_usd"],
                            "tp": tp,
                            "sl": sl,
                            "reason": reason
                        })
                        portfolio.buy(token, tp, sl)
                    else:
                        reason = decision.get('reason', 'Tidak memenuhi kriteria')
                        print(f"-> Sinyal AI: SKIP ({reason})")
                        log_event("AI_SKIP", f"Lewatkan ${token['symbol']} @ ${token['price_usd']:.6f} - {reason}", {
                            "token": token["symbol"],
                            "price": token["price_usd"],
                            "reason": reason
                        })
            else:
                print("Slot beli penuh atau kas tidak mencukupi.")
                
            portfolio.print_summary()
            
            if iterations and count >= iterations:
                break
                
            time.sleep(delay)
            
        except KeyboardInterrupt:
            print("\nBot dihentikan oleh user.")
            break
        except Exception as e:
            print(f"Error pada loop utama: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
