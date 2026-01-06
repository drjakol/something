import requests

BASE_URL = "https://open-api.coinglass.com/public/v2"

def get_open_interest(symbol="BTC"):
    try:
        r = requests.get(f"{BASE_URL}/open_interest", params={"symbol": symbol}, timeout=5)
        data = r.json()
        return data.get("data", {})
    except:
        return None

def get_long_short_ratio(symbol="BTC"):
    try:
        r = requests.get(f"{BASE_URL}/long_short_ratio", params={"symbol": symbol}, timeout=5)
        return r.json().get("data", {})
    except:
        return None

def get_liquidations(symbol="BTC"):
    try:
        r = requests.get(f"{BASE_URL}/liquidation", params={"symbol": symbol}, timeout=5)
        return r.json().get("data", {})
    except:
        return None

def get_etf_flow():
    try:
        r = requests.get(f"{BASE_URL}/etf")
        return r.json().get("data", {})
    except:
        return None
