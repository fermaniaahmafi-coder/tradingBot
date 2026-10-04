#!/bin/bash
cd /home/trading

# Cek apakah ada perubahan (kecuali file yang ada di .gitignore)
if [[ -n $(git status -s) ]]; then
    # Catat waktu saat ini
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
    
    # Tambahkan semua perubahan (terutama portfolio.json, trade_history.json, activities.json)
    git add .
    
    # Commit dengan pesan otomatis
    git commit -m "Auto-sync: Pembaruan data trading dan log ($TIMESTAMP)"
    
    # Push ke GitHub
    # Pastikan URL remote sudah menyertakan token atau SSH sudah terkonfigurasi.
    git push -u origin main
    
    echo "[$TIMESTAMP] Perubahan berhasil di-commit dan dipush ke GitHub." >> /home/trading/git_sync.log
else
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] Tidak ada perubahan baru untuk di-commit." >> /home/trading/git_sync.log
fi
