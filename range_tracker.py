from collections import defaultdict

asia_range = defaultdict(lambda: {"high": None, "low": None})

def update_asia_range(symbol, price):
    r = asia_range[symbol]

    if r["high"] is None or price > r["high"]:
        r["high"] = price
    if r["low"] is None or price < r["low"]:
        r["low"] = price

def get_asia_range(symbol):
    return asia_range.get(symbol)
