def calculate_delta(trades):
    buy_volume = 0
    sell_volume = 0

    for trade in trades:
        amount = trade.get("amount", 0)

        if trade.get("side") == "buy":
            buy_volume += amount
        else:
            sell_volume += amount

    delta = buy_volume - sell_volume

    return {
        "buy_volume": buy_volume,
        "sell_volume": sell_volume,
        "delta": delta
    }
