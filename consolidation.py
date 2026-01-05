def check_consolidation(orderbook, threshold=0.5):
    """
    تشخیص Consolidation
    - اگر قیمت بین حمایت و مقاومت خیلی کم تغییر کند، در حالت Consolidation است
    """
    bids = orderbook.get("bids", [])
    asks = orderbook.get("asks", [])

    if not bids or not asks:
        return False

    highest_bid = max([float(b[0]) for b in bids if len(b) >= 2])
    lowest_ask = min([float(a[0]) for a in asks if len(a) >= 2])

    if (lowest_ask - highest_bid) / highest_bid * 100 < threshold:
        return True

    return False
