import asyncio, os, time, json
from datetime import datetime, timezone
from collections import defaultdict
from fastapi import FastAPI
from telegram import Bot
import ccxt

from data_okx import get_price, get_trades, get_orderbook
from liquidity_map import build_liquidity_map
from orderflow import calculate_orderflow
from consolidation import check_consolidation
from stop_hunt import detect_stop_hunt
from kill_zones import get_kill_zone
from session_filter import active_session
from range_tracker import update_asia_range, get_asia_range
from break_retest import detect_break_retest

from htf_bias import get_htf_bias
from volatility_filter import volatility_ok
from risk_engine import build_trade
from score_engine import smart_score_v2
from stats_engine import calculate_stats
from capital_guard import trading_allowed

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
bot = Bot(BOT_TOKEN)

exchange = ccxt.okx({"enableRateLimit": True})
last_signal = defaultdict(lambda: 0)

COINS = ["BTC/USDT"]
COOLDOWN = 600
BASE_SCORE_THRESHOLD = 70

async def bot_loop():
    while True:
        for symbol in COINS:
            try:
                if not trading_allowed():
                    continue

                session = active_session()
                if not session or not get_kill_zone():
                    continue

                price = await asyncio.to_thread(get_price, symbol)
                trades = await asyncio.to_thread(get_trades, symbol)
                ob = await asyncio.to_thread(get_orderbook, symbol)

                if session == "Asia":
                    update_asia_range(symbol, price)

                asia = get_asia_range(symbol)
                of = calculate_orderflow(trades)
                direction = "LONG" if of["delta"] > 0 else "SHORT"

                br = detect_break_retest(price, asia, direction)
                liq = build_liquidity_map(ob)
                stop = detect_stop_hunt(price, liq, of["delta"])
                cons = check_consolidation(ob)

                htf = get_htf_bias(symbol)
                if (direction == "LONG" and htf == "BEARISH") or \
                   (direction == "SHORT" and htf == "BULLISH"):
                    continue

                candles = exchange.fetch_ohlcv(symbol, "5m", limit=50)
                if not volatility_ok(candles):
                    continue

                base_score = 0
                base_score += 25 if br else -20
                base_score += 20 if stop else 0
                base_score += 15 if liq else -10
                base_score -= 20 if cons else 0

                stats = calculate_stats()
                winrate = stats["winrate"] if stats else None
                score = smart_score_v2(base_score, winrate)

                if score < BASE_SCORE_THRESHOLD:
                    continue

                now = time.time()
                if now - last_signal[symbol] < COOLDOWN:
                    continue

                trade = build_trade(price, direction, sl_distance=price*0.002)

                msg = f"""
🔥 {symbol.replace('/','')} v2 REAL TRADE

Direction: {direction}
Entry: {trade['entry']}
SL: {trade['sl']}
TP: {trade['tp1']}
RR: {trade['rr']}
Score: {score}
HTF Bias: {htf}
"""
                await bot.send_message(CHANNEL_ID, msg)
                last_signal[symbol] = now

            except Exception as e:
                print("ERR:", e)

        await asyncio.sleep(30)

app = FastAPI()

@app.on_event("startup")
async def startup():
    asyncio.create_task(bot_loop())

@app.get("/")
def root():
    return {"status": "v2 running"}
