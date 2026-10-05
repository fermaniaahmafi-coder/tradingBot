import os
import json
import time
from config import Config
from scanner import fetch_current_price
from bot_logger import log_event
from db_manager import get_wallet, set_wallet, get_positions, save_positions, add_trade, get_trades

class Portfolio:
    def __init__(self):
        self.cash = Config.INITIAL_BALANCE
        self.positions = []
        self.history = []
        self.load_state()

    def load_state(self):
        try:
            self.cash = get_wallet()
            self.positions = get_positions()
            self.history = get_trades(500)
        except Exception as e:
            print(f"[PORTFOLIO] Failed to load state from DB: {e}")

    def save_state(self):
        try:
            set_wallet(self.cash)
            save_positions(self.positions)
            
            # Keep JSON files synced for easy git sync / backup
            with open(Config.DATA_FILE, "w") as f:
                json.dump({
                    "cash": self.cash,
                    "positions": self.positions
                }, f, indent=2)
            
            with open(Config.HISTORY_FILE, "w") as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"[PORTFOLIO] Failed to save state: {e}")

    def can_buy(self):
        self.cash = get_wallet()
        self.positions = get_positions()
        return (
            self.cash >= Config.POSITION_SIZE and 
            len(self.positions) < Config.MAX_POSITIONS
        )

    def buy(self, token, tp_multiplier, sl_multiplier):
        if not self.can_buy():
            return False
        
        # Hindari beli token yang sama jika sudah ada di posisi aktif
        if any(p["address"] == token["address"] for p in self.positions):
            return False

        amount_usd = Config.POSITION_SIZE
        buy_price = token["price_usd"]
        tokens_count = amount_usd / buy_price
        
        position = {
            "address": token["address"],
            "name": token["name"],
            "symbol": token["symbol"],
            "buy_price": buy_price,
            "tokens_count": tokens_count,
            "cost_usd": amount_usd,
            "current_price": buy_price,
            "current_val": amount_usd,
            "target_tp_price": buy_price * tp_multiplier,
            "target_sl_price": buy_price * sl_multiplier,
            "opened_at": time.time()
        }
        
        self.cash -= amount_usd
        self.positions.append(position)
        self.save_state()
        
        log_event("TRADE_BUY", f"Membeli ${position['symbol']} @ ${buy_price:.6f}", {
            "symbol": position["symbol"],
            "amount_usd": amount_usd,
            "buy_price": buy_price,
            "tp_price": position["target_tp_price"],
            "sl_price": position["target_sl_price"]
        })
        print(f"[PORTFOLIO] BUY: {token['symbol']} @ ${buy_price:.6f} | TP: ${position['target_tp_price']:.6f} | SL: ${position['target_sl_price']:.6f}")
        return True

    def check_and_update_positions(self):
        self.positions = get_positions()
        active = []
        for pos in self.positions:
            curr_price = fetch_current_price(pos["address"])
            if curr_price is None:
                active.append(pos)
                continue
            
            pos["current_price"] = curr_price
            pos["current_val"] = pos["tokens_count"] * curr_price
            pnl_pct = ((curr_price - pos["buy_price"]) / pos["buy_price"]) * 100
            
            # Hit Take Profit
            if curr_price >= pos["target_tp_price"]:
                self.sell(pos, curr_price, "TAKE_PROFIT", pnl_pct)
            # Hit Stop Loss
            elif curr_price <= pos["target_sl_price"]:
                self.sell(pos, curr_price, "STOP_LOSS", pnl_pct)
            else:
                active.append(pos)
                
        self.positions = active
        self.save_state()

    def sell(self, pos, sell_price, reason, pnl_pct):
        proceeds = pos["tokens_count"] * sell_price
        profit_usd = proceeds - pos["cost_usd"]
        self.cash = get_wallet() + proceeds
        
        trade_record = {
            "symbol": pos["symbol"],
            "address": pos["address"],
            "buy_price": pos["buy_price"],
            "sell_price": sell_price,
            "cost_usd": pos["cost_usd"],
            "proceeds": proceeds,
            "profit_usd": profit_usd,
            "pnl_pct": pnl_pct,
            "reason": reason,
            "opened_at": pos.get("opened_at", time.time()),
            "closed_at": time.time()
        }
        
        add_trade(trade_record)
        self.history.append(trade_record)
        set_wallet(self.cash)
        
        log_event("TRADE_SELL", f"Menjual ${pos['symbol']} ({reason}) @ ${sell_price:.6f} | PnL: {pnl_pct:+.2f}%", {
            "symbol": pos["symbol"],
            "sell_price": sell_price,
            "profit_usd": profit_usd,
            "pnl_pct": pnl_pct,
            "reason": reason
        })
        print(f"[PORTFOLIO] SELL ({reason}): {pos['symbol']} @ ${sell_price:.6f} | PnL: ${profit_usd:+.2f} ({pnl_pct:+.2f}%)")

    def print_summary(self):
        self.cash = get_wallet()
        self.positions = get_positions()
        coin_val = sum(p.get("current_val", 0) for p in self.positions)
        total_asset = self.cash + coin_val
        slots_left = int(self.cash // Config.POSITION_SIZE)
        
        print("\n" + "="*45)
        print(f"TOTAL ASET: ${total_asset:.2f}")
        print(f"Kas: ${self.cash:.2f} + Koin: ${coin_val:.2f}")
        print(f"Uang Siap Pakai: ${self.cash:.2f} (Bisa beli {slots_left}x lagi)")
        print(f"Posisi Aktif: {len(self.positions)} | Posisi Selesai: {len(self.history)}")
        
        if self.positions:
            print("-" * 45)
            print("POSISI AKTIF:")
            for p in self.positions:
                pnl = ((p["current_price"] - p["buy_price"]) / p["buy_price"]) * 100
                print(f" - {p['symbol']}: ${p['current_price']:.6f} (PnL: {pnl:+.1f}%) | Val: ${p['current_val']:.2f}")
        print("="*45 + "\n")
