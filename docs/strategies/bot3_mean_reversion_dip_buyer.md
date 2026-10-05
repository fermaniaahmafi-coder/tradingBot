# Bot 3: Mean Reversion / Dip Buyer

## 1. Filosofi & Karakteristik Persona
- **Tujuan Utama:** Membeli aset yang sedang mengalami koreksi harga sesaat (*panic dip / pullback*) yang berlebihan, lalu menjualnya saat harga memantul kembali ke nilai wajarnya (*mean reversion*).
- **Psikologi Trading:** "Beli saat orang lain panik menjual koin yang fundamentalnya masih bagus, lalu jual saat pantulan teknikal terjadi."
- **Waktu Tahan Rata-rata (*Holding Time*):** 2 – 6 menit.

---

## 2. Parameter Indikator Teknikal
| Indikator | Pengaturan | Syarat BUY | Syarat SKIP / REJECT |
| :--- | :--- | :--- | :--- |
| **RSI (14)** | Oversold Range | **28.0 s.d 45.0** (Area jenuh jual yang bersiap memantul) | RSI > 55 (sudah terlampau naik, bukan harga diskon) |
| **Bollinger Bands** | 20 SMA, 2 Deviasi | **Menyentuh atau Dekat Lower Band** | Harga berada di Upper Band |
| **EMA Support** | EMA 9 vs EMA 21 | Harga mulai menahan penurunan di area support | Downtrend ekstrem dengan volume jual membesar terus-menerus |
| **MACD (12, 26, 9)** | Reversal Signal | Histogram negatif mulai mengecil (indikasi pelemahan tekanan jual) | Histogram terus melebar tajam ke bawah |

---

## 3. Filter Fundamental & Anti-Scam
- **Likuiditas Minimal:** $10,000 USD (wajib likuiditas stabil agar tidak ambles ke 0).
- **Volume 24 Jam:** > $15,000 USD.
- **Deteksi Dev Dumping:** Memastikan penurunan harga bukan karena *rug pull* developer, melainkan aksi *profit taking* ritel biasa.

---

## 4. Aturan Eksekusi (Risk Management)
- **Position Size:** $10.00 USD per token.
- **Target Take Profit (TP):** **+8% s.d +15%** (Default multiplier: `1.12x`).
- **Batas Stop Loss (SL):** **-6% s.d -10%** (Default multiplier: `0.92x`).
- **Hard Clamping:** TP maksimal `1.20x`, SL minimal `0.88x`.

---

## 5. System Prompt LLM
```text
Anda adalah bot sniper memecoin profesional Solana dengan persona strategi: Mean Reversion / Dip Buyer.
Deskripsi Strategi: Membeli koin oversold/pullback sehat dengan likuiditas tinggi, mengincar bounce balik.

Panduan Keputusan Khusus Bot Ini:
1. SKIP jika likuiditas < $10k atau terjadi dev dump ekstrem (sells jauh mendominasi).
2. BUY jika token sedang terkoreksi / oversold (RSI antara 28 - 45) atau harga dekat Lower Bollinger Band dengan likuiditas yang solid.
3. Target Take Profit (TP): 1.08 - 1.15 (+8% s.d +15%).
4. Stop Loss (SL): 0.90 - 0.94 (-10% s.d -6%).

Format output: Valid JSON tanpa markdown blok.
```

---

## 6. Kekuatan & Kelemahan
- **Kelebihan:** 
  - Mendapatkan harga masuk (*entry price*) yang sangat murah dibanding bot lain.
  - Risiko terbeli di pucuk (*buying at top*) praktis nol.
- **Kelemahan:**
  - Jika koin ternyata mengalami *rug pull* total, koreksi tidak akan pernah memantul (*catching a falling knife*).
