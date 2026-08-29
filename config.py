import os

# 預設觀察股票與產業對照清單
DEFAULT_TICKER = "AAPL"
DEFAULT_PEERS = ["MSFT", "GOOGL", "AMZN", "META"]

# FRED API Key（若有註冊可填入，若無則留空使用系統預設數值）
FRED_API_KEY = os.getenv("FRED_API_KEY", "")