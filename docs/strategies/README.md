# Dokumentasi Strategi & Persona Trading Bot (Multi-Bot Architecture)

Repositori ini menjalankan 6 bot trading otomatis (Paper Trading) secara simultan di jaringan Solana dengan persona dan metodologi teknikal yang berbeda. Dokumentasi ini merinci filosofi trading, formula indikator, filter keamanan, aturan entry/exit, dan prompt LLM untuk masing-masing bot.

---

## Tabel Perbandingan Matriks Strategi

| Bot ID | Nama Persona | Filosofi Inti | Target TP | Batas SL | Filter Likuiditas | Kondisi RSI Ideal | Tren EMA (9/21) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Bot 1** | **Micro-Scalper** | Hit & run cepat, ambil cuan kecil sebelum dev dump | +5% s.d +12% | -5% s.d -8% | > $3,000 | 40 – 68 (Netral-Naik) | EMA 9 > EMA 21 (Uptrend) |
| **Bot 2** | **Breakout Momentum** | Menunggangi ledakan volume & tembusan Upper BB | +15% s.d +25% | -7% s.d -10% | > $15,000 | 50 – 75 (High Momentum) | MACD Bullish Strong |
| **Bot 3** | **Mean Reversion (Dip Buyer)** | Beli koin oversold/koreksi sehat, tunggu pantulan | +8% s.d +15% | -6% s.d -10% | > $10,000 | 28 – 45 (Oversold/Dip) | Lower Bollinger Band Bounce |
| **Bot 4** | **Conservative Trend** | Ultra selektif, likuiditas besar, win-rate tinggi | +8% s.d +15% | -4% s.d -7% | > $15,000 | 45 – 62 (Solid Stability) | EMA 9 > 21 + Volume > $20k |
| **Bot 5** | **Moonshot Sniper** | Asymmetric risk/reward, menembak pam koin baru | +20% s.d +40% | -8% s.d -12% | > $3,000 | Fleksibel (< 72) | 5m Price Spike + MACD Cross |
| **Bot 6** | **Hybrid Scalper** | Beli koreksi minor (dip), tp super cepat | +5% s.d +10% | -5% s.d -7% | > $5,000 | 32 – 52 (Pullback) | Menuju Lower BB |

---

## Indikator Teknikal Bersama (Universal Math & Rules)

Setiap bot menerima data candlestick (OHLCV) yang dihitung secara real-time dari GeckoTerminal / DexScreener:

1. **RSI (Relative Strength Index) - 14 Periode**
   - Mengukur kecepatan dan perubahan pergerakan harga.
   - Formula: $RSI = 100 - \left( \frac{100}{1 + RS} \right)$, di mana $RS = \frac{\text{Average Gain}}{\text{Average Loss}}$.
2. **EMA (Exponential Moving Average) - 9 & 21 Periode**
   - Mengidentifikasi arah tren jangka pendek vs menengah.
   - Formula: $EMA_t = \text{Price}_t \times k + EMA_{t-1} \times (1 - k)$, di mana $k = \frac{2}{N + 1}$.
   - **Uptrend:** EMA 9 berada di atas EMA 21.
   - **Downtrend:** EMA 9 berada di bawah EMA 21.
3. **Bollinger Bands (20 Periode, 2 Deviasi Standar)**
   - Mengukur volatilitas harga dan batas relatif overbought/oversold.
   - Middle Band = SMA 20, Upper/Lower Band = Middle Band $\pm (2 \times \sigma)$.
4. **MACD (Moving Average Convergence Divergence) - (12, 26, 9)**
   - MACD Line = EMA 12 - EMA 26.
   - Signal Line = EMA 9 dari MACD Line.
   - Histogram = MACD Line - Signal Line.

---

## Daftar Berkas Rinci:
- [Bot 1: Micro-Scalper (Hit & Run)](./bot1_micro_scalper.md)
- [Bot 2: Breakout Momentum Hunter](./bot2_breakout_momentum.md)
- [Bot 3: Mean Reversion / Dip Buyer](./bot3_mean_reversion_dip_buyer.md)
- [Bot 4: Conservative Trend Follower](./bot4_conservative_trend_follower.md)
- [Bot 5: High-Risk Moonshot Sniper](./bot5_high_risk_moonshot_sniper.md)
- [Bot 6: Hybrid Reversion Scalper](./bot6_hybrid_reversion_scalper.md)
