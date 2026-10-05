# Hermes Agent Knowledge Base - Trading Bot Strategy & Future Roadmap

File ini didedikasikan sebagai repositori *Knowledge Base* (Basis Pengetahuan) spesifik untuk AI / Hermes Agent yang akan melanjutkan pengembangan proyek ini.

## Strategi AI & Trading Engine
1. **Pendekatan Trading**: Micro-Scalping agresif & Hit-and-Run konservatif.
2. **Indikator Acuan**: RSI (menghindari Overbought > 75), Trend MA (menghindari Downtrend), MACD (mencari Bullish Momentum).
3. **Risk Management Override**: AI memberikan sinyal *Take Profit* (TP) dan *Stop Loss* (SL). Skrip menerapkan batasan paksa (Hard Cap) maksimal TP +10% dan SL -10% untuk mencegah halusinasi model. Eksekusi SL lebih diutamakan agar selamat dari *rugpull*.
4. **Alur Prompts (AI Prompting)**: `ai_engine.py` bertugas memaksa model untuk mematuhi output berupa JSON statis berisi saran eksekusi (BUY/SKIP, rasio TP, rasio SL).

## Roadmap Implementasi Real-Trade (On-Chain)
Jika pengguna meminta untuk mengubah bot ini dari simulasi (Paper) ke *Real Trading* Solana, agen selanjutnya HARUS mengimplementasikan hal berikut secara hati-hati:

1. **RPC Network**: 
   - Wajib ganti RPC bawaan Solana menjadi RPC berbayar/privat kecepatan tinggi seperti **Helius** atau **QuickNode**. Public node lambat dan menyebabkan kegagalan transaksi di ekosistem Memecoin.
2. **Execution Engine (Swap API)**: 
   - Hapus perhitungan matematis di `portfolio.py`, ganti dengan API Swap.
   - Gunakan **Jupiter Aggregator API v6** (`/quote` dan `/swap`).
   - Sediakan parser transaksi dan signing melalui *solana-py* dengan `Keypair` lokal (disimpan hanya di .env).
3. **MEV & Frontrunning Protection**:
   - Integrasikan **Jito Block Engine** (Tip ke validator) agar transaksi tidak tersangkut akibat *sandwich attacks*. 
   - Terapkan parameter `slippageBps` (rekomendasi 500-1500 bps atau 5-15% tergantung volatilitas token baru).
4. **Arsitektur Mode Sakelar**:
   - Manfaatkan flag di `config.py` (misal: `TRADING_MODE = 'REAL'`).
   - Pastikan database (`trading.db`) memiliki kolom tambahan untuk mencatat `tx_hash` riil.

## Panduan Debugging untuk AI Selanjutnya
- Jika dashboard web (Flask) gagal memuat atau status 500, periksa SQLite lock (`db_manager.py`). Pastikan `PRAGMA journal_mode=WAL` selalu diinisialisasi.
- Selalu uji *syntax* Python dengan `python3 -m py_compile <nama_file>.py` sebelum *restart* `trading-bot.service` untuk menghindari *exit code 1 / FAILURE* yang mematikan bot secara diam-diam.