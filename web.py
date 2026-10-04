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
                            <div class="pos-item">
                                <div class="pos-token">
                                    <div class="pos-symbol">${p.symbol} <span class="tag tag-blue">${p.name.substring(0, 14)}</span></div>
                                    <div class="pos-meta">Entry: ${formatPrice(p.buy_price)} &bull; Target TP: ${formatPrice(p.target_tp_price)} &bull; Target SL: ${formatPrice(p.target_sl_price)}</div>
                                </div>
                                <div class="pos-stats">
                                    <div class="pos-val">${formatUSD(p.current_val)}</div>
                                    <div class="pos-pnl ${pnlClass}">${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(2)}% (${formatPrice(p.current_price)})</div>
                                </div>
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
                            <div class="pos-item">
                                <div class="pos-token">
                                    <div class="pos-symbol">${h.symbol} ${badge}</div>
                                    <div class="pos-meta">Beli: ${formatPrice(h.buy_price)} &bull; Jual: ${formatPrice(h.sell_price)}</div>
                                </div>
                                <div class="pos-stats">
                                    <div class="pos-val ${colorClass}">${isWin ? '+' : ''}${formatUSD(h.profit_usd)}</div>
                                    <div class="pos-pnl ${colorClass}">${h.pnl_pct >= 0 ? '+' : ''}${h.pnl_pct.toFixed(2)}%</div>
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

    cash = Config.INITIAL_BALANCE
    positions = []
    history = []
    
    if os.path.exists(Config.DATA_FILE):
        try:
            with open(Config.DATA_FILE, "r") as f:
                data = json.load(f)
                cash = data.get("cash", Config.INITIAL_BALANCE)
                positions = data.get("positions", [])
        except:
            pass
            
    if os.path.exists(Config.HISTORY_FILE):
        try:
            with open(Config.HISTORY_FILE, "r") as f:
                history = json.load(f)
        except:
            pass
            
    coin_val = sum([p.get("current_val", 0) for p in positions])
    logs = get_recent_logs(40)
    
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
        # Reset state files
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
