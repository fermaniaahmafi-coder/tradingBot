import math
import requests

def get_ohlcv_from_geckoterminal(pair_address):
    try:
        url = f"https://api.geckoterminal.com/api/v2/networks/solana/pools/{pair_address}/ohlcv/minute?aggregate=5&limit=30"
        headers = {"Accept": "application/json;version=20230302"}
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
    except Exception as e:
        print(f"[INDICATOR] Error fetching OHLCV for {pair_address}: {e}")
    return []

def calculate_technical_indicators(ohlcv_list):
    if not ohlcv_list or len(ohlcv_list) < 3:
        return None
        
    sorted_candles = sorted(ohlcv_list, key=lambda x: x[0])
    closes = [float(c[4]) for c in sorted_candles]
    n = len(closes)
    curr_price = closes[-1]
    
    def calc_ema(data, span):
        k = 2 / (span + 1)
        ema = [data[0]]
        for val in data[1:]:
            ema.append((val * k) + (ema[-1] * (1 - k)))
        return ema
        
    ema_9 = calc_ema(closes, min(9, n))[-1]
    ema_21 = calc_ema(closes, min(21, n))[-1]
    
    ma_trend = 'UPTREND' if (curr_price > ema_9 and ema_9 > ema_21) else (
               'DOWNTREND' if (curr_price < ema_9 and ema_9 < ema_21) else 'CONSOLIDATING'
    )
    
    gains, losses = [], []
    for i in range(1, n):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
        
    rsi_period = min(14, len(gains))
    if rsi_period > 0:
        avg_gain = sum(gains[-rsi_period:]) / rsi_period
        avg_loss = sum(losses[-rsi_period:]) / rsi_period
        if avg_loss == 0:
            rsi = 100.0 if avg_gain > 0 else 50.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100.0 - (100.0 / (1.0 + rs))
    else:
        rsi = 50.0
        
    rsi_state = 'OVERSOLD' if rsi < 35 else ('OVERBOUGHT' if rsi > 70 else 'NEUTRAL')
    
    fast_period = min(12, max(2, n // 3))
    slow_period = min(26, max(4, (n // 3) * 2))
    sig_period = min(9, max(2, n // 4))
    
    ema_fast = calc_ema(closes, fast_period)
    ema_slow = calc_ema(closes, slow_period)
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_line = calc_ema(macd_line, sig_period)
    
    macd_val = macd_line[-1]
    macd_sig = signal_line[-1]
    macd_hist = macd_val - macd_sig
    macd_trend = 'BULLISH' if macd_val > macd_sig else 'BEARISH'
    
    bb_period = min(20, n)
    recent_closes = closes[-bb_period:]
    sma_20 = sum(recent_closes) / bb_period
    variance = sum((x - sma_20) ** 2 for x in recent_closes) / bb_period
    std_dev = math.sqrt(variance)
    
    bb_upper = sma_20 + (2 * std_dev)
    bb_lower = sma_20 - (2 * std_dev)
    
    bb_pos = 'NEAR_UPPER' if curr_price >= bb_upper * 0.95 else (
             'NEAR_LOWER' if curr_price <= bb_lower * 1.05 else 'INSIDE_BANDS'
    )
    
    # Stochastic Oscillator (5, 3, 3) for fast scalping momentum & reversal
    highs = [float(c[2]) for c in sorted_candles]
    lows = [float(c[3]) for c in sorted_candles]
    k_vals = []
    for idx in range(n):
        start_idx = max(0, idx - 5 + 1)
        hh = max(highs[start_idx : idx + 1])
        ll = min(lows[start_idx : idx + 1])
        if hh == ll:
            k = 50.0
        else:
            k = ((closes[idx] - ll) / (hh - ll)) * 100.0
        k_vals.append(k)
        
    curr_k = round(k_vals[-1], 1)
    recent_k = k_vals[-3:]
    curr_d = round(sum(recent_k) / len(recent_k), 1)
    stoch_state = 'OVERSOLD' if curr_k < 20 else ('OVERBOUGHT' if curr_k > 80 else 'NEUTRAL')
    stoch_trend = 'BULLISH' if curr_k >= curr_d else 'BEARISH'
    stoch_bounce = bool(curr_k < 35 and curr_k > curr_d)

    return {
        'candles': n,
        'rsi': round(rsi, 1),
        'rsi_state': rsi_state,
        'macd': {
            'trend': macd_trend
        },
        'moving_averages': {
            'trend': ma_trend,
            'ema_9': round(ema_9, 8),
            'ema_21': round(ema_21, 8)
        },
        'bollinger_bands': {
            'position': bb_pos
        },
        'stochastic': {
            'k': curr_k,
            'd': curr_d,
            'state': stoch_state,
            'trend': stoch_trend,
            'bounce_signal': stoch_bounce
        }
    }
