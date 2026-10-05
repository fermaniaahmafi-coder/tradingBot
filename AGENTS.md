# Hermes Solana Sniper Bot - Project Context

Ini adalah panduan utama (Context File) untuk agen AI/Hermes di masa depan yang akan mengelola, mengembangkan, atau memperbaiki *trading bot* ini.

## Arsitektur Sistem
Bot ini menggunakan pendekatan *Paper Trading* (simulasi) berbasis AI untuk micro-scalping token memecoin di jaringan Solana.
- **Root Directory**: `/home/trading`
- **Virtual Environment**: `/home/trading/venv`
- **Service Utama**:
  1. `trading-bot.service` -> Menjalankan `main.py` (Core Engine).
  2. `trading-web.service` -> Menjalankan `web.py` (Flask Dashboard di port 5050).

## Struktur File Utama
- `main.py`: Loop utama bot (scanner -> analyze -> buy/sell -> check posisi).
- `ai_engine.py`: Terhubung dengan LLM lokal/kustom via endpoint 9router (`http://127.0.0.1:20128/v1`).
- `scanner.py`: Mengambil data teknikal & harga *real-time* via API eksternal (DexScreener, dll).
- `portfolio.py`: Pengelola saldo dan portofolio, memonitor TP/SL secara dinamis.
- `db_manager.py`: Modul koneksi ke SQLite dengan dukungan WAL (*Write-Ahead Logging*) untuk konkurensi (Bot & Web membaca secara bersamaan).
- `config.py`: File konfigurasi (modal awal, toleransi risiko, API, path file).
- `bot_logger.py`: Pencatat aktivitas (AI Sinyal, buy/sell).

## Arsitektur Database (SQLite)
Database terletak di `/home/trading/trading.db`.
- **Tabel `wallet`**: Menyimpan saldo kas/uang siap pakai.
- **Tabel `positions`**: Koin yang sedang aktif dibeli (*Open Positions*).
- **Tabel `trades`**: Riwayat *trade* yang sudah ditutup (*Closed Positions*).
- **Tabel `activities`**: Log aktivitas *real-time*.

## Operasional Harian & Pemeliharaan
- **Melihat Status**: `systemctl status trading-bot trading-web`
- **Melihat Log Bot (Realtime)**: `journalctl -u trading-bot.service -f -n 50`
- **Dashboard Web**: Di-reverse proxy oleh Nginx ke `trading.gxa.my.id` (internal port 5050).
- **Sinkronisasi Data**: Cron job (`auto_sync.sh`) mem-push data ke GitHub.

*Jika kamu Hermes, bacalah file ini sebelum mengubah logika di dalam bot agar tidak merusak flow portofolio yang sedang berjalan!*