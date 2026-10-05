# Roadmap Pengembangan Monetra Solana AI Trading Bot

Dokumen ini adalah panduan strategis (master blueprint) pengembangan jangka pendek, menengah, dan panjang untuk proyek **Monetra Solana AI Sniper Bot**. Dokumen ini memastikan pengembangan di server VPS maupun lingkungan lokal (*local development*) tetap selaras, terstruktur, dan terukur.

---

## Ringkasan Tahapan Pengembangan

```text
[Fase 1: Pondasi & A/B Multi-Bot]  ===> SELESAI (Aktif)
       │
[Fase 2: Analitik Lanjutan & Auto-Prompt Tuning] ===> JANGKA PENDEK (1 - 2 Minggu)
       │
[Fase 3: Real-Time Stream & On-Chain Security] ===> JANGKA MENENGAH (1 Bulan)
       │
[Fase 4: Transisi Mainnet & Eksekusi Wallet Riil] ===> JANGKA PANJANG (2 - 3 Bulan)
       │
[Fase 5: Ekosistem, Telegram Bot & Mobile Alerts] ===> FINISHING & SCALING
```

---

## Fase 1: Pondasi Multi-Bot & Paper Trading (Status: SELESAI)
> **Fokus:** Validasi logika, kestabilan infrastruktur, dan isolasi data.

- [x] **Arsitektur 6 Persona Bot Simultan:**
  - Bot 1 (Micro-Scalper), Bot 2 (Breakout Momentum), Bot 3 (Dip Buyer), Bot 4 (Conservative Trend), Bot 5 (Moonshot Sniper), Bot 6 (Hybrid Reversion Scalper).
- [x] **Shared Market Cache & Rate-Limit Shield:**
  - Mengurangi beban request ke DexScreener dan GeckoTerminal dengan TTL cache 25 detik.
- [x] **Isolasi Database & Multi-Service Systemd:**
  - Database SQLite independen (`trading_botX.db`) dengan WAL mode untuk performa konkurensi tinggi.
- [x] **Web Dashboard dengan Switcher Real-Time:**
  - Dashboard Flask interaktif untuk memilih dan memantau status kelima bot secara terpisah.
- [x] **Automated Git Synchronization:**
  - Sinkronisasi riwayat transaksi dan log secara berkala ke repositori GitHub.

---

## Fase 2: Analitik Lanjutan & Optimasi Prompt AI (Jangka Pendek: 1 - 2 Minggu)
> **Fokus:** Mengolah hasil trade menjadi data evaluasi matematis dan melatih respon AI agar semakin presisi.

### 1. Leaderboard & Auto-Ranking System
- [ ] Menambahkan halaman khusus **"Leaderboard Tournament"** di Web UI untuk membandingkan metrik penting antar bot:
  - *Sharpe Ratio* (Rasio imbal hasil terhadap risiko).
  - *Profit Factor* (Gross Win dibagi Gross Loss).
  - *Maximum Drawdown* (% penurunan modal terbesar dari puncak).
  - *Average Holding Time* dan *Win/Loss Streaks*.

### 2. Evaluator Kinerja Harian Berbasis LLM
- [ ] Membuat modul *Daily Strategy Auditor*: Setiap 24 jam sekali, LLM menganalisis transaksi rugi (Loss) dan otomatis memberi saran perbaikan bobot indikator (misal: "RSI cut-off pada Bot 2 perlu diturunkan dari 75 ke 70").
- [ ] Dataset Curation: Menyimpan riwayat prompt + data teknikal + hasil trade ke format JSONL standar untuk persiapan *fine-tuning* model lokal.

### 3. Dynamic Volatility Adjustment (ATR)
- [ ] Mengintegrasikan indikator **ATR (Average True Range)** ke dalam kalkulasi:
  - Jika volatilitas pasar Solana sedang sangat liar, target TP dan SL secara dinamis diperlebar.
  - Jika pasar sedang stagnan (*low volume*), target dipersempit agar modal tidak terkunci lama.

---

## Fase 3: Real-Time Stream & On-Chain Security (Jangka Menengah: 1 Bulan)
> **Fokus:** Mengurangi latensi pemindaian data dan memperketat filter anti-scam.

