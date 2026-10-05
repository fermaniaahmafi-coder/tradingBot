import time
from db_manager import add_activity, get_recent_activities

LOG_FILE = "/home/trading/activities.json"

def log_event(event_type, message, details=None):
    """
    event_type: 'SCAN', 'AI_BUY', 'AI_SKIP', 'TRADE_BUY', 'TRADE_SELL', 'STATUS', 'ERROR'
    """
    try:
        add_activity(event_type, message, details)
    except Exception:
        # Fallback to local activities.json
        try:
            import json, os
            logs = []
            if os.path.exists("activities.json"):
                with open("activities.json", "r") as f:
                    logs = json.load(f)
            logs.insert(0, {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "event_type": event_type,
                "message": message,
                "details": details or {}
            })
            with open("activities.json", "w") as f:
                json.dump(logs[:60], f, indent=2)
        except Exception:
            pass

def get_recent_logs(limit=50):
    try:
        return get_recent_activities(limit)
    except Exception:
        return []
