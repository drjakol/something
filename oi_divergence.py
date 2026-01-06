def oi_divergence(price_change, oi_change):
    """
    Price ↑ + OI ↓  → Short covering (Bullish)
    Price ↓ + OI ↓  → Long covering (Bearish)
    """
    if oi_change is None:
        return 0

    if price_change > 0 and oi_change < 0:
        return +10
    if price_change < 0 and oi_change < 0:
        return -10
    return 0
