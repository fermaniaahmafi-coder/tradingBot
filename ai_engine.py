import requests
import json
from config import Config

STRATEGIES = {
    "bot1": {
        "name": "Micro-Scalper (Hit & Run)",
        "desc": "Quick scalp dengan TP kecil (5-10%) & SL ketat (5-8%). Wajib EMA Uptrend dan RSI 40-68.",
        "default_tp": 1.08,
        "default_sl": 0.94,
        "max_tp": 1.15,
        "min_sl": 0.90,
        "prompt_rules": """
1. SKIP jika RSI > 72 (Overbought) atau MA Trend adalah DOWNTREND.
2. BUY jika MA Trend adalah UPTREND / Konsolidasi Sehat, MACD BULLISH, dan RSI antara 40 - 68.
3. Target Take Profit (TP): 1.05 - 1.12 (+5% s.d +12%).
4. Stop Loss (SL): 0.92 - 0.95 (-8% s.d -5%)."""
    },
    "bot2": {
        "name": "Breakout Momentum Hunter",
        "desc": "Mengejar volume explosion dan breakout Upper Bollinger Bands / MACD Bullish Crossover kuat.",
        "default_tp": 1.18,
        "default_sl": 0.92,
        "max_tp": 1.28,
        "min_sl": 0.88,
        "prompt_rules": """
1. SKIP jika volume 24h rendah (< $15k) atau transaksi 5m sepi.
2. BUY jika volume tinggi, MACD BULLISH kuat, dan harga menembus atau bergerak di Upper Bollinger Band dengan RSI 50 - 75.
3. Target Take Profit (TP): 1.15 - 1.25 (+15% s.d +25%).
4. Stop Loss (SL): 0.90 - 0.93 (-10% s.d -7%)."""
    },
    "bot3": {
        "name": "Mean Reversion / Dip Buyer",
        "desc": "Membeli koin oversold/pullback sehat dengan likuiditas tinggi, mengincar bounce balik.",
        "default_tp": 1.12,
        "default_sl": 0.92,
        "max_tp": 1.20,
        "min_sl": 0.88,
        "prompt_rules": """
1. SKIP jika likuiditas < $10k atau terjadi dev dump ekstrem (sells jauh mendominasi).
2. BUY jika token sedang terkoreksi / oversold (RSI antara 28 - 45) atau harga dekat Lower Bollinger Band dengan likuiditas yang solid.
3. Target Take Profit (TP): 1.08 - 1.15 (+8% s.d +15%).
4. Stop Loss (SL): 0.90 - 0.94 (-10% s.d -6%)."""
    },
    "bot4": {
        "name": "Conservative Trend Follower",
        "desc": "Sangat selektif: Likuiditas besar (> $15k), EMA 9 > 21 matang, RSI stabil 45-62 untuk win rate maksimal.",
        "default_tp": 1.12,
        "default_sl": 0.94,
        "max_tp": 1.20,
        "min_sl": 0.91,
        "prompt_rules": """
1. SKIP jika likuiditas < $15k, volume 24h < $20k, atau MA Trend bukan UPTREND jelas.
2. BUY HANYA JIKA EMA 9 > EMA 21 (Uptrend kuat), MACD BULLISH, dan RSI stabil antara 45 - 62.
3. Target Take Profit (TP): 1.08 - 1.15 (+8% s.d +15%).
4. Stop Loss (SL): 0.93 - 0.96 (-7% s.d -4%)."""
    },
    "bot5": {
        "name": "High-Risk Moonshot Sniper",
        "desc": "Membidik momentum eksplosif awal koin baru untuk target profit besar (20-40%) dengan risk-reward tinggi.",
        "default_tp": 1.25,
        "default_sl": 0.90,
        "max_tp": 1.45,
        "min_sl": 0.85,
        "prompt_rules": """
1. SKIP jika honeypot (sells = 0).
2. BUY jika ada indikasi lonjakan harga cepat (price_change_5m positif) dan MACD baru saja cross ke atas.
3. Target Take Profit (TP): 1.20 - 1.40 (+20% s.d +40%).
4. Stop Loss (SL): 0.88 - 0.92 (-12% s.d -8%)."""
    },
    "bot6": {
        "name": "Hybrid Reversion Scalper (Dip-Scalper)",
        "desc": "Kombinasi Micro-Scalper + Mean Reversion: Membeli saat pullback/dip sehat (RSI 32-52) dengan eksekusi TP cepat (5-10%) & SL ketat (5-7%).",
        "default_tp": 1.08,
        "default_sl": 0.94,
        "max_tp": 1.14,
        "min_sl": 0.91,
        "prompt_rules": """
1. SKIP jika honeypot (sells = 0) atau dev dump ekstrem (sells jauh melebihi buys).
2. BUY jika token sedang mengalami pullback/koreksi minor (RSI antara 32 - 52, atau harga di area Middle/Lower Bollinger Band) dengan likuiditas aktif (> $5k).
3. BUY juga jika terjadi konsolidasi sehat setelah penurunan minor dan mulai stabil.
4. Target Take Profit (TP): 1.05 - 1.10 (+5% s.d +10% hit-and-run cepat).
5. Stop Loss (SL): 0.93 - 0.95 (-7% s.d -5%)."""
    }
}

