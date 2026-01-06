import ccxt

exchange = ccxt.okx({"enableRateLimit": True})

def get_htf_bias(symbol, timeframe="4h", limit=50):
    candles = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    highs = [c[2] for c in candles]
    lows = [c[3] for c in candles]
    close = candles[-1][4]

    high = max(highs)
    low = min(lows)
    mid = (high + low) / 2

    if close > mid:
        return "BULLISH"
    elif close < mid:
        return "BEARISH"
    return "NEUTRAL"
