from adaptive_weights import adaptive_weight

def smart_score_v2(base_score, winrate):
    """
    Normalized Smart Score (0 – 100)
    """
    weight = adaptive_weight(winrate)
    score = base_score * weight

    # hard clamp to avoid score explosion
    if score < 0:
        score = 0
    if score > 100:
        score = 100

    return round(score, 2)
