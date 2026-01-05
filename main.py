import asyncio
import os
from fastapi import FastAPI
from telegram import Bot
from data_okx import get_price, get_trades, get_orderbook
from liquidity_map import build_liquidity_map
from stop_hunt import detect_stop_hunt
from false_breakout import filter_false_breakout
from consolidation import check_consolidation
from orderflow import calculate_delta
import uvicorn

# --- تنظیمات ربات ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

app = FastAPI()
bot = Bot(token=BOT_TOKEN)

@app.get("/")
def root():
    return {"status": "bot is running"}

async def telegram_bot():
    print("Bot is starting...")
    prev_price = None

    while True:
        try:
            # دریافت دیتا
            price = get_price("BTC/USDT")
            orderbook = get_orderbook("BTC/USDT")
            trades = get_trades("BTC/USDT")
            liq = build_liquidity_map(orderbook)
            delta_data = calculate_delta(trades)

            # Stop Hunt
            stop_hunt = detect_stop_hunt(
                price=price,
                liquidity=liq,
                delta=delta_data["delta"]
            )

            # False Breakout Filter
            if prev_price is not None:
                breakout_real = filter_false_breakout(price, liq, prev_price)
            else:
                breakout_real = True

            # Consolidation Check
            in_consolidation = check_consolidation(orderbook)

            # اگر سیگنال معتبر بود
            if stop_hunt and breakout_real and not in_consolidation:
                strategy_type = "Aggressive" if stop_hunt["strength"] > 50 else "Conservative"
                await bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=f"""
🧠 Stop Hunt Detected – BTCUSDT
Direction: {stop_hunt['type']}
Reason: {stop_hunt['reason']}
Price: {price}
Support: {liq['support']}, Resistance: {liq['resistance']}
Delta: {delta_data['delta']}
Strategy Type: {strategy_type}
"""
                )

            prev_price = price
            await asyncio.sleep(60)

        except Exception as e:
            print(f"Error in bot loop: {e}")
            await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(telegram_bot())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
