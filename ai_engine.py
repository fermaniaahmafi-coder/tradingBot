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
        "name": "Selective Dip-Scalper (Bot1+Bot3 Fusion)",
        "desc": "Fusion Bot1 Scalper + Bot3 Reversion: Entry HANYA saat uptrend terkonfirmasi (EMA 9>21) DAN pullback sehat (RSI 35-55). TP cepat 8-12%, SL ketat 5-7%. Likuiditas min $8k, blacklist token beracun.",
        "default_tp": 1.10,
        "default_sl": 0.94,
        "max_tp": 1.15,
        "min_sl": 0.91,
        "prompt_rules": """
1. SKIP jika RSI > 70 (Overbought) atau RSI < 28 (Free-fall, bukan pullback).
2. SKIP jika MA Trend adalah DOWNTREND jelas (EMA 9 < EMA 21 dengan gap lebar).
3. SKIP jika likuiditas < $8k, volume 24h < $12k, atau sells jauh mendominasi buys (dev dump).
4. SKIP jika token ada di daftar hitam internal (sudah loss 3x berturut-turut).
5. BUY HANYA JIKA SEMUA terpenuhi: (a) EMA 9 >= EMA 21 ATAU konsolidasi sehat, (b) MACD BULLISH atau baru cross-up, (c) RSI 35-55 (pullback sehat, bukan pucuk bukan jurang), (d) harga di Middle/Lower Bollinger Band area.
6. Target Take Profit (TP): 1.08 - 1.12 (+8% s.d +12% hit-and-run).
7. Stop Loss (SL): 0.93 - 0.95 (-7% s.d -5%)."""
    },
    "bot7": {
        "name": "Autonomous AI Scalper (GLM-5.2 - Aggressive Data Harvest)",
        "desc": "High-Throughput Data Harvest & Exploratory Scalper (GLM-5.2): Sizing mikro ($3-$6), slot posisi 18, filter keyakinan adaptif (>=55%), pengumpulan dataset training riil, dan perputaran modal kilat (20 menit).",
        "model": "cbai/glm-5.2",
        "default_tp": 1.09,
        "default_sl": 0.94,
        "max_tp": 1.20,
        "min_sl": 0.90,
        "default_size": 4.5,
        "prompt_rules": """
1. MODE AGGRESIF DATA HARVEST (EXPLORATORY TRAINING LOOP):
   - Tujuan utama fase ini adalah mengumpulkan ratusan variasi sampel data pasar nyata secara intensif.
   - Ambang batas keyakinan (confidence) diturunkan ke >= 55%. Loloskan sinyal yang menunjukkan potensi pantulan atau momentum awal untuk mencatat hasil statistik!
   - Sizing mikro ($3.00 - $6.00) agar portofolio dapat menampung hingga 18 posisi sekaligus tanpa kehabisan kas.
2. SINERGI INDIKATOR SCALPING (M1/M5):
   - EMA 9/21: Prioritaskan BUY saat Bullish (Harga > EMA 9 > EMA 21) atau golden cross segar.
   - Bollinger Bands (20,2): Cari diskon di Lower/Middle Band. SKIP jika harga mentok di Upper Band jenuh.
   - Stochastic Oscillator (5,3,3): Kunci konfirmasi reversal! Sinyal BUY valid saat %K memotong ke atas %D (%K > %D) dari area oversold (< 25-30).
   - RSI (14): Filter keselamatan. Loloskan jika RSI 28-60. Mutlak SKIP jika RSI > 72 (pucuk overbought) atau dump bebas tanpa volume beli.
3. ADAPTASI RENTANG JAM PASAR:
   - JAM BAHAYA (DANGER): Sizing mikro defensif ($3.00 - $4.00), SL ketat (-5%), TP kilat (+6% s.d +8%).
   - JAM EMAS (GOLDEN): Sizing optimal ($5.00 - $6.50), TP lebih lebar (+10% s.d +15%).
   - JAM NETRAL: Sizing $4.00 - $5.00, konfirmasi Stochastic %K > %D.
4. PENGAMATAN OVERSELL PASCA LOSS:
   - Jika bot atau token baru mengalami loss: AMATI sampai Stochastic %K cross-up %D di area oversold < 30. Lalu SIAP-SIAP BELI dengan sizing mikro ($3-$5) dan SL ketat.
5. TARGET TP: 1.06 - 1.18 (+6% s.d +18%), SL: 0.92 - 0.96 (-8% s.d -4%).
6. SKIP JIKA: Likuiditas < $3.5k, volume 24h < $5k, transaksi jual nol (honeypot mutlak), atau dev dump ekstrim."""
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
        stoch = tech.get('stochastic') or {}
        stoch_line = f"- Stochastic (5,3,3): %K {stoch.get('k')}, %D {stoch.get('d')} (State: {stoch.get('state')}, Trend: {stoch.get('trend')}, Bounce Reversal: {stoch.get('bounce_signal')})" if stoch else ""
        ma_info = tech.get('moving_averages', {})
        ema_details = f"EMA 9: {ma_info.get('ema_9')}, EMA 21: {ma_info.get('ema_21')}" if 'ema_9' in ma_info else ""
        tech_str = f"""
- RSI (14): {tech.get('rsi')} ({tech.get('rsi_state')})
- Trend MA (EMA 9/21): {ma_info.get('trend')} ({ema_details})
- Bollinger Bands (20,2): {tech.get('bollinger_bands', {}).get('position')}
- MACD Trend: {tech.get('macd', {}).get('trend')}
{stoch_line}"""

    learning_str = ""
    hourly_context_str = ""
    if bot_id == "bot7":
        try:
            from db_manager import get_trades, get_stats, get_current_hourly_context
            stats = get_stats(bot_id="bot7")
            trades = get_trades(5, bot_id="bot7")
            if stats.get("total_trades", 0) > 0:
                win_rate = (stats["win_count"] / stats["total_trades"] * 100)
                recent_history = []
                for t in trades[-3:]:
                    recent_history.append(f"- {t.get('symbol')}: PnL {t.get('pnl_pct', 0):+.1f}% ({t.get('reason', '')})")
                recent_lines = "\n".join(recent_history)
                learning_str = f"""
RIWAYAT BELAJAR BOT7 (Self-Reflection):
- Total Trades: {stats['total_trades']} | Win Rate: {win_rate:.1f}% | Net Profit: ${stats['total_profit']:+.2f}
- 3 Trade Terakhir:
{recent_lines}
(Gunakan evaluasi ini untuk menyesuaikan toleransi risiko & ukuran posisi Anda.)
"""
            hourly_context_str = f"\nANALISIS WAKTU & TREN JAM (WIB):\n- {get_current_hourly_context(bot_id='bot7')}\n"
        except Exception:
            pass

    if bot_id == "bot7":
        prompt = f"""
Anda adalah bot sniper memecoin profesional Solana dengan persona strategi: **{strat['name']}**.
Deskripsi Strategi: {strat['desc']}
{learning_str}
{hourly_context_str}
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
{{"action": "BUY", "position_size": 10.0, "tp_multiplier": {strat['default_tp']}, "sl_multiplier": {strat['default_sl']}, "confidence": 80, "regime": "SCALP", "reason": "Penjelasan singkat berdasarkan persona strategi"}}
"""
    else:
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
    
    ai_model = strat.get("model", Config.AI_MODEL)
    payload = {
        "model": ai_model,
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
            
            # Phase 3: Exploratory Data Harvest Guard (Confidence threshold >= 55%)
            if bot_id == "bot7" and result.get("action") == "BUY":
                confidence = result.get("confidence", 75)
                if isinstance(confidence, (int, float)) and confidence < 55:
                    result["action"] = "SKIP"
                    result["reason"] = f"Keyakinan AI {confidence}% < 55% (Di bawah batas eksplorasi data)."

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
                
            pos_size = result.get("position_size")
            if isinstance(pos_size, (int, float)):
                min_sz = 3.0 if bot_id == "bot7" else 5.0
                max_sz = 7.0 if bot_id == "bot7" else 25.0
                result["position_size"] = round(max(min_sz, min(float(pos_size), max_sz)), 2)
            else:
                result["position_size"] = strat.get("default_size", Config.POSITION_SIZE)

            # Penyesuaian Dinamis Real-Time Sesuai Rentang Jam Saat Ini untuk Bot 7
            if bot_id == "bot7" and result.get("action") == "BUY":
                try:
                    from db_manager import get_hourly_analytics
                    analytics = get_hourly_analytics(bot_id="bot7")
                    from datetime import datetime, timezone
                    now_wib_h = (datetime.now(timezone.utc).hour + 7) % 24
                    hr_info = analytics["hourly_data"][now_wib_h]
                    if hr_info.get("is_danger"):
                        # Jam Rawan Dump: Sizing mikro ketat, SL aman, TP kilat
                        result["position_size"] = min(result["position_size"], 4.0)
                        if result["sl_multiplier"] < 0.95:
                            result["sl_multiplier"] = 0.95
                        if result["tp_multiplier"] > 1.10:
                            result["tp_multiplier"] = 1.10
                    elif hr_info.get("is_golden"):
                        # Jam Emas: Boleh sizing hingga $6.50
                        result["position_size"] = min(result["position_size"], 6.5)
                except Exception:
                    pass

            return result
        else:
            print(f"[{bot_id.upper()} AI] Error {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[{bot_id.upper()} AI] Request error: {e}")
        
    return {"action": "SKIP", "tp_multiplier": 0, "sl_multiplier": 0, "reason": "Error calling AI"}
