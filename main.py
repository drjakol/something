import asyncio
import os
from fastapi import FastAPI
from telegram import Bot
import uvicorn

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

SCORE_THRESHOLD = 70   # حداقل امتیاز ارسال سیگنال

app = FastAPI()
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
    if not stop_hunt:
        score += 20
    else:
        score -= 15

    # False Breakout
    if false_breakout_passed:
        score += 20
    else:
        score -= 10

    # Consolidation
    if not in_consolidation:
        score += 15
    else:
        score -= 20

    # Delta strength
    if abs(delta_data["delta"]) > 10:
        score += 15

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
                price = await asyncio.to_thread(get_price, symbol)
                orderbook = await asyncio.to_thread(get_orderbook, symbol)
                trades = await asyncio.to_thread(get_trades, symbol)

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

                in_consolidation = check_consolidation(orderbook)

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

                    msg = f"""
📍 {normalize_symbol(symbol)} – Signal Report

🟦 Type: {strategy_type}
🟢 Direction: {direction}
📈 Entry Zone: {levels['entry']}
🛑 SL: {levels['sl']}
🎯 TP1: {levels['tp1']} | TP2: {levels['tp2']}
"""

                    await bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=msg
                    )

                prev_prices[symbol] = price
                await asyncio.sleep(6)

            except Exception as e:
                print(f"Error {symbol}: {e}")
                await asyncio.sleep(6)

        await asyncio.sleep(120)

# ---------------- FASTAPI ----------------
@app.get("/")
def root():
    return {"status": "running"}

@app.on_event("startup")
async def startup():
    asyncio.create_task(telegram_bot())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
