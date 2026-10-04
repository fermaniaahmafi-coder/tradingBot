# Dokumentasi Evaluasi & Strategi (Trading Bot)

## 1. Strategi Saat Ini
- **Metode Utama:** Hit and Run (Scalping).
- **Logika:** Mengambil cuan kecil (+20% hingga +50%) dalam waktu singkat pada token memecoin baru. Posisi segera di-cut (Stop Loss ketat -15% hingga -30%) jika momentum harga melemah atau likuiditas mengering (potensi rugpull).
- **Pengambilan Keputusan:** Model DeepSeek menganalisis sentimen dari `txns_5m` (buy/sell ratio) dan perubahan harga.

## 2. Rencana Strategi Tambahan (Pertimbangan Improvement)
Berdasarkan log dan histori kegagalan (contohnya token KOTH yang dump -81% seketika), bot perlu menguji strategi sekunder:
1. **Momentum Trend-Following:** Hanya masuk jika volume 24 jam melebihi $50k dan rasio buy/sell di atas 1.5. Token tidak akan disnipe di menit pertama untuk menghindari *dev dump*.
2. **Reversal / Buy the Dip:** Membeli koin fundamental/komunitas solid yang terkoreksi wajar (bukan death spiral), dengan TP agresif di resisten pantulan.
3. **Trailing Stop Loss:** Mengubah Static SL menjadi Trailing. Jika harga sudah +30%, SL dipindah ke +10% (Break-even plus) untuk mengunci cuan.

## 3. Data Pengujian Awal (Siklus 1)
- **Token Dianalisis:** PEPE, Firm, Pergent, SPACEINU, PHILSA, KOTH, PERFIL, MRKL.
- **Tingkat *Win Rate* Awal:** Sedang dalam pemantauan (History awal menunjukkan *loss* karena belum beradaptasi dengan model anti-dump; update terkini AI berhasil menghindari KOTH dan masuk profit di PERFIL).
- **Data Historis:** Disimpan secara real-time di `trade_history.json`.
- **Log Aktivitas:** Disimpan di `activities.json`.

## 4. Rencana Pengujian Berkala
1. Bot akan dibiarkan melakukan *Paper Trading* secara terus menerus selama 24-48 jam.
2. Semua entri *TRADE_BUY* dan *TRADE_SELL* akan direkam.
3. Setelah periode uji coba, `trade_history.json` akan dievaluasi untuk melihat *Win Rate* dan menyetel parameter Trailing SL/TP secara presisi.
4. Kode kemudian akan diperbarui dan kembali di-push ke GitHub untuk versi (v1.1).
