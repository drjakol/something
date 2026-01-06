import json

PNL_LOG_FILE = "pnl_log.jsonl"

def calculate_stats():
    wins = losses = total = 0
    profit = loss = 0

    try:
        with open(PNL_LOG_FILE, "r") as f:
            for line in f:
                trade = json.loads(line)
                pnl = trade.get("pnl", 0)

                total += 1
                if pnl > 0:
                    wins += 1
                    profit += pnl
                else:
                    losses += 1
                    loss += abs(pnl)
    except FileNotFoundError:
        return None

    if total == 0:
        return None

    winrate = round(wins / total * 100, 2)
    expectancy = round((profit - loss) / total, 2)

    return {
        "winrate": winrate,
        "expectancy": expectancy,
        "trades": total
    }
