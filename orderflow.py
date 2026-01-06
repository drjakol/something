def calculate_orderflow(trades):
    delta = 0.0
    cvd = 0.0

    for t in trades:
        amount = float(t.get("amount", 0))
        side = t.get("side")

        if side == "buy":
            delta += amount
            cvd += amount
        elif side == "sell":
            delta -= amount
            cvd -= amount

    return {
        "delta": round(delta, 2),
        "cvd": round(cvd, 2)
    }
