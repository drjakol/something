def build_liquidity_map(orderbook, top_n=5):
    bids = sorted(orderbook["bids"], key=lambda x: x[1], reverse=True)
    asks = sorted(orderbook["asks"], key=lambda x: x[1], reverse=True)

    bid_liquidity = bids[:top_n]
    ask_liquidity = asks[:top_n]

    support_zone = min([price for price, size in bid_liquidity])
    resistance_zone = max([price for price, size in ask_liquidity])

    return {
        "bid_liquidity": bid_liquidity,
        "ask_liquidity": ask_liquidity,
        "support": support_zone,
        "resistance": resistance_zone
    }
