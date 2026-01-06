def adaptive_weight(winrate):
    if winrate is None:
        return 1.0
    if winrate > 60:
        return 1.2
    if winrate < 40:
        return 0.8
    return 1.0
