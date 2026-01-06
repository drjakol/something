from adaptive_weights import adaptive_weight

def smart_score_v2(base_score, winrate):
    weight = adaptive_weight(winrate)
    raw_score = base_score * weight
    # محدود کردن Score به 0-100
    return round(max(0, min(100, raw_score)), 2)
