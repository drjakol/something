from datetime import datetime, timezone

def get_kill_zone():
    """
    Kill Zones (UTC)
    نسخه اصلاح‌شده برای اطمینان از همیشه مقداردهی:
    - Asia Range: 00:00 – 06:59
    - London Open: 07:00 – 09:59
    - New York Open: 13:00 – 17:59
    - Extended: سایر ساعات برای تست / ارسال پیام
    """
    hour = datetime.now(timezone.utc).hour

    if 0 <= hour <= 6:
        return "Asia Range"
    elif 7 <= hour <= 9:
        return "London Open"
    elif 13 <= hour <= 17:
        return "New York Open"
    else:
        # مقدار پیش‌فرض برای ساعات غیرجلسه‌ای
        return "Extended Session"
