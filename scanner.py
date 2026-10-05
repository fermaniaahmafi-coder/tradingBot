import requests
import time
import os
import json
from config import Config
from indicators import get_ohlcv_from_geckoterminal, calculate_technical_indicators

DEX_PROFILES_URL = "https://api.dexscreener.com/token-profiles/latest/v1"
DEX_BOOSTS_LATEST_URL = "https://api.dexscreener.com/token-boosts/latest/v1"
DEX_BOOSTS_TOP_URL = "https://api.dexscreener.com/token-boosts/top/v1"
DEX_TOKEN_URL = "https://api.dexscreener.com/latest/dex/tokens/{address}"

CACHE_FILE = "/home/trading/tokens_cache.json"
CACHE_TTL = 25 # Seconds cache validity across all bots

def get_latest_tokens(limit=15):
    # Check shared cache first
    try:
        if os.path.exists(CACHE_FILE):
            mtime = os.path.getmtime(CACHE_FILE)
            if (time.time() - mtime) < CACHE_TTL:
                with open(CACHE_FILE, "r") as f:
                    cached_tokens = json.load(f)
                    if cached_tokens and len(cached_tokens) >= 5:
                        return cached_tokens[:limit]
    except Exception as e:
        pass

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
                
        # Filter chain & deduplicate tokenAddress
        seen_addrs = set()
        sol_addrs = []
        for p in raw_items:
            if p.get("chainId") == Config.NETWORK:
                addr = p.get("tokenAddress")
                if addr and addr not in seen_addrs:
                    seen_addrs.add(addr)
                    sol_addrs.append(addr)
                    
        # Fetch token details: iterate until enough valid tokens are collected
        valid_tokens = []
        target_count = max(limit, 12)
        for addr in sol_addrs:
            token_info = get_token_details(addr)
            if token_info:
                valid_tokens.append(token_info)
                if len(valid_tokens) >= target_count:
                    break
            time.sleep(0.04)
            
        # Save to shared cache
        if valid_tokens:
            try:
                with open(CACHE_FILE, "w") as f:
                    json.dump(valid_tokens, f)
            except Exception:
                pass

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
        
        if liquidity < 3000 or price_usd <= 0:
            return None
            
        # Anti-Honeypot: Harus ada orang yang berhasil jual
        txns_5m = pair.get("txns", {}).get("m5", {})
        buys = txns_5m.get("buys", 0)
        sells = txns_5m.get("sells", 0)
        total_txns = buys + sells
        
        if sells == 0 and buys > 10:
            return None
            
        # Healthy ratio check
        if total_txns > 20:
            sell_ratio = sells / total_txns
            if sell_ratio < 0.08 or sell_ratio > 0.85:
                return None

        # Technical Indicators
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

_price_cache = {}
def fetch_current_price(address):
    now = time.time()
    if address in _price_cache and (now - _price_cache[address]["t"]) < 4:
        return _price_cache[address]["p"]
    try:
        url = DEX_TOKEN_URL.format(address=address)
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            pairs = res.json().get("pairs", [])
            if pairs:
                p = float(pairs[0].get("priceUsd") or 0.0)
                _price_cache[address] = {"p": p, "t": now}
                return p
    except Exception:
        pass
    return None
