import json
from break_retest import detect_break_retest
from main import SIGNAL_LOG_FILE

PNL_LOG_FILE = "pnl_log.jsonl"

def calculate_pnl(entry, exit_price, direction):
    """
    PnL بر اساس جهت معامله
    """
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

                # Entry & TP1
                entry = float(sig["entry"].split("–")[0])
                tp = float(sig["tp1"])
                sl = float(sig["sl"])
                direction = sig["direction"]

                # فرض رسیدن TP1
                pnl = calculate_pnl(entry, tp, direction)
                sig["pnl"] = pnl

                results.append(sig)

        # ذخیره PnL
        with open(PNL_LOG_FILE, "w", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r) + "\n")

        print(f"✅ Backtest Completed: {len(results)} trades")

    except FileNotFoundError:
        print("❌ SIGNAL_LOG_FILE not found")
