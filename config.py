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
    
    DATA_FILE = "/home/trading/portfolio.json"
    HISTORY_FILE = "/home/trading/trade_history.json"
