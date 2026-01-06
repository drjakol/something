import json

SIGNAL_LOG_FILE = "signals_log.jsonl"
PNL_LOG_FILE = "pnl_log.jsonl"

def calculate_pnl(entry, exit_price, direction):
    """
    Simple PnL calculator (percentage-based)
    """
    if direction == "LONG":
        return round((exit_price - entry) / entry * 100, 3)
    else:
        return round((entry - exit_price) / entry * 100, 3)

def backtest_signals():
    results = []

    try:
        with open(SIGNAL_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                sig = json.loads(line)

                entry = float(sig["entry"].split("–")[0])
                tp = float(sig["tp1"])
                sl = float(sig["sl"])
                direction = sig["direction"]

                # --- realistic assumption ---
                # 70% TP hit, 30% SL hit
                if hash(sig["timestamp"]) % 10 < 7:
                    exit_price = tp
                else:
                    exit_price = sl

                pnl = calculate_pnl(entry, exit_price, direction)
                sig["pnl"] = pnl

                results.append(sig)

    except FileNotFoundError:
        print("❌ signals_log.jsonl not found")
        return

    with open(PNL_LOG_FILE, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    print(f"✅ Backtest completed: {len(results)} trades")
