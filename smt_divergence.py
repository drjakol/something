def detect_smt(btc_candles, eth_candles):
    """
    Simple SMT:
    BTC HH but ETH no HH -> bearish
    BTC LL but ETH no LL -> bullish
    """
    btc_highs = [c[2] for c in btc_candles[-5:]]
    eth_highs = [c[2] for c in eth_candles[-5:]]
    btc_lows = [c[3] for c in btc_candles[-5:]]
    eth_lows = [c[3] for c in eth_candles[-5:]]

    if max(btc_highs) > btc_highs[-2] and max(eth_highs) <= eth_highs[-2]:
        return "BEARISH"

    if min(btc_lows) < btc_lows[-2] and min(eth_lows) >= eth_lows[-2]:
        return "BULLISH"

    return None
