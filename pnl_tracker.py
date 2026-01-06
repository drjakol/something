def backtest_signals():
    results = []

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
