# Hermes Solana Sniper Paper Trading Bot

## Ikhtisar (Overview)
Bot *paper trading* otomatis yang dirancang untuk melakukan *snipe* (pembelian cepat) pada token memecoin di jaringan Solana menggunakan model LLM (DeepSeek). Bot mengevaluasi metrik likuiditas, rasio *buy/sell* (`txns_5m`), dan perubahan harga untuk membuat keputusan *Take Profit* (TP) atau *Stop Loss* (SL) dinamis.

## Arsitektur Sistem
1. **Trading Engine (`main.py`, `scanner.py`, `portfolio.py`):** Modul core yang mengelola pencarian token, validasi keamanan (anti-rugpull), dan pembaruan portofolio.
2. **AI Decision Engine (`ai_engine.py`):** Menggunakan API *custom* berbasis 9router (port 20128) untuk mengeksekusi model *deepseek-chat*. AI diberikan konteks pasar 5 menit terakhir untuk memutuskan posisi `HOLD`, `SELL_TP` (Take Profit), atau `SELL_SL` (Stop Loss).
3. **Dashboard Web (`web.py`):** Dashboard berbasis Flask (port 5050) yang di-reverse proxy oleh Nginx (`trading.gxa.my.id`). Menampilkan status bot, saldo *paper trading*, riwayat transaksi, dan kontrol on/off bot.
4. **Database (`trading.db`, `db_manager.py`):** SQLite digunakan untuk menyimpan riwayat transaksi dan data performa token secara lokal yang juga di-dump ke file JSON untuk riwayat Git.

## Pengetahuan dan Strategi Bot
Berbagai strategi dan *technical indicators* (MACD, RSI, EMA, Bollinger Bands) telah diimplementasikan dalam `indicators.py`. Penjelasan mendalam mengenai metrik evaluasi awal terdapat di dalam `TEST_RESULTS.md`.

* **Tipe Strategi:** Hit and Run (Scalping), menargetkan profit +20% s/d +50%.
* **Manajemen Risiko:** Stop Loss ketat di -15% s/d -30% jika rasio tekanan jual melonjak seketika.
* **Auto-Sync Git:** Status trading secara otomatis di-commit ke Git setiap beberapa jam melalui `auto_sync.sh` untuk menyimpan riwayat (history) performa AI dalam `activities.json`, `portfolio.json`, dan `trade_history.json`.

## Menjalankan Bot
Bot dikelola melalui Systemd `trading-bot.service` dan `trading-web.service`.
Konfigurasi tersimpan pada file `.env` (di-ignore oleh git demi keamanan).
