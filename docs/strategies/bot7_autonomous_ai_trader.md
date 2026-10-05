# Bot 7: Autonomous AI Scalper (GLM-5.2)

## 1. Filosofi & Arsitektur Strategi

**Next-Gen Adaptive Scalper** — Menggabungkan kecerdasan `cbai/glm-5.2` dengan formula 4 indikator teknikal scalping terbaik (M1/M5) serta mekanisme *Anti-Paralysis Momentum Evaluation*:
- **LLM Backbone**: `cbai/glm-5.2` via 9router local gateway (`http://127.0.0.1:20128/v1`).
- **Dynamic Sizing ($5.00 - $25.00)**: Ukuran modal disesuaikan langsung oleh AI berdasarkan tingkat keyakinan (*conviction / confidence score* 50% - 100%).
- **Sinergi 4 Indikator Scalping M1/M5**:
  1. `EMA 9/21`: Menentukan bias tren utama dan support dinamis (prioritas BUY saat Bullish: Harga > EMA 9 > EMA 21).
  2. `Bollinger Bands (20, 2)`: Mengukur volatilitas dan mendeteksi pantulan diskon di Lower/Middle Band.
  3. `Stochastic Oscillator (5, 3, 3)`: Trigger pembalikan momentum cepat. Sinyal kuat saat %K menembus ke atas %D (%K > %D) dari area oversold (< 25-30).
  4. `RSI (14)`: Filter keselamatan agar tidak membeli di area jenuh beli (> 70) atau free-fall tanpa support (< 25).
- **Anti-Paralysis (Evaluasi Momentum Pasca-Loss)**:
  Jika token atau bot sedang mengalami riwayat loss beruntun, sistem **tidak menghentikan aksi beli**. Apabila 2–3 indikator momentum di atas terkonfirmasi valid, bot tetap mengeksekusi BUY dengan sizing terukur ($5.00 - $8.00) dan Stop Loss ketat (3-6%).

---

## 2. Parameter Indikator & Fleksibilitas AI

| Parameter / Indikator | Pengaturan & Logika | Kontrol & Aksi |
|---|---|---|
| **Model AI** | `cbai/glm-5.2` (9router) | Dedicated per-bot configuration |
| **EMA 9/21** | Period 9 & 21 | Bias Uptrend jika Harga > EMA 9 > 21 |
| **Bollinger Bands** | 20 SMA, 2 StdDev | Pantulan Lower/Middle Band untuk entry murah |
| **Stochastic Oscillator** | (5, 3, 3) | Trigger buy saat %K cross-up %D di area oversold |
| **RSI (14)** | 14 Period | Wajib 35 - 65 untuk entry sehat (hindari > 70) |
| **Position Sizing** | **$5.00 s/d $25.00** | Ditentukan AI via `position_size` output |
| **Target Take Profit (TP)** | **1.05x s/d 1.25x (+5% s.d +25%)** | Dinamis (Hard cap max: 1.28x) |
| **Batas Stop Loss (SL)** | **0.90x s/d 0.96x (-10% s.d -4%)** | Dinamis (Hard floor min: 0.88x) |
| **Filter Likuiditas** | Min $5,000 USD | DexScreener & On-chain validation |
| **Filter Volume 24h** | Min $8,000 USD | Menghindari koin zombie |

---

## 3. Sistem Safety, Cooldown & Momentum Override

1. **Cooldown Timer (1 Jam TTL)**:
   - Token yang mengalami 3x loss beruntun tidak diblokir selamanya. Setelah 1 jam, status blacklist kedaluwarsa dan token berhak discan kembali.
2. **Momentum Override**:
   - Sekalipun token masih dalam daftar blacklist, jika scanner mendeteksi minimal 2 konfirmasi momentum teknikal (misal: Stochastic Cross-Up + EMA Uptrend + BB Lower Bounce + RSI sehat), token otomatis diizinkan untuk dievaluasi oleh AI.
3. **Hard Clamping**:
   - `position_size`: Dibatasi ke rentang aman [$5.00, $25.00] dan tidak pernah melebihi kas yang tersedia (`portfolio.cash`).
   - `tp_multiplier`: 1.05x - 1.28x.
   - `sl_multiplier`: 0.88x - 0.96x.

---

## 4. Format Output JSON AI

```json
{
  "action": "BUY",
  "position_size": 10.00,
  "tp_multiplier": 1.10,
  "sl_multiplier": 0.94,
  "confidence": 78,
  "regime": "SCALP",
  "reason": "Setup reversal valid: Stochastic oversold bounce (%K 22.5 > %D 18.2) konfirmasi bullish cross, EMA 9>21 uptrend, BB near lower band support. RSI 42 sehat."
}
```
