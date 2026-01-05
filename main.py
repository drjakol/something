import time
import os
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

print("Bot is starting...")

bot = Bot(token=BOT_TOKEN)

bot.send_message(
    chat_id=CHANNEL_ID,
    text="✅ Bot successfully started and is running on server."
)

while True:
    time.sleep(60)
