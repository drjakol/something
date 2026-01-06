from datetime import datetime, timezone

def active_session():
    hour = datetime.now(timezone.utc).hour

    if 7 <= hour <= 11:
        return "London"
    elif 13 <= hour <= 17:
        return "New York"
    else:
        return None
