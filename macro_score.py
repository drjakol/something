from options_max_pain import max_pain_bias
from oi_divergence import oi_divergence
from etf_lag import etf_lag_bias

def macro_score(
    price_change,
    oi_data,
    ls_ratio,
    liq,
    options,
    etf,
    price
):
    score = 0

    # OI change
    oi_change = oi_data.get("change") if oi_data else None
    score += 10 if oi_change and oi_change > 0 else 0

    # OI Divergence
    score += oi_divergence(price_change, oi_change)

    # Long / Short crowd
    if ls_ratio:
        if ls_ratio.get("longRatio", 0) > 0.6:
            score -= 5
        elif ls_ratio.get("shortRatio", 0) > 0.6:
            score += 5

    # Liquidation spike
    if liq and liq.get("total", 0) > 50_000_000:
        score += 10

    # Options Max Pain
    score += max_pain_bias(options, price)

    # ETF lag
    if etf:
        score += etf_lag_bias(etf.get("netFlow"))

    return score
