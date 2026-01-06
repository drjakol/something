import asyncio, os, time, json
from datetime import datetime, timezone
from collections import defaultdict
from fastapi import FastAPI
from telegram import Bot

from data_okx import get_price, get_trades, get_orderbook
from liquidity_map import build_liquidity_map
from orderflow import calculate_orderflow
from session_filter import active_session
from kill_zones import get_kill_zone
from range_tracker import update_asia_range, get_asia_range
from break_retest import detect_break_retest

from coinglass_client import (
    get_open_interest,
    get_long_short_ratio,
    get_liquidations,
    get_etf_flow
)
from macro_score import macro_score

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

COINS = ["BTC/USDT", "SOL/USDT", "AVAX/USDT"]
SCORE_THRESHOLD = 80
COOLDOWN = 300

bot = Bot(BOT_TOKEN)
last_signal = defaultdict(lambda: 0)
prev_price = {}

def normalize(s): return s.replace("/", "")

async def telegram_bot():
    print("🚀 Institutional Bot Started")

    while True:
        for symbol in COINS:
            try:
                session = active_session()
                kill_zone = get_kill_zone()
                if not session or not kill_zone:
                    continue

                price = await asyncio.to_thread(get_price, symbol)
                trades = await asyncio.to_thread(get_trades, symbol)
                orderbook = await asyncio.to_thread(get_orderbook, symbol)

                if session == "Asia":
                    update_asia_range(symbol, price)

                asia_range = get_asia_range(symbol)
                liquidity = build_liquidity_map(orderbook)
                orderflow = calculate_orderflow(trades)

                direction = "LONG" if orderflow["delta"] > 0 else "SHORT"

                br = detect_break_retest(
                    price,
                    asia_range if session != "Asia" else None,
                    direction
                )

                # -------- MACRO DATA (BTC only) --------
                macro = 0
                if symbol.startswith("BTC"):
                    p_prev = prev_price.get(symbol, price)
                    price_change = price - p_prev

                    oi = open_interest()
                    ls = long_short_ratio()
                    liq = liquidations()
                    opt = options_oi()
                    etf = etf_flow()

                    macro = macro_score(
                        price_change, oi, ls, liq, opt, etf, price
                    )

                score = (
                    25 +
                    (20 if br else -10) +
                    (20 if abs(orderflow["delta"]) > 50 else -10) +
                    macro
                )

                now = time.time()
                if score >= SCORE_THRESHOLD and now - last_signal[symbol] > COOLDOWN:
                    msg = f"""
🔥 {normalize(symbol)} INSTITUTIONAL SIGNAL

🌍 Session: {session}
⏱ Kill Zone: {kill_zone}
📊 Score: {score}

🟢 Direction: {direction}
💰 Price: {price}

📉 Break & Retest: {"Yes" if br else "No"}

📈 Orderflow:
Delta: {orderflow['delta']}
CVD: {orderflow['cvd']}

🌐 Macro Bias:
Score: {macro}
"""
                    await bot.send_message(chat_id=CHANNEL_ID, text=msg)
                    last_signal[symbol] = now

                prev_price[symbol] = price
                await asyncio.sleep(6)

            except Exception as e:
                print("Error:", e)
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
