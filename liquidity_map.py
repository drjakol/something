def build_liquidity_map(orderbook):
    bids = [(float(p), float(s)) for p, s, *_ in orderbook.get("bids", []) if s]
    asks = [(float(p), float(s)) for p, s, *_ in orderbook.get("asks", []) if s]

    if not bids or not asks:
        return None

    support = max(bids, key=lambda x: x[1])[0]
    resistance = max(asks, key=lambda x: x[1])[0]

    return {
        "support": support,
        "resistance": resistance,
        "bids": sorted(bids, key=lambda x: x[1], reverse=True)[:5],
        "asks": sorted(asks, key=lambda x: x[1], reverse=True)[:5]
    }
