import asyncio
import os
from fastapi import FastAPI
from telegram import Bot
from data_okx import get_price
from liquidity_map import build_liquidity_map
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

    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=f"""
🗺 Liquidity Map – BTCUSDT

Support Zone: {liq['support']}
Resistance Zone: {liq['resistance']}

Top Bid Liquidity:
{liq['bid_liquidity'][:3]}

Top Ask Liquidity:
{liq['ask_liquidity'][:3]}
"""
)

    while True:
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(telegram_bot())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
