from datetime import datetime, timezone

def get_kill_zone():
    """
    Kill Zones (UTC)
    """
    hour = datetime.now(timezone.utc).hour

    if 0 <= hour <= 6:
        return "Asia Range"
    elif 7 <= hour <= 9:
        return "London Open"
    elif 13 <= hour <= 15:
        return "New York Open"
    else:
        return None
