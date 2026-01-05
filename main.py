import asyncio
import os
from fastapi import FastAPI
from telegram import Bot
from data_okx import get_price, get_trades, get_orderbook
from liquidity_map import build_liquidity_map
from stop_hunt import detect_stop_hunt
import uvicorn

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

app = FastAPI()
bot = Bot(token=BOT_TOKEN)

@app.get("/")
def root():
    return {"status": "bot is running"}

async def telegram_bot():
    print("Bot is starting...")
    price = get_price("BTC/USDT")
    orderbook = get_orderbook("BTC/USDT")
    liq = build_liquidity_map(orderbook)
    stop_hunt = detect_stop_hunt(
        price=price,
        liquidity=liq,
        delta=delta_data["delta"]
    )

    if stop_hunt:
    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=f"""
🧠 Stop Hunt Detected – BTCUSDT

Direction: {stop_hunt['type']}
Reason: {stop_hunt['reason']}
"""
    )

    while True:
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(telegram_bot())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
