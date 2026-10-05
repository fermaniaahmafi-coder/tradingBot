# Bot 4: Conservative Trend Follower

## 1. Filosofi & Karakteristik Persona
- **Tujuan Utama:** Menghindari risiko semaksimal mungkin dengan hanya mengeksekusi token yang telah terbukti memiliki tren naik solid, likuiditas besar, dan volume tinggi.
- **Psikologi Trading:** "Kualitas di atas kuantitas. Lebih baik tidak trading seharian daripada masuk ke koin abal-abal yang berisiko tinggi."
- **Waktu Tahan Rata-rata (*Holding Time*):** 5 – 15 menit.

---

## 2. Parameter Indikator Teknikal
| Indikator | Pengaturan | Syarat BUY | Syarat SKIP / REJECT |
| :--- | :--- | :--- | :--- |
| **EMA (9 & 21)** | Golden Trend | **EMA 9 > EMA 21 (Uptrend Kuat)** dengan jarak garis yang konsisten | EMA 9 di bawah EMA 21 atau garis saling silang tak beraturan |
| **RSI (14)** | Zona Stabil | **45.0 s.d 62.0** (Kondisi akumulasi sehat tanpa overbought) | RSI > 65 atau RSI < 40 |
| **MACD (12, 26, 9)** | Konfirmasi Tren | **MACD Line > Signal Line & Histogram > 0** | MACD Bearish Divergence |
| **Bollinger Bands** | 20 SMA, 2 Deviasi | Harga bergerak stabil di antara Middle dan Upper Band | Volatilitas ekstrem tak terkendali |

---

## 3. Filter Fundamental & Anti-Scam
- **Likuiditas Minimal:** **$15,000 s.d $20,000 USD** (Standar likuiditas tertinggi di antara semua bot).
- **Volume 24 Jam:** **> $25,000 USD**.
- **Healthy Txns Distribution:** Rasio pembeli harus mendominasi (> 55% buy orders).

---

## 4. Aturan Eksekusi (Risk Management)
- **Position Size:** $10.00 USD per token.
- **Target Take Profit (TP):** **+8% s.d +15%** (Default multiplier: `1.12x`).
- **Batas Stop Loss (SL):** **-4% s.d -7%** (Default multiplier: `0.94x`).
- **Hard Clamping:** TP maksimal `1.20x`, SL paling ketat minimal `0.91x`.

---

## 5. System Prompt LLM
```text
Anda adalah bot sniper memecoin profesional Solana dengan persona strategi: Conservative Trend Follower.
Deskripsi Strategi: Sangat selektif: Likuiditas besar (> $15k), EMA 9 > 21 matang, RSI stabil 45-62 untuk win rate maksimal.

Panduan Keputusan Khusus Bot Ini:
1. SKIP jika likuiditas < $15k, volume 24h < $20k, atau MA Trend bukan UPTREND jelas.
2. BUY HANYA JIKA EMA 9 > EMA 21 (Uptrend kuat), MACD BULLISH, dan RSI stabil antara 45 - 62.
3. Target Take Profit (TP): 1.08 - 1.15 (+8% s.d +15%).
4. Stop Loss (SL): 0.93 - 0.96 (-7% s.d -4%).

Format output: Valid JSON tanpa markdown blok.
```

---

## 6. Kekuatan & Kelemahan
- **Kelebihan:** 
  - Memiliki persentase kerugian (*drawdown*) paling kecil.
  - Sangat cocok untuk mengelola modal nyata dalam jumlah besar.
- **Kelemahan:**
  - Frekuensi trade rendah (*jarang open posisi*) karena kriteria seleksi yang sangat ketat.
