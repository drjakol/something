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
from kill_zones import get_kill_zone
from range_tracker import update_asia_range, get_asia_range
from break_retest import detect_break_retest
from stats_engine import calculate_stats
from session_stats import session_winrate

import ccxt
deribit = ccxt.deribit({"enableRateLimit": True})

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

COINS = ["BTC/USDT", "SOL/USDT", "AVAX/USDT", "DOT/USDT", "LTC/USDT"]
SIGNAL_LOG_FILE = "signals_log.jsonl"
SCORE_THRESHOLD = 15
COOLDOWN_SECONDS = 300

bot = Bot(token=BOT_TOKEN)
last_signal_time = defaultdict(lambda: 0)

def normalize_symbol(symbol):
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
    with open(SIGNAL_LOG_FILE, "a") as f:
        f.write(json.dumps(data) + "\n")

async def get_deribit_price(symbol="BTC/USDT"):
    try:
        ticker = await asyncio.to_thread(deribit.fetch_ticker, symbol)
        return ticker["last"]
    except Exception as e:
        print("Deribit price error:", e)
        return None

async def get_deribit_oi(symbol="BTC/USDT"):
    try:
        oi = await asyncio.to_thread(deribit.fetch_open_interest, symbol)
        return oi.get("open_interest", 0)
    except Exception as e:
        print("Deribit OI error:", e)
        return 0

async def telegram_bot():
    print("🚀 Institutional Bot with Deribit Started")

    while True:
        for symbol in COINS:
            try:
                session = active_session()
                kill_zone = get_kill_zone()
                if not session or not kill_zone:
                    continue

                okx_price = await asyncio.to_thread(get_price, symbol)
                okx_trades = await asyncio.to_thread(get_trades, symbol)
                okx_orderbook = await asyncio.to_thread(get_orderbook, symbol)

                if session == "Asia":
                    update_asia_range(symbol, okx_price)
                asia_levels = get_asia_range(symbol)

                liquidity = build_liquidity_map(okx_orderbook)
                orderflow = calculate_orderflow(okx_trades)
                direction = "LONG" if orderflow["delta"] > 0 else "SHORT"

                br_confirmed = detect_break_retest(
                    okx_price,
                    asia_levels if session != "Asia" else None,
                    direction
                )

                # --- Deribit Integration ---
                deri_price = await get_deribit_price(symbol)
                deri_oi = await get_deribit_oi(symbol)
                price = (okx_price + deri_price)/2 if deri_price else okx_price

                # --- Smart Score Calculation ---
                score = 0
                score += 25 if kill_zone else -10
                score += 20 if br_confirmed else -10
                score += 30 if abs(orderflow["delta"]) > 50 else -15
                score += 15 if liquidity else -10
                score += 10 * (deri_oi/1_000_000)  # OI weight

                now = time.time()
                if score >= SCORE_THRESHOLD and now - last_signal_time[symbol] > COOLDOWN_SECONDS:
                    levels = build_signal_levels(price, direction)
                    stats = calculate_stats()
                    session_stats = session_winrate()

                    msg = f"""
🔥 {normalize_symbol(symbol)} PRO SIGNAL

🌍 Session: {session}
⏱ Kill Zone: {kill_zone}
📊 Score: {score:.2f}

🟢 Direction: {direction}
💰 Entry: {levels['entry']}
🛑 SL: {levels['sl']}
🎯 TP1: {levels['tp1']} | TP2: {levels['tp2']}

📉 Break & Retest: {"Confirmed" if br_confirmed else "No"}

📈 Order Flow:
Delta: {orderflow['delta']}
CVD: {orderflow['cvd']}

🌐 Session Winrate:
Asia: {session_stats.get("Asia", "--")}% | London: {session_stats.get("London", "--")}% | New York: {session_stats.get("New York", "--")}% 
"""
                    await bot.send_message(chat_id=CHANNEL_ID, text=msg)
                    last_signal_time[symbol] = now

                    log_signal({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "symbol": normalize_symbol(symbol),
                        "session": session,
                        "kill_zone": kill_zone,
                        "direction": direction,
                        "score": score
                    })

                await asyncio.sleep(6)

            except Exception as e:
                print(f"❌ Error {symbol}: {e}")
                await asyncio.sleep(6)

        await asyncio.sleep(60)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(telegram_bot())
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    return {"status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
