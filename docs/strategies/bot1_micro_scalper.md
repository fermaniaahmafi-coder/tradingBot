# Bot 1: Micro-Scalper (Hit & Run)

## 1. Filosofi & Karakteristik Persona
- **Tujuan Utama:** Mengamankan keuntungan kecil secara konsisten dan meminimalkan waktu *exposure* di pasar memecoin Solana yang rawan aksi dump kilat (*whales/dev dump*).
- **Psikologi Trading:** "Ambil profit sedikit demi sedikit asal rutin, jangan serakah menunggu pam ratusan persen."
- **Waktu Tahan Rata-rata (*Holding Time*):** 1 – 3 menit.

---

## 2. Parameter Indikator Teknikal
| Indikator | Pengaturan | Syarat BUY | Syarat SKIP / REJECT |
| :--- | :--- | :--- | :--- |
| **RSI (14)** | Rentang 0 - 100 | **40.0 s.d 68.0** | **RSI > 72.0** (Overbought/Pucuk) atau **< 35.0** (Tren Mati) |
| **EMA (9 & 21)** | Exponential Moving Average | **EMA 9 > EMA 21** (Konfirmasi Uptrend) | **EMA 9 < EMA 21** (Downtrend aktif) |
| **MACD (12, 26, 9)** | Histogram & Signal Line | **Histogram Positif** & Signal Bullish | Histogram Negatif atau Bearish Crossover |
| **Bollinger Bands** | 20 SMA, 2 Deviasi | Harga di area Middle menuju Upper | Harga sudah menembus tajam di atas Upper Band |

---

## 3. Filter Fundamental & Anti-Scam
- **Likuiditas Minimal:** $3,000 USD (bisa masuk koin baru namun tidak boleh *illiquid*).
- **Volume 24 Jam:** > $10,000 USD.
- **Pengecekan Honeypot:** Jika transaksi buy 5 menit > 10, wajib ada minimal 1 transaksi sell (`sells > 0`).
- **Rasio Transaksi (Sell/Total Txns):** Wajib antara 10% s.d 80%. Kurang dari 10% terindikasi honeypot; lebih dari 80% terindikasi dev dumping cascade.

---

## 4. Aturan Eksekusi (Risk Management)
- **Position Size:** $10.00 USD per token.
- **Target Take Profit (TP):** **+5% s.d +12%** (Default multiplier: `1.08x`).
- **Batas Stop Loss (SL):** **-5% s.d -8%** (Default multiplier: `0.94x`).
- **Hard Clamping:** Jika LLM merekomendasikan TP > 1.15, sistem otomatis memotong ke `1.12x` untuk mencegah ilusi target terlalu jauh.

---

## 5. System Prompt LLM
```text
Anda adalah bot sniper memecoin profesional yang menggunakan strategi micro-scalping (hit and run cepat) berbasis Indikator Teknikal di Solana.
Deskripsi Strategi: Quick scalp dengan TP kecil (5-10%) & SL ketat (5-8%). Wajib EMA Uptrend dan RSI 40-68.

Panduan Keputusan Khusus Bot Ini:
1. SKIP jika RSI > 72 (Overbought) atau MA Trend adalah DOWNTREND.
2. BUY jika MA Trend adalah UPTREND / Konsolidasi Sehat, MACD BULLISH, dan RSI antara 40 - 68.
3. Target Take Profit (TP): 1.05 - 1.12 (+5% s.d +12%).
4. Stop Loss (SL): 0.92 - 0.95 (-8% s.d -5%).

Format output: Valid JSON tanpa markdown blok.
```

---

## 6. Kekuatan & Kelemahan
- **Kelebihan:** 
  - Tingkat kemenangan (*win rate*) paling stabil dan tinggi.
  - Risiko drawdown modal sangat minim karena cut-loss cepat dilakukan jika pasar berbalik arah.
- **Kelemahan:**
  - Kerap melewatkan reli koin yang terbang hingga 100x lipat karena sudah take profit di awal.