def analyze_token(token_info, bot_id="bot1"):
    """
    Kirim data token ke LLM untuk menentukan keputusan trading berdasarkan persona bot_id.
    """
    strat = STRATEGIES.get(bot_id, STRATEGIES["bot1"])
    
    if not Config.AI_API_KEY:
        return {
            "action": "BUY",
            "tp_multiplier": strat["default_tp"],
            "sl_multiplier": strat["default_sl"],
            "reason": f"Fallback Mock AI for {strat['name']}"
        }
    
    tech = token_info.get('technicals')
    tech_str = "Data teknikal tidak tersedia (koin terlalu baru)."
    if tech:
        tech_str = f"""
- RSI (14): {tech.get('rsi')} ({tech.get('rsi_state')})
- Trend MA (EMA 9/21): {tech.get('moving_averages', {}).get('trend')}
- MACD Trend: {tech.get('macd', {}).get('trend')}
- Bollinger Bands: {tech.get('bollinger_bands', {}).get('position')}"""

    prompt = f"""
Anda adalah bot sniper memecoin profesional Solana dengan persona strategi: **{strat['name']}**.
Deskripsi Strategi: {strat['desc']}

Analisis data token berikut:
Nama: {token_info.get('name')} ({token_info.get('symbol')})
Harga USD: {token_info.get('price_usd')}
Likuiditas USD: {token_info.get('liquidity_usd')}
Volume 24h: {token_info.get('volume_24h')}
Transaksi 5m: {token_info.get('txns_5m')}
Perubahan Harga 5m: {token_info.get('price_change_5m')}%

INDIKATOR TEKNIKAL:
{tech_str}

Panduan Keputusan Khusus Bot Ini:
{strat['prompt_rules']}

Tulis balasan HANYA dalam format JSON (tanpa markdown blok):
{{"action": "BUY", "tp_multiplier": {strat['default_tp']}, "sl_multiplier": {strat['default_sl']}, "reason": "Penjelasan singkat berdasarkan persona strategi"}}
"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {Config.AI_API_KEY}"
    }
    
    payload = {
        "model": Config.AI_MODEL,
        "messages": [
            {"role": "system", "content": "You output only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "stream": False
    }
    
    try:
        res = requests.post(f"{Config.AI_BASE_URL}/chat/completions", headers=headers, json=payload, timeout=15)
        if res.status_code == 200:
            content = res.json()["choices"][0]["message"]["content"].strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()

            result = json.loads(content)
            
            # Enforce boundary clamping according to strategy bounds
            tp = result.get("tp_multiplier")
            if isinstance(tp, (int, float)):
                if tp > strat["max_tp"]:
                    result["tp_multiplier"] = strat["max_tp"]
                elif tp < 1.02:
                    result["tp_multiplier"] = 1.05
            else:
                result["tp_multiplier"] = strat["default_tp"] if result.get("action") == "BUY" else 0
                
            sl = result.get("sl_multiplier")
            if isinstance(sl, (int, float)):
                if sl < strat["min_sl"]:
                    result["sl_multiplier"] = strat["min_sl"]
                elif sl > 0.98:
                    result["sl_multiplier"] = 0.95
            else:
                result["sl_multiplier"] = strat["default_sl"] if result.get("action") == "BUY" else 0
                
            return result
        else:
            print(f"[{bot_id.upper()} AI] Error {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[{bot_id.upper()} AI] Request error: {e}")
        
    return {"action": "SKIP", "tp_multiplier": 0, "sl_multiplier": 0, "reason": "Error calling AI"}
