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

COINS = ["BTC/USDT", "SOL/USDT", "AVAX/USDT", "DOT/USDT", 
         "LTC/USDT", "DOGE/USDT", "LINK/USDT", "UNI/USDT"]

@app.get("/")
def root():
    return {"status": "bot is running"}

async def telegram_bot():
    print("Bot is starting...")
    prev_prices = {symbol: None for symbol in COINS}

    while True:
        for symbol in COINS:
            try:
                # دریافت دیتا
                price = get_price(symbol)
                orderbook = get_orderbook(symbol)
                trades = get_trades(symbol)
                liq = build_liquidity_map(orderbook)
                delta_data = calculate_delta(trades)

                # Stop Hunt
                stop_hunt = detect_stop_hunt(
                    price=price,
                    liquidity=liq,
                    delta=delta_data["delta"]
                )

                # False Breakout Filter
                prev_price = prev_prices.get(symbol)
                if prev_price is not None:
                    breakout_real = filter_false_breakout(price, liq, prev_price)
                else:
                    breakout_real = True

                # Consolidation Check
                in_consolidation = check_consolidation(orderbook)

                if True:  # True برای تست اولیه
                    await bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=f"Test message for {symbol} ✅"
                    )

                # ارسال سیگنال فقط اگر شرایط درست باشد
                if stop_hunt and breakout_real and not in_consolidation:
                    # تعیین نوع استراتژی
                    if stop_hunt["strength"] > 50:
                        strategy_type = "Aggressive"
                        emoji = "🔴"
                    else:
                        strategy_type = "Conservative"
                        emoji = "🟢"

                    await bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=f"""
{emoji} *Stop Hunt Detected – {symbol}*

*Direction:* {stop_hunt['type']}
*Reason:* {stop_hunt['reason']}
*Price:* {price}
*Support:* {liq['support']} | *Resistance:* {liq['resistance']}
*Delta:* {delta_data['delta']}
*Strategy Type:* {strategy_type}
"""
                    , parse_mode="Markdown")

                prev_prices[symbol] = price
                await asyncio.sleep(6)  # جلوگیری از محدودیت API

            except Exception as e:
                print(f"Error for {symbol}: {e}")
                await asyncio.sleep(6)

        await asyncio.sleep(120)  # بررسی دوره‌ای هر 120 ثانیه

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(telegram_bot())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
