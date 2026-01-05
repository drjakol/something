def build_liquidity_map(orderbook):
    """
    ساخت نقشه نقدینگی (Liquidity Map) از Orderbook
    - orderbook: دیکشنری با keys "bids" و "asks"
    - هر bid/ask ممکن است یک لیست دو یا سه تایی باشد: [price, size] یا [price, size, extra]
    """

    bid_liquidity = orderbook.get("bids", [])
    ask_liquidity = orderbook.get("asks", [])

    # فیلتر و استخراج فقط دو مقدار price و size
    clean_bids = []
    for item in bid_liquidity:
        if len(item) >= 2:
            price, size = item[0], item[1]
            clean_bids.append((float(price), float(size)))

    clean_asks = []
    for item in ask_liquidity:
        if len(item) >= 2:
            price, size = item[0], item[1]
            clean_asks.append((float(price), float(size)))

    # محاسبه حمایت و مقاومت بر اساس بیشترین نقدینگی
    support_zone = min([price for price, size in clean_bids], default=None)
    resistance_zone = max([price for price, size in clean_asks], default=None)

    # می‌توانید نقدینگی کل در هر محدوده را هم اضافه کنید
    total_bid_liq = sum([size for price, size in clean_bids])
    total_ask_liq = sum([size for price, size in clean_asks])

    return {
        "support": support_zone,
        "resistance": resistance_zone,
        "total_bid_liquidity": total_bid_liq,
        "total_ask_liquidity": total_ask_liq,
        "bids": clean_bids,
        "asks": clean_asks
    }
