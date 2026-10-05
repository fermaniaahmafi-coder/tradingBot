# Bot 6: Selective Dip-Scalper (Fusion Bot1 + Bot3)

## 1. Filosofi & Evolusi Strategi

**Versi Baru** — Fusion dari dua strategi yang terbukti profit di testing 382 trades:
- **Bot1 (Micro-Scalper)**: +18.6% ROI, win rate 50% — entry saat uptrend dengan TP cepat
- **Bot3 (Mean Reversion)**: +19.8% ROI, win rate 46% — entry saat pullback dengan high frequency

**Masalah Bot6 Lama yang Diperbaiki:**
1. Entry terlalu longgar — "konsolidasi sehat" tanpa konfirmasi trend = beli di tengah kejatuhan
2. Tidak ada blacklist — terus beli token yang sudah loss berkali-kali (Trojan, DAFTPUNK51, dll)
3. RSI range 32-52 terlalu lebar — masih bisa kena free-fall

**Psikologi Baru:**
> "Hanya entry saat SEMUA kondisi terpenuhi: uptrend terkonfirmasi + pullback sehat + bukan token beracun. Kualitas over kuantitas."

---

## 2. Parameter Indikator Teknikal

| Indikator | Pengaturan | Syarat BUY | Syarat SKIP |
|-----------|------------|------------|-------------|
| **RSI (14)** | Pullback Zone | **35.0 - 55.0** | RSI > 70 (overbought) atau RSI < 28 (free-fall) |
| **EMA 9/21** | Trend Filter | EMA 9 >= EMA 21 atau konsolidasi sehat | Downtrend jelas (gap lebar) |
| **MACD** | Momentum | BULLISH atau baru cross-up | BEARISH |
| **Bollinger Bands** | Position | Middle/Lower Band area | Upper Band (sudah naik) |
| **Volume 24h** | Min | > $12,000 | < $12,000 |
| **Likuiditas** | Min | > $8,000 | < $8,000 |

---

## 3. Filter Fundamental & Anti-Scam

- **Likuiditas Minimal:** $8,000 USD (naik dari $5k)
- **Volume 24h Minimal:** $12,000 USD
- **Anti-Honeypot:** Wajib ada transaksi jual (`sells > 0`)
- **Dev Dump Check:** Ditolak jika sells jauh mendominasi buys
- **BLACKLIST:** Token dengan 3+ consecutive losses otomatis di-skip (shared across semua bot)

---

## 4. Aturan Eksekusi (Risk Management)

- **Position Size:** $10.00 USD per token
- **Target Take Profit (TP):** **+8% s.d +12%** (Default: `1.10x`)
- **Batas Stop Loss (SL):** **-5% s.d -7%** (Default: `0.94x`)
- **Hard Clamping:** TP max `1.15x` (+15%), SL min `0.91x` (-9%)

---

## 5. System Prompt LLM

```text
Anda adalah bot sniper memecoin profesional Solana dengan persona strategi: Selective Dip-Scalper (Bot1+Bot3 Fusion).
Deskripsi Strategi: Fusion Bot1 Scalper + Bot3 Reversion: Entry HANYA saat uptrend terkonfirmasi (EMA 9>21) DAN pullback sehat (RSI 35-55). TP cepat 8-12%, SL ketat 5-7%. Likuiditas min $8k, blacklist token beracun.

Panduan Keputusan Khusus Bot Ini:
1. SKIP jika RSI > 70 (Overbought) atau RSI < 28 (Free-fall, bukan pullback).
2. SKIP jika MA Trend adalah DOWNTREND jelas (EMA 9 < EMA 21 dengan gap lebar).
3. SKIP jika likuiditas < $8k, volume 24h < $12k, atau sells jauh mendominasi buys (dev dump).
4. SKIP jika token ada di daftar hitam internal (sudah loss 3x berturut-turut).
5. BUY HANYA JIKA SEMUA terpenuhi: (a) EMA 9 >= EMA 21 ATAU konsolidasi sehat, (b) MACD BULLISH atau baru cross-up, (c) RSI 35-55 (pullback sehat), (d) harga di Middle/Lower Bollinger Band area.
6. Target Take Profit (TP): 1.08 - 1.12 (+8% s.d +12%).
7. Stop Loss (SL): 0.93 - 0.95 (-7% s.d -5%).

Format output: Valid JSON tanpa markdown blok.
```

---

## 6. Blacklist System

**Cara Kerja:**
- Setiap trade yang loss menambah counter token tersebut
- Win mereset counter ke 0
- Token dengan counter >= 3 masuk blacklist
- Blacklist dicek SEBELUM AI analysis (hemat API call)
- Disimpan di `token_blacklist.json` (shared across semua bot)

**Blacklist Awal (dari data testing):**
- TIT, DAFTPUNK51, LLM, RELAY, solOS (5 losses)
- Trojan (4 losses)
- BOND, SH, RESCUE, PUE, Web, Bob, lemonbob (3 losses)

---

## 7. Kekuatan & Kelemahan

**Kelebihan:**
- Selektif — hanya entry saat kondisi optimal
- Blacklist mencegah kerugian berulang dari token beracun
- Gabungan kekuatan Bot1 (trend) + Bot3 (pullback)
- Higher win rate expected (target > 50%)

**Kelemahan:**
- Frekuensi trade lebih rendah (lebih selektif)
- Mungkin melewatkan beberapa peluang di sideways market

---

## 8. Metrik Evaluasi (Target 1 Minggu)

- Win rate > 50%
- Total P/L positif
- Max drawdown < 15%
- Blacklist hit rate (berapa token berbahaya berhasil dihindari)
- Sharpe ratio > 1.0
