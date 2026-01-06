from collections import defaultdict

# state per symbol + direction
_last_break = defaultdict(dict)

def detect_break_retest(price, levels, direction, symbol, tolerance=0.002):
    """
    ICT Break & Retest Logic (Safe Version)
    - Break: قیمت واضح از high/low عبور کند
    - Retest: قیمت دوباره به همان level برگردد
    """

    if not levels or levels.get("high") is None or levels.get("low") is None:
        return False

    key = f"{symbol}_{direction}"
    level = levels["high"] if direction == "LONG" else levels["low"]

    state = _last_break.get(key, {})

    # --- Break ---
    if not state.get("broken"):
        if direction == "LONG" and price > level * (1 + tolerance):
            _last_break[key] = {"broken": True, "level": level}
        elif direction == "SHORT" and price < level * (1 - tolerance):
            _last_break[key] = {"broken": True, "level": level}
        return False

    # --- Retest ---
    if abs(price - state["level"]) / state["level"] <= tolerance:
        _last_break.pop(key, None)  # reset safely
        return True

    return False
