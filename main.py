import asyncio
import os
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

async def main():
    print("Bot is starting...")

    bot = Bot(token=BOT_TOKEN)

    await bot.send_message(
        chat_id=CHANNEL_ID,
        text="✅ Bot successfully started and is running on server."
    )

    while True:
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
