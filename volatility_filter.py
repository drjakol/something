import numpy as np

def atr(candles, period=14):
    trs = []
    for i in range(1, len(candles)):
        high = candles[i][2]
        low = candles[i][3]
        prev_close = candles[i-1][4]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    return np.mean(trs[-period:])

def volatility_ok(candles, min_ratio=0.002):
    a = atr(candles)
    price = candles[-1][4]
    return (a / price) >= min_ratio
