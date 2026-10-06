import os
import json
import time
from config import Config
from scanner import fetch_current_price
from bot_logger import log_event
from db_manager import get_wallet, set_wallet, get_positions, save_positions, add_trade, get_trades, init_db

class Portfolio:
    def __init__(self, bot_id="bot1"):
        self.bot_id = bot_id
        self.cash = Config.INITIAL_BALANCE
        self.positions = []
        self.history = []
        try:
            init_db(self.bot_id)
        except Exception:
            pass
        self.load_state()

    def load_state(self):
        try:
            self.cash = get_wallet(self.bot_id)
            self.positions = get_positions(self.bot_id)
            self.history = get_trades(500, self.bot_id)
        except Exception as e:
            print(f"[PORTFOLIO {self.bot_id}] Failed to load state from DB: {e}")

    def save_state(self):
        try:
            set_wallet(self.cash, self.bot_id)
            save_positions(self.positions, self.bot_id)
            
            with open(Config.get_data_file(self.bot_id), "w") as f:
                json.dump({"cash": self.cash, "positions": self.positions}, f, indent=2)
            
            with open(Config.get_history_file(self.bot_id), "w") as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"[PORTFOLIO {self.bot_id}] Failed to save state: {e}")

    def can_buy(self, amount=None):
        self.cash = get_wallet(self.bot_id)
        self.positions = get_positions(self.bot_id)
        min_amount = amount if amount is not None else (3.0 if self.bot_id == "bot7" else Config.POSITION_SIZE)
        max_positions = 18 if self.bot_id == "bot7" else Config.MAX_POSITIONS
        gas_fee = 0.04
        return (
            self.cash >= (min_amount + gas_fee) and 
            len(self.positions) < max_positions
        )

    def buy(self, token, tp_multiplier, sl_multiplier, position_size=None):
        if position_size is not None and isinstance(position_size, (int, float)):
            min_size = 3.0 if self.bot_id == "bot7" else 5.0
            max_size = 8.0 if self.bot_id == "bot7" else 25.0
            amount_usd = round(max(min_size, min(float(position_size), max_size, self.cash)), 2)
        else:
            amount_usd = 4.5 if self.bot_id == "bot7" else Config.POSITION_SIZE

        gas_fee_buy = 0.04  # Simulasi Solana base fee + priority tip
        if self.cash < (amount_usd + gas_fee_buy):
            return False

        if not self.can_buy(amount_usd):
            return False
        
        if any(p["address"] == token["address"] for p in self.positions):
            return False

        raw_price = token["price_usd"]
        liquidity = max(2000.0, float(token.get("liquidity_usd") or 10000.0))
        
        # AMM Price Impact & Slippage Beli (0.2% base slippage + order_size / (2 * liquidity))
        buy_slippage_pct = min(2.5, (amount_usd / (2.0 * liquidity)) * 100.0 + 0.2)
        effective_buy_price = raw_price * (1.0 + buy_slippage_pct / 100.0)

        # DEX Swap LP Fee (0.3% Raydium standard)
        dex_fee_buy = round(amount_usd * 0.003, 4)
        total_buy_fee = round(dex_fee_buy + gas_fee_buy, 4)
        
        # Modal bersih yang berhasil ditukar ke token
        net_buy_capital = amount_usd - dex_fee_buy
        tokens_count = net_buy_capital / effective_buy_price
        
        position = {
            "address": token["address"],
            "name": token["name"],
            "symbol": token["symbol"],
            "buy_price": effective_buy_price,
            "raw_buy_price": raw_price,
            "tokens_count": tokens_count,
            "cost_usd": amount_usd,
            "buy_fee_usd": total_buy_fee,
            "buy_slippage_pct": buy_slippage_pct,
            "liquidity_usd": liquidity,
            "current_price": effective_buy_price,
            "current_val": net_buy_capital,
            "target_tp_price": effective_buy_price * tp_multiplier,
            "target_sl_price": effective_buy_price * sl_multiplier,
            "opened_at": time.time()
        }
        
        self.cash = round(self.cash - (amount_usd + gas_fee_buy), 2)
        self.positions.append(position)
        self.save_state()
        
        log_event("TRADE_BUY", f"Membeli ${position['symbol']} @ ${effective_buy_price:.6f} (${amount_usd:.2f}) | Slip: +{buy_slippage_pct:.1f}% | Fee: ${total_buy_fee:.2f}", {
            "symbol": position["symbol"],
            "amount_usd": amount_usd,
            "buy_price": effective_buy_price,
            "raw_price": raw_price,
            "slippage_pct": buy_slippage_pct,
            "fee_usd": total_buy_fee,
            "tp_price": position["target_tp_price"],
            "sl_price": position["target_sl_price"]
        }, bot_id=self.bot_id)
        print(f"[PORTFOLIO {self.bot_id}] BUY: {token['symbol']} @ ${effective_buy_price:.6f} | Size: ${amount_usd:.2f} | Fee: ${total_buy_fee:.2f} | TP: ${position['target_tp_price']:.6f} | SL: ${position['target_sl_price']:.6f}")
        return True

    def check_and_update_positions(self):
        self.positions = get_positions(self.bot_id)
        active = []
        now = time.time()
        for pos in self.positions:
            curr_price = fetch_current_price(pos["address"])
            if curr_price is None:
                active.append(pos)
                continue
            
            pos["current_price"] = curr_price
            pos["current_val"] = pos["tokens_count"] * curr_price
            pnl_pct = ((curr_price - pos["buy_price"]) / pos["buy_price"]) * 100
            
            opened_at = pos.get("opened_at", now)
            holding_mins = (now - opened_at) / 60.0

            # 4. Stagnation / Time-Decay Timeout Exit (Koin tertahan > 20 mnt tanpa volatilitas atau > 35 mnt)
            timeout_limit = 20.0 if self.bot_id == "bot7" else 40.0
            max_hold_limit = 35.0 if self.bot_id == "bot7" else 60.0
            if curr_price >= pos["target_tp_price"]:
                self.sell(pos, curr_price, "TAKE_PROFIT", pnl_pct)
            elif curr_price <= pos["target_sl_price"]:
                self.sell(pos, curr_price, "STOP_LOSS", pnl_pct)
            elif curr_price <= pos["buy_price"] * 0.15:
                self.sell(pos, curr_price, "RUG_FLASH_CRASH", pnl_pct)
            elif holding_mins >= timeout_limit and (abs(pnl_pct) < 2.5 or holding_mins >= max_hold_limit):
                self.sell(pos, curr_price, "STAGNATION_TIMEOUT", pnl_pct)
            else:
                active.append(pos)
                
        self.positions = active
        self.save_state()

    def sell(self, pos, sell_price, reason, pnl_pct):
        liquidity = max(2000.0, float(pos.get("liquidity_usd", 10000.0)))
        cost_usd = pos["cost_usd"]

        # AMM Sell Slippage Simulation (Asymmetric: dump/stop loss kena slippage lebih tinggi)
        if reason == "STOP_LOSS":
            sell_slippage_pct = min(5.0, 1.5 + (cost_usd / (2.0 * liquidity)) * 100.0)
        elif reason == "RUG_FLASH_CRASH":
            sell_slippage_pct = 15.0
        else:
            sell_slippage_pct = min(1.5, 0.2 + (cost_usd / (2.0 * liquidity)) * 100.0)

        effective_sell_price = sell_price * (1.0 - sell_slippage_pct / 100.0)
        gross_proceeds = pos["tokens_count"] * effective_sell_price
        
        # DEX Swap Fee (0.3%) + Gas Fee ($0.04)
        dex_fee_sell = round(gross_proceeds * 0.003, 4)
        gas_fee_sell = 0.04
        total_sell_fee = round(dex_fee_sell + gas_fee_sell, 4)

        net_proceeds = max(0.0, round(gross_proceeds - dex_fee_sell - gas_fee_sell, 4))
        
        total_fees = round(pos.get("buy_fee_usd", 0.05) + total_sell_fee, 4)
        total_slippage = round(pos.get("buy_slippage_pct", 0.2) + sell_slippage_pct, 2)
        
        profit_usd = round(net_proceeds - cost_usd, 4)
        net_pnl_pct = round(((net_proceeds - cost_usd) / cost_usd) * 100.0, 2)
        
        self.cash = round(get_wallet(self.bot_id) + net_proceeds, 2)
        
        trade_record = {
            "symbol": pos["symbol"],
            "address": pos["address"],
            "buy_price": pos["buy_price"],
            "sell_price": effective_sell_price,
            "cost_usd": cost_usd,
            "proceeds": net_proceeds,
            "profit_usd": profit_usd,
            "pnl_pct": net_pnl_pct,
            "reason": reason,
            "fee_usd": total_fees,
            "slippage_pct": total_slippage,
            "opened_at": pos.get("opened_at", time.time()),
            "closed_at": time.time()
        }
        
        add_trade(trade_record, self.bot_id)
        self.history.append(trade_record)
        set_wallet(self.cash, self.bot_id)
        
        log_event("TRADE_SELL", f"Menjual ${pos['symbol']} ({reason}) @ ${effective_sell_price:.6f} | Net PnL: {net_pnl_pct:+.2f}% (${profit_usd:+.2f}) | Fee: ${total_fees:.2f}", {
            "symbol": pos["symbol"],
            "sell_price": effective_sell_price,
            "profit_usd": profit_usd,
            "pnl_pct": net_pnl_pct,
            "reason": reason,
            "fee_usd": total_fees,
            "slippage_pct": total_slippage
        }, bot_id=self.bot_id)
        print(f"[PORTFOLIO {self.bot_id}] SELL ({reason}): {pos['symbol']} @ ${effective_sell_price:.6f} | Net PnL: ${profit_usd:+.2f} ({net_pnl_pct:+.2f}%) | Fees: ${total_fees:.2f}")

    def print_summary(self):
        self.cash = get_wallet(self.bot_id)
        self.positions = get_positions(self.bot_id)
        coin_val = sum(p.get("current_val", 0) for p in self.positions)
        total_asset = self.cash + coin_val
        slots_left = int(self.cash // Config.POSITION_SIZE)
        
        print(f"\n{'='*45}")
        print(f"[{self.bot_id.upper()}] TOTAL ASET: ${total_asset:.2f}")
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
