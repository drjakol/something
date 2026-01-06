def max_pain_bias(options_data, price):
    """
    ساده‌شده:
    اگر قیمت زیر Max Pain → Bullish bias
    اگر بالای Max Pain → Bearish bias
    """
    if not options_data or "maxPain" not in options_data:
        return 0

    max_pain = options_data["maxPain"]

    if price < max_pain:
        return +10
    elif price > max_pain:
        return -10
    return 0
