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
from consolidation import check_consolidation
from orderflow import calculate_orderflow
from session_filter import active_session
from kill_zones import get_kill_zone
from range_tracker import update_asia_range, get_asia_range
from break_retest import detect_break_retest
from session_stats import session_winrate
from stats_engine import calculate_stats
from score_engine import smart_score_v2

import ccxt

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

COINS = ["BTC/USDT", "SOL/USDT", "AVAX/USDT", "DOT/USDT", "LTC/USDT"]
SIGNAL_LOG_FILE = "signals_log.jsonl"
COOLDOWN_SECONDS = 300       # فاصله سیگنال‌ها (5 دقیقه)
SCORE_THRESHOLD = 10         # حداقل Smart Score برای ارسال سیگنال

DERIBIT_SYMBOL = "BTC-PERPETUAL"

# ---------------- INIT ----------------
bot = Bot(token=BOT_TOKEN)
last_signal_time = defaultdict(lambda: 0)
deribit = ccxt.deribit({"enableRateLimit": True})

# ---------------- HELPERS ----------------
def normalize_symbol(symbol):
    return symbol.replace("/", "")

def build_signal_levels(price, direction):
    precision = 2 if price > 100 else 4
    if direction == "LONG":
        return {
            "entry": f"{round(price * 0.995, precision)}–{round(price * 1.001, precision)}",
            "sl": round(price * 0.99, precision),
            "tp1": round(price * 1.015, precision),
            "tp2": round(price * 1.03, precision),
        }
    else:
        return {
            "entry": f"{round(price * 0.999, precision)}–{round(price * 1.005, precision)}",
            "sl": round(price * 1.01, precision),
            "tp1": round(price * 0.985, precision),
            "tp2": round(price * 0.97, precision),
        }

def log_signal(data):
    with open(SIGNAL_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")

# ---------------- DERIBIT ----------------
async def get_deribit_price():
    try:
        ticker = await asyncio.to_thread(
            deribit.fetch_ticker, DERIBIT_SYMBOL
        )
        return ticker["last"]
    except Exception as e:
        print("Deribit price error:", e)
        return None

async def get_deribit_oi():
    try:
        data = await asyncio.to_thread(
            deribit.public_get_get_book_summary_by_currency,
            {"currency": "BTC", "kind": "future"}
        )
        return float(data["result"][0]["open_interest"])
    except Exception as e:
        print("Deribit OI error:", e)
        return 0

# ---------------- MAIN BOT LOOP ----------------
async def telegram_bot():
    print("🚀 Institutional Killer Bot v2 – Real Money Ready Started")

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

                stop_hunt = detect_stop_hunt(
                    okx_price,
                    liquidity,
                    orderflow["delta"]
                )

                consolidation = check_consolidation(okx_orderbook)

                deri_price = await get_deribit_price()
                deri_oi = await get_deribit_oi()
                price = (okx_price + deri_price) / 2 if deri_price else okx_price

                # ---------------- Smart Score Real Money ----------------
                base_score = 0
                base_score += 25 if kill_zone else 0
                base_score += 20 if br_confirmed else 0
                base_score += 30 if abs(orderflow["delta"]) > 50 else 0
                base_score += 10 if liquidity else 0
                base_score += 15 if stop_hunt else 0
                base_score += 20 if not consolidation else 0
                base_score += int(deri_oi / 1_000_000 * 10)

                session_win = session_winrate()
                score = smart_score_v2(base_score=base_score, winrate=session_win.get(session, 50))

                now = time.time()
                if score < SCORE_THRESHOLD:
                    continue
                if now - last_signal_time[symbol] < COOLDOWN_SECONDS:
                    continue

                levels = build_signal_levels(price, direction)

                # ---------------- Telegram Message ----------------
                msg = f"""
🔥 {normalize_symbol(symbol)} INSTITUTIONAL SIGNAL

🌍 Session: {session}
⏱ Kill Zone: {kill_zone}
📊 Smart Score: {score}

🟢 Direction: {direction}
💰 Entry: {levels['entry']}
🛑 SL: {levels['sl']}
🎯 TP1: {levels['tp1']} | TP2: {levels['tp2']}

📉 Break & Retest: {"✅" if br_confirmed else "❌"}
🧲 Stop Hunt: {"✅" if stop_hunt else "❌"}
📦 Consolidation: {"❌ NO TRADE" if consolidation else "OK"}

📈 Orderflow:
Delta: {orderflow['delta']}
CVD: {orderflow['cvd']}

📊 Session Winrate:
Asia: {session_win.get("Asia", "--")}% | London: {session_win.get("London", "--")}% | New York: {session_win.get("New York", "--")}%
"""

                await bot.send_message(chat_id=CHANNEL_ID, text=msg)
                log_signal({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "symbol": normalize_symbol(symbol),
                    "session": session,
                    "direction": direction,
                    "entry": levels["entry"],
                    "sl": levels["sl"],
                    "tp1": levels["tp1"],
                    "tp2": levels["tp2"],
                    "score": score
                })

                last_signal_time[symbol] = now
                await asyncio.sleep(2)

            except Exception as e:
                print(f"❌ Error {symbol}:", e)
                await asyncio.sleep(2)

        await asyncio.sleep(5)

# ---------------- FASTAPI ----------------
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(telegram_bot())
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    return {"status": "Institutional Bot Running – Real Money Ready"}

# ---------------- RUN FASTAPI ----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000))
    )
