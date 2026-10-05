# Bot 2: Breakout Momentum Hunter

## 1. Filosofi & Karakteristik Persona
- **Tujuan Utama:** Menangkap fase ledakan harga awal saat volume transaksi dan volatilitas melonjak secara eksponensial (fase *expansion*).
- **Psikologi Trading:** "Beli koin yang sedang panas dan bervolume jumbo, tunggangi ombak kenaikan tajam lalu keluar sebelum tenaga dorong habis."
- **Waktu Tahan Rata-rata (*Holding Time*):** 3 – 10 menit.

---

## 2. Parameter Indikator Teknikal
| Indikator | Pengaturan | Syarat BUY | Syarat SKIP / REJECT |
| :--- | :--- | :--- | :--- |
| **Bollinger Bands** | 20 SMA, 2 Deviasi | **Breakout Upper Band** (Harga menembus Upper Band dengan *expansion*) | Squeeze datar / harga berada di bawah Middle SMA |
| **Volume 24 Jam** | Likuiditas & Turnover | **Tinggi (> $25,000 USD)** | Volume rendah / token sepi peminat |
| **MACD (12, 26, 9)** | Momentum | **Strong Bullish Crossover** (Histogram meluas ke atas) | Histogram mulai melandai atau tren bear |
| **RSI (14)** | Rentang Momentum | **50.0 s.d 75.0** (Momentum kuat namun belum ekstrem 90+) | RSI < 45 (tidak ada dorongan beli) |

---

## 3. Filter Fundamental & Anti-Scam
- **Likuiditas Minimal:** $15,000 USD (membutuhkan kolam likuiditas cukup dalam agar slippage tidak merusak eksekusi breakout).
- **Aktivitas 5 Menit:** Jumlah transaksi (`txns_5m`) harus aktif dengan rasio beli dominan.
- **Perubahan Harga 5m:** Lebih besar dari 0% dan menunjukkan tren akselerasi harga.

---

## 4. Aturan Eksekusi (Risk Management)
- **Position Size:** $10.00 USD per token.
- **Target Take Profit (TP):** **+15% s.d +25%** (Default multiplier: `1.18x`).
- **Batas Stop Loss (SL):** **-7% s.d -10%** (Default multiplier: `0.92x`).
- **Hard Clamping:** Batas maksimum TP dibatasi pada `1.28x` dan toleransi SL minimum di `0.88x`.

---

## 5. System Prompt LLM
```text
Anda adalah bot sniper memecoin profesional Solana dengan persona strategi: Breakout Momentum Hunter.
Deskripsi Strategi: Mengejar volume explosion dan breakout Upper Bollinger Bands / MACD Bullish Crossover kuat.

Panduan Keputusan Khusus Bot Ini:
1. SKIP jika volume 24h rendah (< $15k) atau transaksi 5m sepi.
2. BUY jika volume tinggi, MACD BULLISH kuat, dan harga menembus atau bergerak di Upper Bollinger Band dengan RSI 50 - 75.
3. Target Take Profit (TP): 1.15 - 1.25 (+15% s.d +25%).
4. Stop Loss (SL): 0.90 - 0.93 (-10% s.d -7%).

Format output: Valid JSON tanpa markdown blok.
```

---

## 6. Kekuatan & Kelemahan
- **Kelebihan:** 
  - Keuntungan per trade jauh lebih besar dibanding scalper biasa.
  - Sangat efektif saat kondisi pasar Solana sedang ramai (*bullish alt season*).
- **Kelemahan:**
  - Rawan terkena *fakeout* (breakout palsu yang langsung dibanting oleh whale).
