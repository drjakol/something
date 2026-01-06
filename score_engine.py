def clamp(val, min_v, max_v):
    return max(min_v, min(val, max_v))

def smart_score(
    kill_zone,
    br,
    orderflow,
    liquidity,
    stop_hunt,
    consolidation,
    oi
):
    score = 0

    score += 20 if kill_zone else -10
    score += 25 if br else -15

    score += clamp(abs(orderflow["delta"]) / 10, 0, 25)

    score += 15 if liquidity else -10
    score += 10 if stop_hunt else 0
    score -= 10 if consolidation else 0

    score += clamp(oi / 1_000_000, 0, 15)

    return round(score, 2)
