def detect_stop_hunt(price, liquidity, delta, buffer=0.001):
    support = liquidity["support"]
    resistance = liquidity["resistance"]

    if price < support * (1 - buffer) and delta > 0:
        return {
            "type": "LONG",
            "reason": "Stop Hunt Below Support"
        }

    if price > resistance * (1 + buffer) and delta < 0:
        return {
            "type": "SHORT",
            "reason": "Stop Hunt Above Resistance"
        }

    return None
