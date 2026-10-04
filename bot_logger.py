import os
import json
import time

LOG_FILE = "/home/trading/activities.json"
MAX_LOGS = 100

def log_event(event_type, message, details=None):
    """
    event_type: 'SCAN', 'AI_DECISION', 'TRADE_BUY', 'TRADE_SELL', 'STATUS', 'ERROR'
    """
    entry = {
        "timestamp": time.strftime("%H:%M:%S"),
        "time_raw": time.time(),
        "type": event_type,
        "message": message,
        "details": details or {}
    }
    
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                logs = json.load(f)
        except Exception:
            logs = []
            
    logs.insert(0, entry)
    logs = logs[:MAX_LOGS]
    
    try:
        with open(LOG_FILE, "w") as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        print(f"[LOGGER ERROR] {e}")

def get_recent_logs(limit=50):
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)[:limit]
    except Exception:
        return []
