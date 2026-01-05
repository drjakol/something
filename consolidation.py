def check_consolidation(orderbook, range_percent=0.5):
    """
    پارامترها:
    - orderbook: dict با bids و asks
    - range_percent: درصد محدوده برای تعیین Consolidation

    خروجی:
    - True اگر قیمت در محدوده Consolidation باشد
    - False اگر روند واضحی داشته باشد
    """
    bids = [price for price, size in orderbook.get("bids", [])]
    asks = [price for price, size in orderbook.get("asks", [])]

    if not bids or not asks:
        return False

    high = max(asks)
    low = min(bids)

    if (high - low) / low * 100 <= range_percent:
        return True

    return False
