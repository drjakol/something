def calculate_delta(trades):
    """
    محاسبه delta ساده از trades
    - trades: لیست معاملات [{price, size, side}]
    """
    delta = 0
    for t in trades:
        size = float(t.get("size", 0))
        side = t.get("side", "buy")
        delta += size if side == "buy" else -size

    return {"delta": delta}
