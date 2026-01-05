import ccxt

exchange = ccxt.bybit({
    "enableRateLimit": True,
    "options": {
        "defaultType": "future"
    }
})

SYMBOLS = [
    "BTC/USDT", "SOL/USDT", "AVAX/USDT",
    "DOT/USDT", "LTC/USDT", "DOGE/USDT",
    "LINK/USDT", "UNI/USDT"
]

def get_orderbook(symbol, limit=100):
    return exchange.fetch_order_book(symbol, limit=limit)

def get_trades(symbol, limit=200):
    return exchange.fetch_trades(symbol, limit=limit)

def get_price(symbol):
    ticker = exchange.fetch_ticker(symbol)
    return ticker["last"]
