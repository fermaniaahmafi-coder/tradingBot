import requests
import time
from config import Config

DEX_PROFILES_URL = "https://api.dexscreener.com/token-profiles/latest/v1"
DEX_TOKEN_URL = "https://api.dexscreener.com/latest/dex/tokens/{address}"

def get_latest_tokens(limit=10):
    try:
        res = requests.get(DEX_PROFILES_URL, timeout=10)
        if res.status_code != 200:
            return []
        
        profiles = res.json()
        sol_tokens = [p for p in profiles if p.get("chainId") == Config.NETWORK][:limit]
        
        valid_tokens = []
        for profile in sol_tokens:
            addr = profile.get("tokenAddress")
            if not addr:
                continue
            
            token_info = get_token_details(addr)
            if token_info:
                valid_tokens.append(token_info)
            time.sleep(0.2)
            
        return valid_tokens
    except Exception as e:
        print(f"[SCANNER] Error fetching profiles: {e}")
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
            "dex_url": pair.get("url")
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
