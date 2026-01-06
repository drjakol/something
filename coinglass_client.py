import requests

BASE_URL = "https://open-api.coinglass.com/public/v2"

def get_open_interest(symbol="BTC"):
    """Open Interest عمومی برای نماد"""
    try:
        r = requests.get(f"{BASE_URL}/open_interest", params={"symbol": symbol}, timeout=5)
        data = r.json()
        return data.get("data", {})
    except Exception as e:
        print(f"Error get_open_interest: {e}")
        return None

def get_long_short_ratio(symbol="BTC"):
    """نسبت Long / Short"""
    try:
        r = requests.get(f"{BASE_URL}/long_short_ratio", params={"symbol": symbol}, timeout=5)
        return r.json().get("data", {})
    except Exception as e:
        print(f"Error get_long_short_ratio: {e}")
        return None

def get_liquidations(symbol="BTC"):
    """Liquidations"""
    try:
        r = requests.get(f"{BASE_URL}/liquidation", params={"symbol": symbol}, timeout=5)
        return r.json().get("data", {})
    except Exception as e:
        print(f"Error get_liquidations: {e}")
        return None

def get_options_oi(symbol="BTC"):
    """Open Interest معاملات آپشن"""
    try:
        r = requests.get(f"{BASE_URL}/options/oi", params={"symbol": symbol}, timeout=5)
        return r.json().get("data", {})
    except Exception as e:
        print(f"Error get_options_oi: {e}")
        return None

def get_etf_flow(symbol="BTC"):
    """جریان ETF"""
    try:
        r = requests.get(f"{BASE_URL}/etf", params={"symbol": symbol}, timeout=5)
        return r.json().get("data", {})
    except Exception as e:
        print(f"Error get_etf_flow: {e}")
        return None
