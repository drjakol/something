def filter_false_breakout(price, liquidity, prev_price):
    """
    جلوگیری از سیگنال‌های اشتباه Breakout
    """
    if not liquidity:
        return True

    if price > liquidity["resistance"] * 1.01:
        return True
    if price < liquidity["support"] * 0.99:
        return True

    # اگر حرکت خیلی کوچک بود
    if abs(price - prev_price) < 0.5:
        return False

    return True
