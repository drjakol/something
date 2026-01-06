from collections import deque

_losses = deque(maxlen=3)

def update_pnl(pnl):
    _losses.append(pnl)

def trading_allowed():
    if len(_losses) < 3:
        return True
    return not all(p <= 0 for p in _losses)
