# Bot 7: Autonomous AI Trader (GLM-5.2)

## 1. Filosofi & Arsitektur Strategi

**Next-Gen Autonomous Agent** — Lompatan dari aturan statis (Bot 1-6) menuju *Adaptive Autonomous Decision Making*:
- **LLM Backbone**: `cbai/glm-5.2` via 9router local gateway (`http://127.0.0.1:20128/v1`).
- **Dynamic Sizing ($5.00 - $25.00)**: Ukuran modal disesuaikan langsung oleh AI berdasarkan tingkat keyakinan (*conviction / confidence score* 50% - 100%).
- **Meta-Regime Switching**: AI mengidentifikasi kondisi pasar token dan memilih rezim yang optimal secara otomatis:
  1. `SCALP`: Volatilitas rendah/stabil, bid-ask teratur, target TP kilat (+5% s.d +10%).
  2. `MOMENTUM`: Breakout Upper Bollinger Bands, lonjakan volume masif, target TP agresif (+12% s.d +25%).
  3. `REVERSAL`: Koreksi sehat ke Lower BB / RSI oversold dengan volume absorbensi, target bounce back (+8% s.d +15%).
- **Self-Reflection & Continuous Learning**: Prompt secara dinamis menyertakan ringkasan performa 3-5 trade terakhir dan win-rate Bot 7 agar model dapat belajar dari kesalahan dan menyesuaikan parameter risiko saat kondisi pasar berubah.

---

## 2. Parameter Indikator & Fleksibilitas AI

| Parameter / Indikator | Rentang Adaptif | Kontrol |
|---|---|---|
| **Model AI** | `cbai/glm-5.2` (9router) | Dedicated per-bot configuration |
| **Position Sizing** | **$5.00 s/d $25.00** | Ditentukan AI via `position_size` output |
| **Target Take Profit (TP)** | **1.05x s/d 1.25x (+5% s.d +25%)** | Dinamis (Hard cap max: 1.30x) |
| **Batas Stop Loss (SL)** | **0.90x s/d 0.96x (-10% s.d -4%)** | Dinamis (Hard floor min: 0.88x) |
| **Confidence Threshold** | 50% - 100% | Digunakan untuk scaling position size |
| **Filter Likuiditas** | Min $5,000 USD | DexScreener & On-chain validation |
| **Filter Volume 24h** | Min $8,000 USD | Menghindari koin zombie |

---

## 3. Sistem Safety, Clamping & Blacklist

1. **Hard Clamping**:
   - `position_size`: Jika AI memberikan nilai di luar batas, sistem otomatis membatasi ke rentang aman [$5.00, $25.00] dan tidak pernah melebihi kas yang tersedia (`portfolio.cash`).
   - `tp_multiplier`: Dibatasi maksimum 1.30x (+30%) dan minimum 1.05x (+5%).
   - `sl_multiplier`: Dibatasi minimum 0.88x (-12%) dan maksimum 0.96x (-4%).
2. **Shared Blacklist**: Token dengan 3x loss berturut-turut otomatis diabaikan (*pre-filtered*) sebelum evaluasi AI untuk menghemat token dan komputasi LLM.
3. **Anti-Honeypot**: Token wajib memiliki transaksi penjualan (`sells > 0`) pada interval 5 menit.

---

## 4. Format Output JSON AI

```json
{
  "action": "BUY",
  "position_size": 12.50,
  "tp_multiplier": 1.12,
  "sl_multiplier": 0.93,
  "confidence": 75,
  "regime": "MOMENTUM",
  "reason": "Likuiditas $18k stabil, breakout EMA 9/21 dengan buy ratio 2:1. Sizing $12.50 mencerminkan confidence 75%."
}
```

---

## 5. System Prompt LLM

```text
Anda adalah bot sniper memecoin profesional Solana dengan persona strategi: Autonomous AI Trader (GLM-5.2).
Deskripsi Strategi: Autonomous Adaptive AI Agent didukung GLM-5.2: Dynamic sizing ($5-$25), adaptive TP/SL, meta-regime selection, dan belajar dari riwayat trade.

[RIWAYAT BELAJAR BOT7 & SELF-REFLECTION JIKA TERSEDIA]

Analisis data token berikut:
Nama: <name> (<symbol>)
Harga USD: <price>
Likuiditas USD: <liquidity>
Volume 24h: <volume>
Transaksi 5m: <txns>
Perubahan Harga 5m: <change>%

INDIKATOR TEKNIKAL:
- RSI (14)
- Trend MA (EMA 9/21)
- MACD Trend
- Bollinger Bands

Panduan Keputusan Khusus Bot Ini:
1. Analisis kondisi token secara komprehensif (Tren, Likuiditas, Volume, RSI, MACD, Bollinger Bands).
2. Tentukan Market Regime: SCALP (volatilitas stabil), MOMENTUM (breakout & lonjakan volume), atau REVERSAL (oversold bounce).
3. Tentukan ukuran posisi secara dinamis (position_size: $5.00 s/d $25.00) dan skor keyakinan (confidence: 50-100%). Sizing lebih tinggi hanya saat sinyal sangat meyakinkan.
4. Target Take Profit (TP): 1.05 - 1.25 (+5% s.d +25%).
5. Stop Loss (SL): 0.90 - 0.96 (-10% s.d -4%).
6. SKIP jika likuiditas < $5,000, volume 24h < $8,000, atau sells jauh mendominasi buys (indikasi dump).
```