### 1. Transisi dari Polling HTTP ke WebSocket / gRPC Feed
- [ ] Mengganti polling API berkala dengan WebSocket stream (Raydium / Pump.fun live new pools stream via Helius atau QuickNode).
- [ ] Latensi pendeteksian koin berkurang dari 10-15 detik menjadi sub-detik (< 500ms).

### 2. On-Chain Deep Forensic (Filter Scam Tingkat Lanjut)
- [ ] **Top 10 Holders Concentration Check:** Menolak koin jika 10 dompet teratas menguasai lebih dari 30% suplai koin (mencegah dump paus).
- [ ] **Mint & Freeze Authority Check:** Memastikan *Mint Authority* dan *Freeze Authority* sudah dinonaktifkan (*revoked*).
- [ ] **LP Burn / Lock Verification:** Memastikan likuiditas pool di Raydium sudah di-burn 100% atau dikunci di kontrak lock terpercaya.
- [ ] **Dev Wallet Profiling:** Mendeteksi riwayat dompet developer pembuat koin (apakah pernah melakukan rugpull pada proyek sebelumnya).

---

## Fase 4: Transisi Mainnet & Eksekusi Wallet Riil (Jangka Panjang: 2 - 3 Bulan)
> **Fokus:** Eksekusi transaksi nyata di blockchain Solana dengan manajemen risiko modal yang aman.

### 1. Integrasi Solana Web3 & DEX Aggregator SDK
- [ ] Integrasi modul `solana-py` / `solders` dan Jupiter Swap API v6.
- [ ] Pengaturan **Dynamic Slippage & Priority Fees** untuk memastikan transaksi masuk ke blok berikutnya tanpa gagal (*slippage protection*).
- [ ] Implementasi **Jito MEV Tip** untuk melindungi transaksi dari serangan *sandwich bots* / front-running.

### 2. Arsitektur Keamanan Dompet (Private Key Safety)
- [ ] Manajemen kunci terenkripsi (*Encrypted Key Vault*) berbasis AES-256; tidak menyimpan private key dalam bentuk *plain-text* di `.env`.
- [ ] Fitur **Circuit Breaker (Kill Switch Otomatis):**
  - Jika terjadi kerugian kumulatif harian mencapai batas tertentu (misal -8% dari total balance), seluruh bot otomatis berhenti beroperasi (*hard stop*) dan menarik seluruh posisi ke USDC/SOL.

### 3. Dual-Mode Execution (Paper vs Live)
- [ ] Setiap bot dapat dialihkan statusnya antara `PAPER_TRADING` dan `LIVE_MAINNET` secara mandiri melalui tombol switch di Web UI.

---

## Fase 5: Notifikasi & Ekosistem Terdistribusi (Finishing)
> **Fokus:** Kemudahan monitoring di mana saja dan portabilitas deployment lokal/cloud.

### 1. Telegram & Discord Alert Bot
- [ ] Notifikasi instan saat bot mengeksekusi BUY atau SELL (beserta link Solscan/Birdeye dan grafik PnL).
- [ ] Perintah interaktif via chat: `/status`, `/stop bot2`, `/leaderboard`, `/balance`.

### 2. Kontainerisasi Lengkap (Docker Compose Multi-Environment)
- [ ] Menyediakan satu file `docker-compose.yml` terpadu:
  - Service `bot-engine` (Python Core)
  - Service `web-dashboard` (UI)
  - Service `redis-cache` (pengganti file json cache)
- [ ] Pengembang lokal cukup menjalankan `docker compose up -d` untuk mereplikasi lingkungan server VPS dalam hitungan detik.

---

## Standar Kontribusi & Sinkronisasi Kode (*Contributor Guidelines*)
Untuk menjaga agar kode tetap bersih dan tidak konflik saat dikembangkan di lokal:
1. **Branching Strategy:** Buat branch fitur dari `main` (misal: `feat/telegram-bot` atau `feat/onchain-filter`).
2. **Environment Isolation:** Jangan pernah men-commit file database SQLite (`*.db*`), file token cache (`tokens_cache.json`), atau file kredensial (`.env`).
3. **Prompt Purity:** Setiap perubahan prompt pada `ai_engine.py` wajib didokumentasikan pada folder `/docs/strategies/`.
