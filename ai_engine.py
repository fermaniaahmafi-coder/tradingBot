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
            "tp_multiplier": 1.2, # TP 20%
            "sl_multiplier": 0.8, # SL 20%
            "reason": "Default AI mock logic"
        }
    
    prompt = f"""
Anda adalah bot sniper memecoin profesional yang menggunakan strategi hit and run di Solana.
Analisis data token berikut:
Nama: {token_info['name']} ({token_info['symbol']})
Harga USD: {token_info['price_usd']}
Likuiditas USD: {token_info['liquidity_usd']}
Volume 24h: {token_info['volume_24h']}
Transaksi 5m: {token_info['txns_5m']}
Perubahan Harga 5m: {token_info['price_change_5m']}%

Berdasarkan volatilitas memecoin dan strategi snipe, tentukan:
1. ACTION: BUY atau SKIP
2. TP_MULTIPLIER: contoh 1.5 untuk take profit di +50%
3. SL_MULTIPLIER: contoh 0.7 untuk stop loss di -30%
4. REASON: Penjelasan singkat.

Tulis balasan HANYA dalam format JSON:
{{"action": "BUY", "tp_multiplier": 1.5, "sl_multiplier": 0.7, "reason": "..."}}
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
            return json.loads(content)
        else:
            print(f"[AI] Error {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[AI] Request error: {e}")
        
    return {"action": "SKIP", "tp_multiplier": 0, "sl_multiplier": 0, "reason": "Error calling AI"}
