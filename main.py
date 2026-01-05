import asyncio
import os
from fastapi import FastAPI
from telegram import Bot
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

    await bot.send_message(
        chat_id=CHANNEL_ID,
        text="✅ Bot successfully started and is running on Render Web Service."
    )

    while True:
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(telegram_bot())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
