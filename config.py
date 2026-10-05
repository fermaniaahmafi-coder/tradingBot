import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    INITIAL_BALANCE = float(os.getenv("INITIAL_BALANCE", "100.0"))
    POSITION_SIZE = float(os.getenv("POSITION_SIZE", "10.0"))
    MAX_POSITIONS = int(os.getenv("MAX_POSITIONS", "10"))
    
    AI_BASE_URL = os.getenv("AI_BASE_URL", "http://localhost:20128/v1")
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_MODEL = os.getenv("AI_MODEL", "deepseek-chat")
    
    NETWORK = os.getenv("NETWORK", "solana")
    MIN_LIQUIDITY = float(os.getenv("MIN_LIQUIDITY", "5000"))
    MIN_VOLUME_24H = float(os.getenv("MIN_VOLUME_24H", "10000"))
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "hermes123")
    JWT_SECRET = os.getenv("JWT_SECRET", "hermes_solana_jwt_secret_key_987654321")
    JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "72"))

    @staticmethod
    def get_db_path(bot_id="bot1"):
        return f"/home/trading/trading_{bot_id}.db" if os.path.exists("/home/trading") else os.path.join(Config.BASE_DIR, f"trading_{bot_id}.db")

    @staticmethod
    def get_data_file(bot_id="bot1"):
        return f"/home/trading/portfolio_{bot_id}.json" if os.path.exists("/home/trading") else os.path.join(Config.BASE_DIR, f"portfolio_{bot_id}.json")

    @staticmethod
    def get_history_file(bot_id="bot1"):
        return f"/home/trading/trade_history_{bot_id}.json" if os.path.exists("/home/trading") else os.path.join(Config.BASE_DIR, f"trade_history_{bot_id}.json")
