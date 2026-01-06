def build_trade(price, direction, sl_distance, rr=3, risk_pct=0.5):
    if direction == "LONG":
        sl = price - sl_distance
        tp = price + sl_distance * rr
    else:
        sl = price + sl_distance
        tp = price - sl_distance * rr

    return {
        "entry": price,
        "sl": round(sl, 2),
        "tp1": round(tp, 2),
        "risk_pct": risk_pct,
        "rr": rr
    }
