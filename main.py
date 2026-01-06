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
from score_engine import smart_score_v2

import ccxt

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

COINS = ["BTC/USDT", "SOL/USDT", "AVAX/USDT", "DOT/USDT", "LTC/USDT"]
SIGNAL_LOG_FILE = "signals_log.jsonl"

COOLDOWN_SECONDS = 600          # ⏱ 10 minutes cooldown
SCORE_THRESHOLD = 0            # 🎯 Minimum Smart Score

DERIBIT_SYMBOL = "BTC-PERPETUAL"

# ================= INIT =================
bot = Bot(token=BOT_TOKEN)
last_signal_time = defaultdict(lambda: 0)
last_direction = defaultdict(lambda: None)

deribit = ccxt.deribit({"enableRateLimit": True})

# ================= HELPERS =================
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

# ================= DERIBIT =================
async def get_deribit_price():
    try:
        ticker = await asyncio.to_thread(deribit.fetch_ticker, DERIBIT_SYMBOL)
        return ticker["last"]
    except:
        return None

async def get_deribit_oi():
    try:
        data = await asyncio.to_thread(
            deribit.public_get_get_book_summary_by_currency,
            {"currency": "BTC", "kind": "future"}
        )
        return float(data["result"][0]["open_interest"])
    except:
        return 0

# ================= MAIN LOOP =================
async def telegram_bot():
    print("🚀 Institutional Killer Bot – Anti‑Spam Build Started")

    while True:
        for symbol in COINS:
            try:
                # -------- Session Filters --------
                session = active_session()
                kill_zone = get_kill_zone()
                if not session or not kill_zone:
                    continue

                # -------- Market Data --------
                price = await asyncio.to_thread(get_price, symbol)
                trades = await asyncio.to_thread(get_trades, symbol)
                orderbook = await asyncio.to_thread(get_orderbook, symbol)

                if session == "Asia":
                    update_asia_range(symbol, price)

                asia_levels = get_asia_range(symbol)

                liquidity = build_liquidity_map(orderbook)
                orderflow = calculate_orderflow(trades)

                direction = "LONG" if orderflow["delta"] > 0 else "SHORT"

                # -------- Anti‑Spam: same direction --------
                if last_direction[symbol] == direction:
                    continue

                br_confirmed = detect_break_retest(
                    price, asia_levels, direction
                )

                stop_hunt = detect_stop_hunt(
                    price, liquidity, orderflow["delta"]
                )

                # -------- Must have real liquidity play --------
                if not br_confirmed and not stop_hunt:
                    continue

                # -------- No trade in consolidation --------
                if check_consolidation(orderbook):
                    continue

                # -------- Deribit Context --------
                deri_price = await get_deribit_price()
                deri_oi = await get_deribit_oi()

                final_price = (price + deri_price) / 2 if deri_price else price

                # -------- Smart Score --------
                base_score = 0
                base_score += 25  # kill zone
                base_score += 25 if br_confirmed else 0
                base_score += 25 if stop_hunt else 0
                base_score += 15 if abs(orderflow["delta"]) > 50 else 0
                base_score += 10 if liquidity else 0

                # 🔒 SAFE OI contribution (0–20)
                oi_score = min(20, int(deri_oi / 1_000_000_000 * 5))
                base_score += oi_score

                winrates = session_winrate()
                score = smart_score_v2(base_score, winrates.get(session, 50))

                # -------- Final Filters --------
                now = time.time()
                if score < SCORE_THRESHOLD:
                    continue
                if now - last_signal_time[symbol] < COOLDOWN_SECONDS:
                    continue

                levels = build_signal_levels(final_price, direction)

                # -------- Telegram Message --------
                msg = (
                    f"🔥 {normalize_symbol(symbol)} INSTITUTIONAL SIGNAL\n\n"
                    f"📊 Score: {score}\n"
                    f"🌍 Session: {session} | {kill_zone}\n\n"
                    f"📈 Direction: {direction}\n"
                    f"🎯 Entry: {levels['entry']}\n"
                    f"🛑 SL: {levels['sl']}\n"
                    f"✅ TP1: {levels['tp1']} | TP2: {levels['tp2']}"
                )

                await bot.send_message(chat_id=CHANNEL_ID, text=msg)

                log_signal({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "symbol": normalize_symbol(symbol),
                    "session": session,
                    "direction": direction,
                    "score": score
                })

                last_signal_time[symbol] = now
                last_direction[symbol] = direction

                await asyncio.sleep(3)

            except Exception as e:
                print(f"❌ {symbol} error:", e)

        await asyncio.sleep(5)

# ================= FASTAPI =================
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(telegram_bot())
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    return {"status": "Institutional Bot Running – Anti‑Spam Active"}

# ================= RUN =================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000))
    )
