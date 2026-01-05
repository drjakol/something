def filter_false_breakout(price, liquidity, prev_price, threshold=50):
    """
    پارامترها:
    - price: قیمت فعلی
    - liquidity: خروجی build_liquidity_map {"support": ..., "resistance": ...}
    - prev_price: آخرین قیمت قبل
    - threshold: حداقل اختلاف لازم برای تایید Breakout

    خروجی:
    - True اگر Breakout واقعی باشد
    - False اگر Breakout جعلی باشد
    """
    # بررسی شکست مقاومت
    if prev_price <= liquidity['resistance'] and price > liquidity['resistance'] + threshold:
        return True
    # بررسی شکست حمایت
    if prev_price >= liquidity['support'] and price < liquidity['support'] - threshold:
        return True

    # اگر هیچکدام نبود، شکست جعلی است
    return False
