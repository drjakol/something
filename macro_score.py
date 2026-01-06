def macro_score(oi, long_short, liquidations, etf):
    score = 0

    if oi and oi.get("change", 0) > 0:
        score += 10

    if long_short:
        if long_short.get("longRatio", 0) > 0.55:
            score -= 5
        elif long_short.get("shortRatio", 0) > 0.55:
            score += 5

    if liquidations and liquidations.get("total", 0) > 50_000_000:
        score += 10

    if etf:
        if etf.get("netFlow", 0) > 0:
            score += 20
        elif etf.get("netFlow", 0) < 0:
            score -= 20

    return score
