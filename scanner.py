import requests
import time
from config import Config
from indicators import get_ohlcv_from_geckoterminal, calculate_technical_indicators

DEX_PROFILES_URL = "https://api.dexscreener.com/token-profiles/latest/v1"
DEX_BOOSTS_LATEST_URL = "https://api.dexscreener.com/token-boosts/latest/v1"
DEX_BOOSTS_TOP_URL = "https://api.dexscreener.com/token-boosts/top/v1"
DEX_TOKEN_URL = "https://api.dexscreener.com/latest/dex/tokens/{address}"

def get_latest_tokens(limit=15):
    try:
        endpoints = [DEX_PROFILES_URL, DEX_BOOSTS_LATEST_URL, DEX_BOOSTS_TOP_URL]
        raw_items = []
        for ep in endpoints:
            try:
                res = requests.get(ep, timeout=6)
                if res.status_code == 200:
                    raw_items.extend(res.json())
            except Exception:
                pass
                
        # Filter chain dan dedup tokenAddress
        seen_addrs = set()
        sol_addrs = []
        for p in raw_items:
            if p.get("chainId") == Config.NETWORK:
                addr = p.get("tokenAddress")
                if addr and addr not in seen_addrs:
                    seen_addrs.add(addr)
                    sol_addrs.append(addr)
                    
        # Ambil detail token
        valid_tokens = []
        for addr in sol_addrs[:limit]:
            token_info = get_token_details(addr)
            if token_info:
                valid_tokens.append(token_info)
            time.sleep(0.1)
            
        return valid_tokens
    except Exception as e:
        print(f"[SCANNER] Error fetching tokens: {e}")
        return []

def get_token_details(address):
    try:
        url = DEX_TOKEN_URL.format(address=address)
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            return None
        
        data = res.json()
        pairs = data.get("pairs")
        if not pairs or len(pairs) == 0:
            return None
        
        pair = pairs[0]
        liquidity = float(pair.get("liquidity", {}).get("usd") or 0.0)
        volume_24h = float(pair.get("volume", {}).get("h24") or 0.0)
        price_usd = float(pair.get("priceUsd") or 0.0)
        

        if liquidity < Config.MIN_LIQUIDITY or price_usd <= 0:
            return None
            
        # --- FUNDAMENTAL CHECKS ---
        txns_5m = pair.get("txns", {}).get("m5", {})
        buys = txns_5m.get("buys", 0)
        sells = txns_5m.get("sells", 0)
        total_txns = buys + sells
        
        # 1. Anti-Honeypot: Harus ada orang yang berhasil jual
        if sells == 0 and buys > 10:
            return None
            
        # 2. Rasio Jual Beli Sehat (Bukan massive dump atau honeypot)
        if total_txns > 20:
            sell_ratio = sells / total_txns
            if sell_ratio < 0.1 or sell_ratio > 0.8:
                return None
        # --------------------------
            

        # --- TECHNICAL INDICATORS ---
        pair_address = pair.get("pairAddress")
        ohlcv = get_ohlcv_from_geckoterminal(pair_address) if pair_address else []
        technicals = calculate_technical_indicators(ohlcv) if ohlcv else None
        
        return {

            "address": address,
            "pair_address": pair.get("pairAddress"),
            "name": pair.get("baseToken", {}).get("name", "Unknown"),
            "symbol": pair.get("baseToken", {}).get("symbol", "UNKNOWN"),
            "price_usd": price_usd,
            "liquidity_usd": liquidity,
            "volume_24h": volume_24h,
            "txns_5m": pair.get("txns", {}).get("m5", {}),
            "price_change_5m": float(pair.get("priceChange", {}).get("m5") or 0.0),
            "dex_url": pair.get("url"),
            "technicals": technicals
        }
    except Exception as e:
        print(f"[SCANNER] Error getting details for {address}: {e}")
        return None

def fetch_current_price(address):
    try:
        url = DEX_TOKEN_URL.format(address=address)
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            pairs = res.json().get("pairs", [])
            if pairs:
                return float(pairs[0].get("priceUsd") or 0.0)
    except Exception:
        pass
    return None
