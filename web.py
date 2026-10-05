from db_manager import get_wallet, set_wallet, get_positions, save_positions, get_trades, get_recent_activities, reset_db
import os
import json
import subprocess
from flask import Flask, jsonify, request, render_template_string
from config import Config
from bot_logger import log_event, get_recent_logs

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hermes Trading Sniper</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0b0f19;
            --surface: #121826;
            --surface-hover: #182235;
            --border: #1e293b;
            --border-light: #2d3748;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --emerald: #10b981;
            --emerald-bg: rgba(16, 185, 129, 0.12);
            --rose: #f43f5e;
            --rose-bg: rgba(244, 63, 94, 0.12);
            --amber: #f59e0b;
            --amber-bg: rgba(245, 158, 11, 0.12);
            --blue: #3b82f6;
            --blue-bg: rgba(59, 130, 246, 0.12);
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: var(--bg);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 24px 16px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        /* Top Header */
        header {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 24px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
        }

        .header-brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo-badge {
            background: linear-gradient(135deg, #6366f1 0%, #3b82f6 100%);
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }

        .brand-title {
            font-size: 20px;
            font-weight: 700;
            letter-spacing: -0.02em;
        }

        .brand-subtitle {
            font-size: 13px;
            color: var(--text-secondary);
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            border: 1px solid transparent;
        }

        .status-pill.running {
            background-color: var(--emerald-bg);
            color: var(--emerald);
            border-color: rgba(16, 185, 129, 0.3);
        }

        .status-pill.stopped {
            background-color: var(--rose-bg);
            color: var(--rose);
            border-color: rgba(244, 63, 94, 0.3);
        }

        .pulse-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: currentColor;
            box-shadow: 0 0 8px currentColor;
            animation: pulse 1.8s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.8); }
        }

        /* Controls */
        .controls {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            border: 1px solid var(--border);
            background-color: var(--surface);
            color: var(--text-primary);
            transition: all 0.2s ease;
        }

        .btn:hover {
            background-color: var(--surface-hover);
            border-color: var(--border-light);
        }

        .btn-start {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border-color: rgba(16, 185, 129, 0.3);
        }
        .btn-start:hover {
            background: rgba(16, 185, 129, 0.25);
        }

        .btn-stop {
            background: rgba(244, 63, 94, 0.15);
            color: #fb7185;
            border-color: rgba(244, 63, 94, 0.3);
        }
        .btn-stop:hover {
            background: rgba(244, 63, 94, 0.25);
        }

        .btn-reset {
            background: rgba(100, 116, 139, 0.15);
            color: #cbd5e1;
        }

        /* Metrics Row */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }

        .metric-card {
            background-color: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 18px 20px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .metric-label {
            font-size: 12px;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .metric-value {
            font-size: 26px;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: var(--text-primary);
        }

        .metric-sub {
            font-size: 13px;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .tag {
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
        }
        .tag-green { background: var(--emerald-bg); color: var(--emerald); }
        .tag-red { background: var(--rose-bg); color: var(--rose); }
        .tag-blue { background: var(--blue-bg); color: var(--blue); }
        .tag-amber { background: var(--amber-bg); color: var(--amber); }

        /* Main Layout (2 Columns) */
        .dashboard-layout {
            display: grid;
            grid-template-columns: 1.1fr 0.9fr;
            gap: 20px;
        }

        @media (max-width: 900px) {
            .dashboard-layout {
                grid-template-columns: 1fr;
            }
        }

        .panel {
            background-color: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .panel-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .panel-title {
            font-size: 15px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Positions List */
        .position-list, .history-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .pos-item {
            background-color: #0e1422;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 14px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: border-color 0.2s;
        }
        .pos-item:hover {
            border-color: var(--border-light);
        }

        .pos-token {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .pos-symbol {
            font-weight: 700;
            font-size: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .pos-meta {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: var(--text-secondary);
        }

        .pos-stats {
            text-align: right;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .pos-val {
            font-weight: 700;
            font-size: 15px;
        }

        .pos-pnl {
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            font-size: 12px;
        }

        /* Activity / Live Process Console */
        .console-box {
            background-color: #090d16;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 12px;
            height: 520px;
            overflow-y: auto;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .log-entry {
            padding: 8px 10px;
            border-radius: 6px;
            background-color: rgba(255, 255, 255, 0.02);
            border-left: 3px solid var(--border-light);
            display: flex;
            flex-direction: column;
            gap: 4px;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-4px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .log-header {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .log-time {
            color: var(--text-muted);
            font-size: 10px;
        }

        .log-badge {
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
        }

        .log-badge.SCAN { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
        .log-badge.AI_BUY { background: rgba(16, 185, 129, 0.2); color: #34d399; }
        .log-badge.AI_SKIP { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
        .log-badge.TRADE_BUY { background: rgba(16, 185, 129, 0.3); color: #10b981; }
        .log-badge.TRADE_SELL { background: rgba(244, 63, 94, 0.3); color: #f43f5e; }
        .log-badge.STATUS { background: rgba(148, 163, 184, 0.2); color: #94a3b8; }

        .log-msg {
            color: #cbd5e1;
            font-size: 11px;
            line-height: 1.4;
        }

        .log-details {
            font-size: 10.5px;
            color: #94a3b8;
            background: rgba(0, 0, 0, 0.2);
            padding: 4px 6px;
            border-radius: 4px;
            margin-top: 2px;
        }

        .empty-state {
            text-align: center;
            padding: 24px 0;
            color: var(--text-muted);
            font-size: 13px;
        }

        .text-green { color: var(--emerald); }
        .text-red { color: var(--rose); }

        /* Toast */
        #toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #1e293b;
            color: white;
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 500;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3);
            border: 1px solid #334155;
            display: none;
            z-index: 1000;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header>
            <div class="header-brand">
                <div class="logo-badge">⚡</div>
                <div>
                    <div class="brand-title">Hermes Solana Sniper</div>
                    <div class="brand-subtitle">Automated AI Hit & Run Trading Engine</div>
                </div>
            </div>

            <div style="display: flex; align-items: center; gap: 16px;">
                <div id="bot-status-pill" class="status-pill running">
                    <span class="pulse-dot"></span>
                    <span id="bot-status-text">BOT RUNNING</span>
                </div>

                <div class="controls">
                    <button class="btn btn-start" onclick="controlBot('start')">▶ Mulai Bot</button>
                    <button class="btn btn-stop" onclick="controlBot('stop')">⏹ Hentikan</button>
                    <button class="btn btn-reset" onclick="resetPortfolio()">🔄 Reset Portofolio</button>
                </div>
            </div>
        </header>

        <!-- Metric Cards -->
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Portofolio</div>
                <div class="metric-value" id="total-asset">$100.00</div>
                <div class="metric-sub" id="asset-split">Kas: $100.00 &bull; Koin: $0.00</div>
            </div>

            <div class="metric-card">
                <div class="metric-label">Uang Siap Pakai</div>
                <div class="metric-value" id="cash-available">$100.00</div>
                <div class="metric-sub">
                    <span class="tag tag-green" id="slots-badge">Bisa beli 10x lagi</span>
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-label">Nilai di Koin</div>
                <div class="metric-value" id="coin-val">$0.00</div>
                <div class="metric-sub" id="pos-count-sub">0 berjalan &bull; 0 selesai</div>
            </div>

            <div class="metric-card">
                <div class="metric-label">Total Profit / Win Rate</div>
                <div class="metric-value" id="total-pnl">+$0.00</div>
                <div class="metric-sub" id="pnl-pct-sub">Win Rate: 0%</div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="dashboard-layout">
            <!-- Left Column: Positions & History -->
            <div style="display: flex; flex-direction: column; gap: 20px;">
                <!-- Active Positions -->
                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">
                            <span>🟢 Posisi Berjalan</span>
                            <span class="tag tag-blue" id="active-count-tag">0</span>
                        </div>
                    </div>
                    <div id="active-positions" class="position-list">
                        <div class="empty-state">Loading...</div>
                    </div>
                </div>

                <!-- History -->
                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">
                            <span>📜 Riwayat Selesai</span>
                            <span class="tag tag-amber" id="history-count-tag">0</span>
                        </div>
                    </div>
                    <div id="history-positions" class="history-list">
                        <div class="empty-state">Loading...</div>
                    </div>
                </div>
            </div>

            <!-- Right Column: Live Process / Activity Logs -->
            <div>
                <div class="panel">
                    <div class="panel-header">
                        <div class="panel-title">
                            <span>⚡ Live Process & AI Feed</span>
                        </div>
                        <span style="font-size: 11px; color: var(--text-muted);">Auto-refresh 3s</span>
                    </div>

                    <div id="console-logs" class="console-box">
                        <div class="empty-state">Menunggu aktivitas bot...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div id="toast">Aksi berhasil dijalankan</div>

    <script>
        function showToast(msg) {
            const toast = document.getElementById('toast');
            toast.textContent = msg;
            toast.style.display = 'block';
            setTimeout(() => { toast.style.display = 'none'; }, 3000);
        }

        function formatUSD(val) {
            return "$" + (val || 0).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        }

        function formatPrice(val) {
            if (!val) return "$0.00";
            if (val < 0.0001) return "$" + val.toLocaleString('en-US', {minimumFractionDigits: 7, maximumFractionDigits: 7});
            if (val < 0.01) return "$" + val.toLocaleString('en-US', {minimumFractionDigits: 5, maximumFractionDigits: 5});
            return "$" + val.toLocaleString('en-US', {minimumFractionDigits: 4, maximumFractionDigits: 4});
        }

        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();

                // Bot Status Pill
                const pill = document.getElementById('bot-status-pill');
                const text = document.getElementById('bot-status-text');
                if (data.bot_active) {
                    pill.className = 'status-pill running';
                    text.textContent = 'BOT RUNNING';
                } else {
                    pill.className = 'status-pill stopped';
                    text.textContent = 'BOT STOPPED';
                }

                // Metrics
                const totalAsset = data.cash + data.coin_value;
                document.getElementById('total-asset').textContent = formatUSD(totalAsset);
                document.getElementById('asset-split').textContent = `Kas: ${formatUSD(data.cash)} • Koin: ${formatUSD(data.coin_value)}`;
                
                document.getElementById('cash-available').textContent = formatUSD(data.cash);
                const slots = Math.floor(data.cash / data.config.position_size);
                const slotsBadge = document.getElementById('slots-badge');
                slotsBadge.textContent = `Bisa beli ${slots}x lagi`;
                slotsBadge.className = slots > 0 ? 'tag tag-green' : 'tag tag-red';

                document.getElementById('coin-val').textContent = formatUSD(data.coin_value);
                document.getElementById('pos-count-sub').textContent = `${data.positions.length} berjalan • ${data.history.length} selesai`;

                // PnL & Win Rate
                const initBalance = data.config.initial_balance || 100.0;
                const netProfit = totalAsset - initBalance;
                const pnlElem = document.getElementById('total-pnl');
                pnlElem.textContent = (netProfit >= 0 ? "+" : "") + formatUSD(netProfit);
                pnlElem.className = "metric-value " + (netProfit >= 0 ? "text-green" : "text-red");

                let winCount = data.history.filter(h => h.profit_usd > 0).length;
                let winRate = data.history.length > 0 ? Math.round((winCount / data.history.length) * 100) : 0;
                document.getElementById('pnl-pct-sub').textContent = `Win Rate: ${winRate}% (${winCount}/${data.history.length} win)`;

                // Active Positions
                document.getElementById('active-count-tag').textContent = data.positions.length;
                const posContainer = document.getElementById('active-positions');
                if (data.positions.length === 0) {
                    posContainer.innerHTML = '<div class="empty-state">Tidak ada posisi berjalan</div>';
                } else {
                    let html = '';
                    data.positions.forEach(p => {
                        const pnlPct = ((p.current_price - p.buy_price) / p.buy_price) * 100;
                        const pnlClass = pnlPct >= 0 ? 'text-green' : 'text-red';
                        html += `
                            <div class="pos-item" onclick="window.location.href='/coin/${p.address}'" style="cursor: pointer;">
                                <div class="pos-token">
                                    <div class="pos-symbol">${p.symbol} <span class="tag tag-blue">${p.name.substring(0, 14)}</span></div>
                                    <div class="pos-meta">Entry: ${formatPrice(p.buy_price)} &bull; Target TP: ${formatPrice(p.target_tp_price)} &bull; Target SL: ${formatPrice(p.target_sl_price)}</div>
                                </div>
                                <div class="pos-stats">
                                    <div class="pos-val">${formatUSD(p.current_val)}</div>
                                    <div class="pos-pnl ${pnlClass}">${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(2)}% (${formatPrice(p.current_price)})</div>
                                </div>
                            </div>
                            
                            <!-- Visual Progress Bar towards TP/SL -->
                            <div style="margin-top: 10px; width: 100%; height: 6px; background: var(--surface-hover); border-radius: 4px; overflow: hidden; position: relative;">
                                <div style="position: absolute; left: 0; height: 100%; width: 50%; background: ${pnlPct >= 0 ? 'var(--emerald)' : 'var(--rose)'}; 
                                    transform: translateX(${pnlPct >= 0 ? '0' : '100%'}) scaleX(${Math.min(Math.abs(pnlPct) / 10, 1)}); 
                                    transform-origin: ${pnlPct >= 0 ? 'left' : 'right'}; transition: all 0.3s ease;">
                                </div>
                                <!-- Center marker (Entry) -->
                                <div style="position: absolute; left: 50%; height: 100%; width: 2px; background: var(--text-primary);"></div>
                            </div>
                        `;
                    });
                    posContainer.innerHTML = html;
                }

                // History
                document.getElementById('history-count-tag').textContent = `${data.history.length} Selesai`;
                const histContainer = document.getElementById('history-positions');
                if (data.history.length === 0) {
                    histContainer.innerHTML = '<div class="empty-state">Belum ada riwayat trading</div>';
                } else {
                    let html = '';
                    const last10 = data.history.slice().reverse().slice(0, 8);
                    last10.forEach(h => {
                        const isWin = h.profit_usd >= 0;
                        const colorClass = isWin ? 'text-green' : 'text-red';
                        const badge = h.reason === 'TAKE_PROFIT' 
                            ? '<span class="tag tag-green">TP</span>' 
                            : '<span class="tag tag-red">SL</span>';
                        html += `
                            <div class="pos-item" onclick="window.location.href='/coin/${h.address}'" style="cursor: pointer;">
                                <div class="pos-token">
                                    <div class="pos-symbol">${h.symbol} ${badge}</div>
                                    <div class="pos-meta">Beli: ${formatPrice(h.buy_price)} &bull; Jual: ${formatPrice(h.sell_price)}</div>
                                </div>
                                <div class="pos-stats" style="text-align: right;">
                                    <div class="pos-val ${colorClass}">${isWin ? '+' : ''}${formatUSD(h.profit_usd)}</div>
                                    <div class="pos-pnl ${colorClass}">${h.pnl_pct >= 0 ? '+' : ''}${h.pnl_pct.toFixed(2)}%</div>
                                    <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Hold: ${( (h.closed_at - (h.opened_at||h.closed_at)) / 60 ).toFixed(1)} mins</div>
                                </div>
                            </div>
                        `;
                    });
                    histContainer.innerHTML = html;
                }

                // Live Console Logs
                const logBox = document.getElementById('console-logs');
                if (data.logs && data.logs.length > 0) {
                    let logHtml = '';
                    data.logs.forEach(l => {
                        let badgeClass = l.type || 'SCAN';
                        let detailHtml = '';
                        if (l.details && Object.keys(l.details).length > 0) {
                            if (l.details.reason) {
                                detailHtml = `<div class="log-details"><strong>Alasan AI:</strong> ${l.details.reason}</div>`;
                            }
                        }
                        logHtml += `
                            <div class="log-entry">
                                <div class="log-header">
                                    <span class="log-time">${l.timestamp}</span>
                                    <span class="log-badge ${badgeClass}">${l.type}</span>
                                </div>
                                <div class="log-msg">${l.message}</div>
                                ${detailHtml}
                            </div>
                        `;
                    });
                    logBox.innerHTML = logHtml;
                }

            } catch (err) {
                console.error("Fetch error:", err);
            }
        }

        async function controlBot(action) {
            try {
                const res = await fetch(`/api/control/${action}`, { method: 'POST' });
                const result = await res.json();
                showToast(result.message || 'Perintah dijalankan');
                fetchStatus();
            } catch (err) {
                showToast('Gagal menjalankan perintah');
            }
        }

        async function resetPortfolio() {
            if (confirm('Yakin ingin mereset portofolio kembali ke modal awal $100? Seluruh history dan log akan dihapus.')) {
                try {
                    const res = await fetch('/api/control/reset', { method: 'POST' });
                    const result = await res.json();
                    showToast(result.message || 'Portofolio direset');
                    fetchStatus();
                } catch (err) {
                    showToast('Gagal mereset portofolio');
                }
            }
        }

        setInterval(fetchStatus, 3000);
        fetchStatus();
    </script>
</body>
</html>
"""


COIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Detail Koin - Hermes Trading Sniper</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0b0f19; --surface: #121826; --surface-hover: #182235;
            --border: #1e293b; --text-primary: #f8fafc; --text-secondary: #94a3b8;
            --emerald: #10b981; --rose: #f43f5e; --blue: #3b82f6;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: var(--bg); color: var(--text-primary); padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
        .btn-back { background: var(--surface); border: 1px solid var(--border); color: var(--text-primary); padding: 8px 16px; border-radius: 8px; text-decoration: none; font-weight: 600; }
        .btn-back:hover { background: var(--surface-hover); }
        .grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
        .card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
        .chart-container { width: 100%; height: 550px; border-radius: 8px; overflow: hidden; }
        .stat-group { margin-bottom: 15px; }
        .stat-label { font-size: 12px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
        .stat-val { font-size: 18px; font-weight: 600; font-family: 'JetBrains Mono', monospace; }
        .text-green { color: var(--emerald); } .text-red { color: var(--rose); }
        .btn-danger { background: rgba(244, 63, 94, 0.1); color: var(--rose); border: 1px solid rgba(244,63,94,0.3); padding: 12px; width: 100%; border-radius: 8px; font-weight: 600; cursor: pointer; margin-top: 10px; }
        .btn-danger:hover { background: rgba(244, 63, 94, 0.2); }
        .gauge-bar { width: 100%; height: 8px; background: #334155; border-radius: 4px; margin-top: 25px; position: relative; }
        .gauge-marker { position: absolute; top: -16px; font-size: 11px; font-weight: bold; transform: translateX(-50%); white-space: nowrap; }
        .gauge-marker.entry { color: #f8fafc; } .gauge-marker.tp { color: var(--emerald); right: 0; transform: translateX(50%); } .gauge-marker.sl { color: var(--rose); left: 0; transform: translateX(-50%); }
        .gauge-current { position: absolute; top: -6px; width: 12px; height: 20px; background: var(--blue); border-radius: 4px; transform: translateX(-50%); box-shadow: 0 0 10px var(--blue); transition: left 0.5s; }
        .gauge-label-bottom { position: absolute; top: 16px; font-size: 10px; font-family: 'JetBrains Mono', monospace; color: var(--text-secondary); transform: translateX(-50%); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <a href="/" class="btn-back">← Kembali</a>
            <h2>Detail <span id="coin-symbol">Memuat...</span></h2>
        </div>
        <div class="grid">
            <div class="card" style="padding: 0;">
                <div id="chart-wrapper" class="chart-container">
                    <div style="padding: 20px; color: var(--text-secondary);">Memuat chart DexScreener...</div>
                </div>
            </div>
            <div class="card" id="details-panel">
                <div style="color: var(--text-secondary);">Memuat data token...</div>
            </div>
        </div>
    </div>

    <script>
        const address = window.location.pathname.split('/').pop();
        
        async function fetchDetails() {
            try {
                const res = await fetch(`/api/coin/${address}`);
                const data = await res.json();
                
                document.getElementById('coin-symbol').textContent = data.symbol || address.substring(0,6);
                
                // Embed chart once
                const chartWrapper = document.getElementById('chart-wrapper');
                if (chartWrapper.innerHTML.includes('Memuat') && data.pair_address) {
                    chartWrapper.innerHTML = `<iframe src="https://dexscreener.com/solana/${data.pair_address}?embed=1&theme=dark&trades=0&info=0" width="100%" height="100%" frameborder="0"></iframe>`;
                }

                let html = '';
                
                if (data.status === 'ACTIVE') {
                    const pnlPct = ((data.current_price - data.buy_price) / data.buy_price) * 100;
                    const pnlClass = pnlPct >= 0 ? 'text-green' : 'text-red';
                    
                    // Gauge Math
                    let range = data.target_tp_price - data.target_sl_price;
                    let currentPos = data.current_price - data.target_sl_price;
                    let pctLeft = (currentPos / range) * 100;
                    pctLeft = Math.max(0, Math.min(100, pctLeft));
                    let entryPos = ((data.buy_price - data.target_sl_price) / range) * 100;

                    html += `
                        <div style="margin-bottom: 20px;">
                            <span style="background: rgba(59, 130, 246, 0.2); color: var(--blue); padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: bold;">POSISI AKTIF</span>
                        </div>
                        
                        <div class="stat-group">
                            <div class="stat-label">Harga Saat Ini (Live)</div>
                            <div class="stat-val ${pnlClass}">$${data.current_price.toFixed(8)} (${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(2)}%)</div>
                        </div>
                        
                        <div style="display: flex; gap: 20px; margin-bottom: 25px;">
                            <div class="stat-group">
                                <div class="stat-label">Entry Price</div>
                                <div class="stat-val" style="font-size:14px;">$${data.buy_price.toFixed(8)}</div>
                            </div>
                            <div class="stat-group">
                                <div class="stat-label">Value Saat Ini</div>
                                <div class="stat-val ${pnlClass}" style="font-size:14px;">$${data.current_val.toFixed(2)}</div>
                            </div>
                        </div>

                        <div class="gauge-bar" style="margin-bottom: 40px;">
                            <div class="gauge-marker sl" style="left: 0;">SL (-6%)</div>
                            <div class="gauge-label-bottom" style="left: 0;">$${data.target_sl_price.toFixed(8)}</div>
                            
                            <div class="gauge-marker tp" style="left: 100%;">TP (+8%)</div>
                            <div class="gauge-label-bottom" style="left: 100%;">$${data.target_tp_price.toFixed(8)}</div>
                            
                            <div class="gauge-marker entry" style="left: ${entryPos}%;">Entry</div>
                            
                            <div class="gauge-current" style="left: ${pctLeft}%;"></div>
                        </div>

                        <hr style="border: 0; border-top: 1px solid var(--border); margin: 20px 0;">
                        
                        <div style="display: flex; gap: 20px;">
                            <div class="stat-group">
                                <div class="stat-label">24h Volume</div>
                                <div class="stat-val" style="font-size:14px;">$${data.volume_24h ? data.volume_24h.toLocaleString(undefined, {maximumFractionDigits:0}) : '0'}</div>
                            </div>
                            <div class="stat-group">
                                <div class="stat-label">Liquidity</div>
                                <div class="stat-val" style="font-size:14px;">$${data.liquidity_usd ? data.liquidity_usd.toLocaleString(undefined, {maximumFractionDigits:0}) : '0'}</div>
                            </div>
                        </div>

                        <button class="btn-danger" onclick="sellNow()">Jual Sekarang (Manual Close)</button>
                    `;
                } else if (data.status === 'CLOSED') {
                    const isWin = data.profit_usd >= 0;
                    const pnlClass = isWin ? 'text-green' : 'text-red';
                    html += `
                        <div style="margin-bottom: 20px;">
                            <span style="background: rgba(100, 116, 139, 0.2); color: var(--text-secondary); padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: bold;">RIWAYAT (${data.reason})</span>
                        </div>
                        <div class="stat-group">
                            <div class="stat-label">Entry Price</div>
                            <div class="stat-val" style="font-size:14px;">$${data.buy_price.toFixed(8)}</div>
                        </div>
                        <div class="stat-group">
                            <div class="stat-label">Exit Price</div>
                            <div class="stat-val" style="font-size:14px;">$${data.sell_price.toFixed(8)}</div>
                        </div>
                        <div class="stat-group">
                            <div class="stat-label">Profit/Loss</div>
                            <div class="stat-val ${pnlClass}">${isWin ? '+' : ''}$${data.profit_usd.toFixed(2)} (${isWin ? '+' : ''}${data.pnl_pct.toFixed(2)}%)</div>
                        </div>
                    `;
                } else {
                    html += `
                        <div class="stat-group">
                            <div class="stat-label">Harga Saat Ini</div>
                            <div class="stat-val">$${(data.current_price || 0).toFixed(8)}</div>
                        </div>
                        <div class="stat-group">
                            <div class="stat-label">Status</div>
                            <div class="stat-val" style="font-size:14px;">Tidak ada posisi aktif/riwayat.</div>
                        </div>
                    `;
                }

                if (data.dex_url) {
                    html += `<div style="margin-top: 20px; text-align: center;"><a href="${data.dex_url}" target="_blank" style="color: var(--blue); font-size: 14px; text-decoration: none;">Buka di DexScreener ↗</a></div>`;
                }
                
                document.getElementById('details-panel').innerHTML = html;
                
            } catch (err) {
                console.error("Fetch error:", err);
            }
        }

        async function sellNow() {
            if(confirm('Yakin ingin menutup posisi secara manual pada harga pasar saat ini?')) {
                try {
                    const res = await fetch(`/api/control/sell/${address}`, { method: 'POST' });
                    const result = await res.json();
                    alert(result.message || 'Berhasil');
                    fetchDetails();
                } catch (e) {
                    alert('Gagal mengeksekusi');
                }
            }
        }

        setInterval(fetchDetails, 3000);
        fetchDetails();
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/status")
def api_status():
    try:
        check = subprocess.run(["systemctl", "is-active", "trading-bot"], capture_output=True, text=True)
        bot_active = (check.stdout.strip() == "active")
    except:
        bot_active = False

    try:
        cash = get_wallet()
        positions = get_positions()
        history = get_trades(500)
        logs = get_recent_activities(40)
    except Exception as e:
        cash = Config.INITIAL_BALANCE
        positions = []
        history = []
        logs = []
            
    coin_val = sum([p.get("current_val", 0) for p in positions])
    
    return jsonify({
        "bot_active": bot_active,
        "cash": cash,
        "coin_value": coin_val,
        "positions": positions,
        "history": history,
        "logs": logs,
        "config": {
            "initial_balance": Config.INITIAL_BALANCE,
            "position_size": Config.POSITION_SIZE
        }
    })

@app.route("/api/control/<action>", methods=["POST"])
def api_control(action):
    if action == "start":
        subprocess.run(["systemctl", "start", "trading-bot"])
        log_event("STATUS", "Bot diaktifkan melalui Dashboard.")
        return jsonify({"success": True, "message": "Bot berhasil dimulai!"})
    elif action == "stop":
        subprocess.run(["systemctl", "stop", "trading-bot"])
        log_event("STATUS", "Bot dihentikan melalui Dashboard.")
        return jsonify({"success": True, "message": "Bot berhasil dihentikan!"})
    elif action == "reset":
        subprocess.run(["systemctl", "stop", "trading-bot"])
        # Reset SQLite DB and fallback files
        reset_db(Config.INITIAL_BALANCE)
        with open(Config.DATA_FILE, "w") as f:
            json.dump({"cash": Config.INITIAL_BALANCE, "positions": []}, f, indent=2)
        with open(Config.HISTORY_FILE, "w") as f:
            json.dump([], f, indent=2)
        from bot_logger import LOG_FILE
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w") as f:
                json.dump([], f, indent=2)
            
        log_event("STATUS", f"Portofolio direset ke modal awal ${Config.INITIAL_BALANCE:.2f}.")
        subprocess.run(["systemctl", "start", "trading-bot"])
        return jsonify({"success": True, "message": "Portofolio direset & bot direstart!"})
    else:
        return jsonify({"error": "Unknown action"}), 400


@app.route("/coin/<address>")
def coin_detail(address):
    return render_template_string(COIN_TEMPLATE)

from scanner import get_token_details
@app.route("/api/coin/<address>")
def api_coin(address):
    # Cari di posisi
    try:
        positions = get_positions()
        history = get_trades(500)
    except:
        positions = []
        history = []
        
    pos = next((p for p in positions if p["address"] == address), None)
    hist = next((h for h in reversed(history) if h["address"] == address), None)
    
    # Ambil detail market live dari DexScreener
    live_data = get_token_details(address)
    
    result = {
        "address": address,
        "symbol": "Unknown",
        "current_price": 0,
    }
    
    if live_data:
        result.update({
            "pair_address": live_data.get("pair_address"),
            "current_price": live_data.get("price_usd", 0),
            "symbol": live_data.get("symbol", "UNKNOWN"),
            "dex_url": live_data.get("dex_url"),
            "volume_24h": live_data.get("volume_24h"),
            "liquidity_usd": live_data.get("liquidity_usd"),
        })
        
    if pos:
        result.update(pos)
        if live_data: result["current_val"] = pos["tokens_count"] * live_data["price_usd"]
        result["status"] = "ACTIVE"
    elif hist:
        result.update(hist)
        result["status"] = "CLOSED"
        # Jika gak dapat live_data, fallback pair buat chart dari hist gak ada, tapi kita bisa pakai address token
        if not live_data: result["pair_address"] = address
    else:
        result["status"] = "NOT_OWNED"
        if not live_data: result["pair_address"] = address
        
    return jsonify(result)

@app.route("/api/control/sell/<address>", methods=["POST"])
def api_control_sell(address):
    # Trigger script / code untuk manual sell
    # Karena portfolio jalan di process terpisah, kita manipulasi target_sl_price jadi current_price
    # supaya bot mendeteksi SL dan menjualnya di iterasi berikutnya (max 15 detik).
    try:
        positions = get_positions()
        found = False
        for p in positions:
            if p["address"] == address:
                p["target_sl_price"] = 9999999999  # Paksa hit SL
                p["target_tp_price"] = 0
                found = True
        if found:
            save_positions(positions)
            # Sync to JSON
            with open(Config.DATA_FILE, "w") as f:
                json.dump({"cash": get_wallet(), "positions": positions}, f, indent=2)
            return jsonify({"success": True, "message": "Perintah jual dikirim! Bot akan menutup posisi dalam 15 detik."})
        return jsonify({"error": "Posisi tidak ditemukan"}), 404
    except Exception as e:
        return jsonify({"error": f"Gagal update posisi: {e}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
