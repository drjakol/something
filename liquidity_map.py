def build_liquidity_map(orderbook, top_n=5):
    bids = sorted(orderbook["bids"], key=lambda x: x[1], reverse=True)
    asks = sorted(orderbook["asks"], key=lambda x: x[1], reverse=True)

    bid_liquidity = bids[:top_n]
    ask_liquidity = asks[:top_n]

    bid_prices = [level[0] for level in bid_liquidity]
    ask_prices = [level[0] for level in ask_liquidity]

    support_zone = min(bid_prices)
    resistance_zone = max(ask_prices)

    return {
        "bid_liquidity": bid_liquidity,
        "ask_liquidity": ask_liquidity,
        "support": support_zone,
        "resistance": resistance_zone
    }
