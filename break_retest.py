from collections import defaultdict

_last_break = defaultdict(dict)

def detect_break_retest(price, levels, direction, tolerance=0.002):
    if not levels or not levels.get("high") or not levels.get("low"):
        return False

    key = "high" if direction == "LONG" else "low"
    level = levels[key]

    state = _last_break.get(key, {})

    # Break
    if not state.get("broken"):
        if direction == "LONG" and price > level * (1 + tolerance):
            _last_break[key] = {"broken": True}
        elif direction == "SHORT" and price < level * (1 - tolerance):
            _last_break[key] = {"broken": True}
        return False

    # Retest
    if state.get("broken"):
        if abs(price - level) / level <= tolerance:
            _last_break[key] = {}
            return True

    return False
