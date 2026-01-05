import asyncio
import os
import json
from datetime import datetime
from fastapi import FastAPI
from telegram import Bot

from data_okx import get_price, get_trades, get_orderbook
from liquidity_map import build_liquidity_map
from stop_hunt import detect_stop_hunt
from false_breakout import filter_false_breakout
from consolidation import check_consolidation
from orderflow import calculate_delta

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

COINS = [
    "BTC/USDT", "SOL/USDT", "AVAX/USDT",
    "DOT/USDT", "LTC/USDT", "DOGE/USDT"
]

SCORE_THRESHOLD = 30   # حداقل امتیاز ارسال سیگنال
SIGNAL_LOG_FILE = "signals_log.jsonl"

# ---------------- FASTAPI & BOT ----------------
bot = Bot(token=BOT_TOKEN)

# ---------------- UTILS ----------------
def normalize_symbol(symbol: str) -> str:
    return symbol.replace("/", "")

def build_signal_levels(price, direction):
    if direction == "LONG":
        return {
            "entry": f"{int(price*0.995)}–{int(price*1.0)}",
            "sl": int(price*0.99),
            "tp1": int(price*1.015),
            "tp2": int(price*1.03)
        }
    else:
        return {
            "entry": f"{int(price*1.0)}–{int(price*1.005)}",
            "sl": int(price*1.01),
            "tp1": int(price*0.985),
            "tp2": int(price*0.97)
        }

def log_signal(data, filename=SIGNAL_LOG_FILE):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")

def orderbook_volatility(orderbook):
    """Adaptive threshold برای Consolidation"""
    bids = orderbook.get("bids", [])
    asks = orderbook.get("asks", [])
    if not bids or not asks:
        return 0.5
    bid_prices = [float(b[0]) for b in bids[:10]]
    ask_prices = [float(a[0]) for a in asks[:10]]
    mid = (bid_prices[0] + ask_prices[0]) / 2
    spread = (ask_prices[0] - bid_prices[0]) / mid * 100
    return spread

# ---------------- SCORING SYSTEM ----------------
def calculate_score(
    stop_hunt,
    false_breakout_passed,
    in_consolidation,
    delta_data,
    liquidity
):
    score = 0
    # Stop Hunt
    score += 20 if not stop_hunt else -15
    # False Breakout
    score += 20 if false_breakout_passed else -10
    # Consolidation
    score += 15 if not in_consolidation else -20
    # Delta strength
    score += 15 if abs(delta_data["delta"]) > 10 else 0
    # Liquidity clarity
    if liquidity["support"] and liquidity["resistance"]:
        score += 10
    return score

# ---------------- MAIN BOT LOOP ----------------
async def telegram_bot():
    print("🚀 Bot started")
    prev_prices = {symbol: None for symbol in COINS}

    while True:
        for symbol in COINS:
            try:
                # دریافت داده‌ها
                price = await asyncio.to_thread(get_price, symbol)
                orderbook = await asyncio.to_thread(get_orderbook, symbol)
                trades = await asyncio.to_thread(get_trades, symbol)

                # محاسبه
                liquidity = build_liquidity_map(orderbook)
                delta_data = calculate_delta(trades)

                stop_hunt = detect_stop_hunt(
                    price=price,
                    liquidity=liquidity,
                    delta=delta_data["delta"]
                )

                prev_price = prev_prices.get(symbol)
                false_breakout_passed = (
                    filter_false_breakout(price, liquidity, prev_price)
                    if prev_price else True
                )

                adaptive_threshold = min(max(orderbook_volatility(orderbook)*1.5, 0.3), 1.2)
                in_consolidation = check_consolidation(orderbook, threshold=adaptive_threshold)

                score = calculate_score(
                    stop_hunt,
                    false_breakout_passed,
                    in_consolidation,
                    delta_data,
                    liquidity
                )

                if score >= SCORE_THRESHOLD:
                    direction = "LONG" if delta_data["delta"] > 0 else "SHORT"
                    strategy_type = "Conservative" if score < 85 else "Aggressive"
                    levels = build_signal_levels(price, direction)

                    # محدود کردن پیام برای تلگرام
                    bid_clusters = ", ".join([str(int(p)) for p, s in liquidity["bids"][:3]])
                    ask_clusters = ", ".join([str(int(p)) for p, s in liquidity["asks"][:3]])

                    msg = f"""
📍 {normalize_symbol(symbol)} – Signal Report

🟦 Type: {strategy_type}
🟢 Direction: {direction}
📈 Entry Zone: {levels['entry']}
🛑 SL: {levels['sl']}
🎯 TP1: {levels['tp1']} | TP2: {levels['tp2']}

📊 Liquidity Pools:
Bid Clusters: {bid_clusters}
Ask Clusters: {ask_clusters}

📌 Order Flow:
Delta: {delta_data['delta']}

⚡ False Breakout Filter: {"Passed" if false_breakout_passed else "Failed"}
🚫 Stop Hunt: {"Not Detected" if not stop_hunt else "Detected"}
"""

                    await bot.send_message(chat_id=CHANNEL_ID, text=msg)

                    # لاگ سیگنال برای بک‌تست
                    log_signal({
                        "timestamp": datetime.utcnow().isoformat(),
                        "symbol": normalize_symbol(symbol),
                        "direction": direction,
                        "score": score,
                        "entry": levels["entry"],
                        "sl": levels["sl"],
                        "tp1": levels["tp1"],
                        "tp2": levels["tp2"],
                        "delta": delta_data["delta"],
                        "consolidation": in_consolidation,
                        "stop_hunt": bool(stop_hunt),
                        "false_breakout_passed": false_breakout_passed
                    })

                prev_prices[symbol] = price
                await asyncio.sleep(6)

            except Exception as e:
                print(f"Error {symbol}: {e}")
                await asyncio.sleep(6)

        await asyncio.sleep(120)

# ---------------- FASTAPI ----------------
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(telegram_bot())
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    return {"status": "running"}

# ---------------- RUN ----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
