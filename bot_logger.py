import time
from db_manager import add_activity, get_recent_activities

LOG_FILE = "/home/trading/activities.json"

def log_event(event_type, message, details=None):
    """
    event_type: 'SCAN', 'AI_BUY', 'AI_SKIP', 'TRADE_BUY', 'TRADE_SELL', 'STATUS', 'ERROR'
    """
    try:
        add_activity(event_type, message, details)
    except Exception as e:
        print(f"[LOGGER ERROR] {e}")

def get_recent_logs(limit=50):
    try:
        return get_recent_activities(limit)
    except Exception:
        return []
