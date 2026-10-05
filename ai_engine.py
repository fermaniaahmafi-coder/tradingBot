import requests
import json
from config import Config

def analyze_token(token_info):
    """
    Kirim data token ke LLM untuk menentukan apakah layak beli, TP, dan SL.
    """
    if not Config.AI_API_KEY:
        # Fallback dummy jika API key belum diset
        return {
            "action": "BUY",
            "tp_multiplier": 1.08, # TP 8%
            "sl_multiplier": 0.94, # SL 6%
            "reason": "Default AI mock logic"
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
Anda adalah bot sniper memecoin profesional yang menggunakan strategi **micro-scalping** (hit and run cepat) berbasis Indikator Teknikal di Solana.
Analisis data token berikut:
Nama: {token_info['name']} ({token_info['symbol']})
Harga USD: {token_info['price_usd']}
Likuiditas USD: {token_info['liquidity_usd']}
Volume 24h: {token_info['volume_24h']}
Transaksi 5m: {token_info['txns_5m']}
Perubahan Harga 5m: {token_info['price_change_5m']}%

INDIKATOR TEKNIKAL:
{tech_str}

Panduan Keputusan Teknikal:
1. SKIP jika RSI > 75 (Overbought / Pucuk) atau MA Trend adalah DOWNTREND.
2. BUY jika MA Trend adalah UPTREND / Konsolidasi Sehat, MACD BULLISH, dan RSI antara 40 - 68.
3. Target Take Profit (TP): 1.05 - 1.15 (+5% s.d +15%).
4. Stop Loss (SL): 0.90 - 0.95 (-10% s.d -5%).

Tulis balasan HANYA dalam format JSON (tanpa markdown blok):
{{"action": "BUY", "tp_multiplier": 1.08, "sl_multiplier": 0.94, "reason": "Penjelasan singkat berdasarkan indikator"}}
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
            content = res.json()["choices"][0]["message"]["content"]
            # Bersihkan markdown json jika ada
            if content.startswith("```json"):
                content = content[7:-3].strip()

            result = json.loads(content)
            
            # Enforce strict bounds (Risk Management Override)
            if "tp_multiplier" in result and result["tp_multiplier"] > 1.20:
                result["tp_multiplier"] = 1.10  # Max TP 10%
            if "sl_multiplier" in result and result["sl_multiplier"] < 0.85:
                result["sl_multiplier"] = 0.90  # Max SL -10%
                
            return result

        else:
            print(f"[AI] Error {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[AI] Request error: {e}")
        
    return {"action": "SKIP", "tp_multiplier": 0, "sl_multiplier": 0, "reason": "Error calling AI"}
