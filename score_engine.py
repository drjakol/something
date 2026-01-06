from adaptive_weights import adaptive_weight

def smart_score_v2(base_score, winrate):
    """
    محاسبه Smart Score با وزن Adaptive و محدودیت 0-100
    """
    weight = adaptive_weight(winrate)
    raw_score = base_score * weight
    return round(max(0, min(100, raw_score)), 2)
