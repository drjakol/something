import asyncio
import os
import json
import time
from datetime import datetime, timezone
from collections import defaultdict

from fastapi import FastAPI
from telegram import Bot

from data_okx import get_price, get_trades, get_orderbook
from liquidity_map import build_liquidity_map
from stop_hunt import detect_stop_hunt
from false_breakout import filter_false_breakout
from consolidation import check_consolidation
from orderflow import calculate_orderflow
from session_filter import active_session
from stats_engine import calculate_stats

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

COINS = [
    "BTC/USDT", "SOL/USDT", "AVAX/USDT",
    "DOT/USDT", "LTC/USDT", "DOGE/USDT"
]

SCORE_THRESHOLD = 60
COOLDOWN_SECONDS = 300
SIGNAL_LOG_FILE = "signals_log.jsonl"

bot = Bot(token=BOT_TOKEN)

# ---------------- UTILS ----------------
def normalize_symbol(symbol: str) -> str:
    return symbol.replace("/", "")

def build_signal_levels(price, direction):
    precision = 4 if price < 100 else 2

    if direction == "LONG":
        return {
            "entry": f"{round(price*0.995, precision)}–{round(price*1.001, precision)}",
            "sl": round(price*0.99, precision),
            "tp1": round(price*1.015, precision),
            "tp2": round(price*1.03, precision)
        }
    else:
        return {
            "entry": f"{round(price*0.999, precision)}–{round(price*1.005, precision)}",
            "sl": round(price*1.01, precision),
            "tp1": round(price*0.985, precision),
            "tp2": round(price*0.97, precision)
        }

def log_signal(data):
    with open(SIGNAL_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")

# ---------------- SCORING ----------------
def calculate_score(
    stop_hunt,
    false_breakout_passed,
    in_consolidation,
    orderflow,
    liquidity,
    session
):
    score = 0

    # Session weight
    if session == "Asia":
        score += 15
    elif session in ("London", "New York"):
        score += 25
    else:
        score -= 30

    score += 20 if abs(orderflow["delta"]) > 50 else -10
    score += 15 if abs(orderflow["cvd"]) > 50 else 0
    score += 15 if not in_consolidation else -20
    score += 10 if false_breakout_passed else -15
    score += -10 if stop_hunt else 10
    score += 10 if liquidity else -10

    return score

# ---------------- MAIN LOOP ----------------
last_signal_time = defaultdict(lambda: 0)

async def telegram_bot():
    print("🚀 Bot started with Asia / London / NY Sessions")
    prev_prices = {symbol: None for symbol in COINS}

    while True:
        for symbol in COINS:
            try:
                session = active_session()
                if not session:
                    continue

                price = await asyncio.to_thread(get_price, symbol)
                trades = await asyncio.to_thread(get_trades, symbol)
                orderbook = await asyncio.to_thread(get_orderbook, symbol)

                liquidity = build_liquidity_map(orderbook)
                if not liquidity:
                    continue

                orderflow = calculate_orderflow(trades)

                prev_price = prev_prices.get(symbol)
                false_breakout_passed = (
                    filter_false_breakout(price, liquidity, orderflow["delta"])
                    if prev_price else True
                )

                in_consolidation = check_consolidation(orderbook)
                stop_hunt = detect_stop_hunt(
                    price, liquidity, orderflow["delta"]
                )

                score = calculate_score(
                    stop_hunt,
                    false_breakout_passed,
                    in_consolidation,
                    orderflow,
                    liquidity,
                    session
                )

                now = time.time()
                if score >= SCORE_THRESHOLD:
                    if now - last_signal_time[symbol] < COOLDOWN_SECONDS:
                        continue

                    direction = "LONG" if orderflow["delta"] > 0 else "SHORT"
                    levels = build_signal_levels(price, direction)
                    stats = calculate_stats()

                    msg = f"""
🔥 {normalize_symbol(symbol)} SMART SIGNAL

🌍 Session: {session}
📊 Score: {score}

🟢 Direction: {direction}
💰 Entry: {levels['entry']}
🛑 SL: {levels['sl']}
🎯 TP1: {levels['tp1']} | TP2: {levels['tp2']}

💧 Liquidity Zones:
Support: {liquidity['support']}
Resistance: {liquidity['resistance']}

📈 Order Flow:
Delta: {orderflow['delta']}
CVD: {orderflow['cvd']}

📊 Performance:
Winrate: {stats['winrate'] if stats else '--'}%
Expectancy: {stats['expectancy'] if stats else '--'}
"""

                    await bot.send_message(chat_id=CHANNEL_ID, text=msg)
                    last_signal_time[symbol] = now

                    log_signal({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "symbol": normalize_symbol(symbol),
                        "direction": direction,
                        "score": score,
                        "session": session,
                        "entry": levels["entry"],
                        "sl": levels["sl"],
                        "tp1": levels["tp1"],
                        "tp2": levels["tp2"],
                        "delta": orderflow["delta"],
                        "cvd": orderflow["cvd"]
                    })

                prev_prices[symbol] = price
                await asyncio.sleep(6)

            except Exception as e:
                print(f"❌ Error {symbol}: {e}")
                await asyncio.sleep(6)

        await asyncio.sleep(60)

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
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000))
    )
