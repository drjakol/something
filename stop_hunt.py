def detect_stop_hunt(price, liquidity, delta):
    """
    تشخیص Stop Hunt ساده
    - price: آخرین قیمت
    - liquidity: خروجی build_liquidity_map
    - delta: delta کل معاملات
    """

    if not liquidity or "bids" not in liquidity or "asks" not in liquidity:
        return None

    # نمونه قوانین ساده
    if delta > 1000 and price < liquidity["support"] * 1.002:
        return {"type": "Long Stop Hunt", "reason": "Large sell orders below support", "strength": delta / 100}
    elif delta < -1000 and price > liquidity["resistance"] * 0.998:
        return {"type": "Short Stop Hunt", "reason": "Large buy orders above resistance", "strength": abs(delta) / 100}
    else:
        return None
