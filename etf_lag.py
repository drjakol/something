from collections import deque

_etf_history = deque(maxlen=3)

def etf_lag_bias(net_flow):
    """
    ETF اثرش با تأخیر 1–2 روزه میاد
    """
    if net_flow is None:
        return 0

    _etf_history.append(net_flow)

    if len(_etf_history) < 2:
        return 0

    avg = sum(_etf_history) / len(_etf_history)

    if avg > 0:
        return +15
    elif avg < 0:
        return -15
    return 0
