# Bot 5: High-Risk Moonshot Sniper

## 1. Filosofi & Karakteristik Persona
- **Tujuan Utama:** Menembak koin yang baru terbit atau sedang mengalami kenaikan vertikal agresif demi meraih *multi-bagger returns* (keuntungan besar 20% - 40%+).
- **Psikologi Trading:** "Berani ambil risiko tinggi demi reward yang sangat besar. Biarkan beberapa trade terkena stop loss asalkan satu trade yang meledak bisa menutup semua kerugian dan menghasilkan profit melimpah (*Asymmetric Risk-Reward*)."
- **Waktu Tahan Rata-rata (*Holding Time*):** 1 – 5 menit.

---

## 2. Parameter Indikator Teknikal
| Indikator | Pengaturan | Syarat BUY | Syarat SKIP / REJECT |
| :--- | :--- | :--- | :--- |
| **Price Change 5m** | Lonjakan Kilat | **Positif (> +3% s.d +15%)** | Perubahan harga negatif atau flat |
| **MACD (12, 26, 9)** | Akselerasi | **Fresh Bullish Cross** (Baru saja berpotongan ke atas) | Bearish cross |
| **RSI (14)** | Toleransi Luas | **Toleran hingga 72.0** | RSI > 80 (Overbought parah) |
| **Bollinger Bands** | Expansion | Upper band mengembang tajam | Squeeze tanpa volume |

---

## 3. Filter Fundamental & Anti-Scam
- **Likuiditas Minimal:** $3,000 USD (fleksibel untuk koin baru meluncur di Raydium / Pump.fun).
- **Anti-Honeypot:** Wajib ada bukti transaksi jual minimal 1x (`sells > 0`) agar saldo tidak terkunci.

---

## 4. Aturan Eksekusi (Risk Management)
- **Position Size:** $10.00 USD per token.
- **Target Take Profit (TP):** **+20% s.d +40%** (Default multiplier: `1.25x`).
- **Batas Stop Loss (SL):** **-8% s.d -12%** (Default multiplier: `0.90x`).
- **Hard Clamping:** TP maksimal mencapai `1.45x` (+45%) dan SL batas bawah `0.85x` (-15%).

---

## 5. System Prompt LLM
```text
Anda adalah bot sniper memecoin profesional Solana dengan persona strategi: High-Risk Moonshot Sniper.
Deskripsi Strategi: Membidik momentum eksplosif awal koin baru untuk target profit besar (20-40%) dengan risk-reward tinggi.

Panduan Keputusan Khusus Bot Ini:
1. SKIP jika honeypot (sells = 0).
2. BUY jika ada indikasi lonjakan harga cepat (price_change_5m positif) dan MACD baru saja cross ke atas.
3. Target Take Profit (TP): 1.20 - 1.40 (+20% s.d +40%).
4. Stop Loss (SL): 0.88 - 0.92 (-12% s.d -8%).

Format output: Valid JSON tanpa markdown blok.
```

---

## 6. Kekuatan & Kelemahan
- **Kelebihan:** 
  - Potensi pertumbuhan modal tercepat saat pasar memecoin sedang banjir likuiditas.
  - Menghasilkan return persentase per transaksi terbesar di antara semua bot.
- **Kelemahan:**
  - *Win-rate* biasanya lebih rendah dan kurva ekuitas lebih berfluktuasi (*volatile*).
