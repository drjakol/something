from datetime import datetime, timezone

def active_session():
    """
    Trading Sessions (UTC)
    Asia:     00:00 – 06:59
    London:   07:00 – 11:59
    New York: 13:00 – 17:59
    """

    hour = datetime.now(timezone.utc).hour

    if 0 <= hour <= 6:
        return "Asia"
    elif 7 <= hour <= 11:
        return "London"
    elif 13 <= hour <= 17:
        return "New York"
    else:
        return None
