import os
from dotenv import load_dotenv

load_dotenv()

# Binance
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "")
TESTNET = os.getenv("TESTNET", "true").lower() == "true"

# Claude
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Trading
TRADING_PAIRS = os.getenv("TRADING_PAIRS", "BTCUSDT,ETHUSDT").split(",")
AUTO_SCAN = os.getenv("AUTO_SCAN", "true").lower() == "true"
AUTO_SCAN_COUNT = int(os.getenv("AUTO_SCAN_COUNT", "20"))
AUTO_SCAN_MODE = os.getenv("AUTO_SCAN_MODE", "volume")  # "volume" or "volatile"
PRIMARY_TIMEFRAME = os.getenv("PRIMARY_TIMEFRAME", "15m")
TREND_TIMEFRAME = os.getenv("TREND_TIMEFRAME", "1h")
CAPITAL_USDT = float(os.getenv("CAPITAL_USDT", "1000"))
RISK_PER_TRADE_PERCENT = float(os.getenv("RISK_PER_TRADE_PERCENT", "1.5"))
DAILY_LOSS_LIMIT_USDT = float(os.getenv("DAILY_LOSS_LIMIT_USDT", "30"))
MAX_OPEN_TRADES = int(os.getenv("MAX_OPEN_TRADES", "2"))
AI_CONFIDENCE_THRESHOLD = int(os.getenv("AI_CONFIDENCE_THRESHOLD", "75"))

# Binance API URLs
BINANCE_BASE_URL = "https://testnet.binance.vision" if TESTNET else "https://api.binance.com"
# Always use live Binance WebSocket for market data (testnet doesn't support public streams)
BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"
