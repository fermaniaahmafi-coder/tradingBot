# Bot 6: Hybrid Reversion Scalper (Dip-Scalper)

## 1. Filosofi & Karakteristik Persona
- **Tujuan Utama:** Menghasilkan frekuensi trade yang jauh lebih tinggi daripada bot lain dengan menggabungkan dua aliran strategi: Beli saat harga sedang diskon (koreksi minor) seperti *Mean Reversion*, namun jual sangat cepat seperti *Micro-Scalper*.
- **Psikologi Trading:** "Daripada menunggu uptrend sempurna yang jarang muncul (Bot 1) atau menunggu market benar-benar jatuh berdarah-darah (Bot 3), lebih baik beli koreksi-koreksi kecil di tengah pasar yang stabil dan segera bungkus profit 5% tanpa berlama-lama."
- **Waktu Tahan Rata-rata (*Holding Time*):** 1 – 4 menit.

---

## 2. Parameter Indikator Teknikal
| Indikator | Pengaturan | Syarat BUY | Syarat SKIP / REJECT |
| :--- | :--- | :--- | :--- |
| **RSI (14)** | Shallow Dip | **32.0 s.d 52.0** (Koreksi wajar / Pullback stabil) | RSI > 55 (Bukan zona diskon) atau RSI < 30 (Dump parah) |
| **Bollinger Bands** | 20 SMA, 2 Deviasi | **Area Middle hingga Lower Band** | Harga melayang di Upper Band |
| **Volume & Likuiditas** | Aktif | **Likuiditas > $5k** | Market mati atau likuiditas mengering |

---

## 3. Filter Fundamental & Anti-Scam
- **Likuiditas Minimal:** $5,000 USD.
- **Anti-Honeypot:** Wajib ada bukti transaksi jual minimal 1x (`sells > 0`) agar saldo tidak terkunci.
- **Dev Dump Check:** Ditolak keras jika rasio *sells* terlampau mendominasi *buys* dalam 5 menit terakhir (indikasi rugpull).

---

## 4. Aturan Eksekusi (Risk Management)
- **Position Size:** $10.00 USD per token.
- **Target Take Profit (TP):** **+5% s.d +10%** (Default multiplier: `1.08x`). Eksekusi kilat (Hit-and-Run).
- **Batas Stop Loss (SL):** **-5% s.d -7%** (Default multiplier: `0.94x`). Toleransi cut-loss sangat sempit.
- **Hard Clamping:** TP maksimal mencapai `1.14x` (+14%) dan SL batas bawah `0.91x` (-9%).

---

## 5. System Prompt LLM
```text
Anda adalah bot sniper memecoin profesional Solana dengan persona strategi: Hybrid Reversion Scalper (Dip-Scalper).
Deskripsi Strategi: Kombinasi Micro-Scalper + Mean Reversion: Membeli saat pullback/dip sehat (RSI 32-52) dengan eksekusi TP cepat (5-10%) & SL ketat (5-7%).

Panduan Keputusan Khusus Bot Ini:
1. SKIP jika honeypot (sells = 0) atau dev dump ekstrem (sells jauh melebihi buys).
2. BUY jika token sedang mengalami pullback/koreksi minor (RSI antara 32 - 52, atau harga di area Middle/Lower Bollinger Band) dengan likuiditas aktif (> $5k).
3. BUY juga jika terjadi konsolidasi sehat setelah penurunan minor dan mulai stabil.
4. Target Take Profit (TP): 1.05 - 1.10 (+5% s.d +10% hit-and-run cepat).
5. Stop Loss (SL): 0.93 - 0.95 (-7% s.d -5%).

Format output: Valid JSON tanpa markdown blok.
```

---

## 6. Kekuatan & Kelemahan
- **Kelebihan:** 
  - Frekuensi open posisi (trade frequency) sangat tinggi karena kriteria entri jauh lebih rileks dan sering muncul di pasar harian (memecoin sering naik-turun dalam rentang kecil).
  - Profit kecil tapi terus menerus diakumulasi.
- **Kelemahan:**
  - Jika koreksi kecil (RSI 40) ternyata awal dari koreksi besar, bot akan sering tersentuh Stop Loss beruntun.
