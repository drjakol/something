def detect_break_retest(price, levels, direction, tolerance=0.001):
    """
    Break & Retest logic
    """
    if not levels:
        return False

    level = levels["high"] if direction == "LONG" else levels["low"]
    if not level:
        return False

    if direction == "LONG":
        return price > level and abs(price - level) / level < tolerance
    else:
        return price < level and abs(price - level) / level < tolerance
