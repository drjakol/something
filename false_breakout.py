def filter_false_breakout(price, liquidity, delta):
    if not liquidity:
        return False

    if price > liquidity["resistance"] and delta < 0:
        return False

    if price < liquidity["support"] and delta > 0:
        return False

    return True
