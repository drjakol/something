import json
from datetime import datetime

SIGNAL_LOG_FILE = "signals_log.jsonl"
PNL_LOG_FILE = "pnl_log.jsonl"

def calculate_pnl(entry_price, exit_price, direction, size=1):
    """
    محاسبه سود/ضرر ساده
    direction: "LONG" یا "SHORT"
    size: تعداد واحد فرضی
    """
    if direction == "LONG":
        pnl = (exit_price - entry_price) * size
    else:
        pnl = (entry_price - exit_price) * size
    return pnl

def backtest_signals():
    """
    تحلیل PnL از فایل لاگ سیگنال‌ها
    """
    results = []
    try:
        with open(SIGNAL_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                sig = json.loads(line)
                # ساده‌ترین حالت: TP1 یا TP2 رسید
                tp_price = sig.get("tp1")  # فقط TP1 در این تحلیل
                sl_price = sig.get("sl")
                entry = int(sig.get("entry").split("–")[0])
                direction = sig.get("direction", "LONG")

                # فرض کنیم اگر Delta مثبت TP1 رسید، PnL مثبت
                # (در عمل باید دیتا واقعی ترید داشته باشیم)
                if direction == "LONG":
                    exit_price = tp_price if tp_price > entry else sl_price
                else:
                    exit_price = tp_price if tp_price < entry else sl_price

                pnl = calculate_pnl(entry, exit_price, direction)
                sig["pnl"] = pnl
                sig["timestamp"] = datetime.utcnow().isoformat()
                results.append(sig)

        with open(PNL_LOG_FILE, "w", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r) + "\n")
        print(f"✅ PnL Backtest complete, {len(results)} signals processed")

    except FileNotFoundError:
        print("⚠️ No signal log file found for backtest")
