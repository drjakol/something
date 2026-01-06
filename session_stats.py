import json
from collections import defaultdict

PNL_LOG_FILE = "pnl_log.jsonl"

def session_winrate():
    stats = defaultdict(lambda: {"wins": 0, "total": 0})

    try:
        with open(PNL_LOG_FILE, "r") as f:
            for line in f:
                t = json.loads(line)
                session = t.get("session")
                pnl = t.get("pnl", 0)

                if not session:
                    continue

                stats[session]["total"] += 1
                if pnl > 0:
                    stats[session]["wins"] += 1
    except FileNotFoundError:
        return {}

    result = {}
    for s, d in stats.items():
        if d["total"] > 0:
            result[s] = round(d["wins"] / d["total"] * 100, 2)

    return result
