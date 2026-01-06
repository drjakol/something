from adaptive_weights import adaptive_weight

def clamp(x, a, b):
    return max(a, min(b, x))

def smart_score_v2(
    base_score,
    winrate
):
    weight = adaptive_weight(winrate)
    return round(base_score * weight, 2)
