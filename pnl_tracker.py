import json
from main import SIGNAL_LOG_FILE  # مسیر فایل سیگنال‌ها
PNL_LOG_FILE = "pnl_log.jsonl"

def calculate_pnl(entry, exit_price, direction):
    try:
        entry = float(entry)
        exit_price = float(exit_price)
    except Exception:
        return 0

    if direction == "LONG":
        return round(exit_price - entry, 2)
    else:
        return round(entry - exit_price, 2)

def backtest_signals():
    results = []

    try:
        with open(SIGNAL_LOG_FILE, "r") as f:
            for line in f:
                sig = json.loads(line)

                entry = float(sig["entry"].split("–")[0])
                tp = float(sig["tp1"])
                sl = float(sig["sl"])
                direction = sig["direction"]

                exit_price = tp  # فرض رسیدن TP1
                pnl = calculate_pnl(entry, exit_price, direction)

                sig["pnl"] = pnl
                results.append(sig)

        with open(PNL_LOG_FILE, "w") as f:
            for r in results:
                f.write(json.dumps(r) + "\n")

        print("✅ Backtest Completed:", len(results))
    except FileNotFoundError:
        print("❌ SIGNAL_LOG_FILE not found")
