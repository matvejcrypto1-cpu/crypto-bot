import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

import requests
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

API_BASE = "https://api.coingecko.com/api/v3"
API_HEADERS = {"accept": "application/json", "user-agent": "Mozilla/5.0"}

WAITING_COIN = 0


def format_usd(value):
    """Formats a number into a readable USD price."""
    if value is None:
        return "N/A"
    if value >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.1f}T"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1:
        return f"${value:,.2f}"
    return f"${value:.6f}"


def format_change(change):
    """Formats percentage change with + or - sign."""
    if change is None:
        return "N/A"
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.1f}%"


# ── API helpers ─────────────────────────────────────────────────────


def get_coin_price(coin_id):
    """Fetches coin data from CoinGecko API."""
    url = f"{API_BASE}/coins/{coin_id}"
    params = {
        "localization": "false",
        "tickers": "false",
        "community_data": "false",
        "developer_data": "false",
        "sparkline": "false",
    }
    resp = requests.get(url, params=params, headers=API_HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_top_coins(limit=5):
    """Fetches top coins by market cap."""
    url = f"{API_BASE}/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": "false",
    }
    resp = requests.get(url, params=params, headers=API_HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_global_data():
    """Fetches global market data."""
    url = f"{API_BASE}/global"
    resp = requests.get(url, headers=API_HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()


# ── Telegram handlers ──────────────────────────────────────────────


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I'm a crypto bot.\n\n"
        "Available commands:\n"
        "/price — check coin price\n"
        "/top — top 5 coins by market cap\n"
        "/dominance — BTC and ETH dominance"
    )


async def price_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("price_start called by user %s", update.effective_user.id)
    await update.message.reply_text(
        "🪙 Enter coin name (e.g. bitcoin, ethereum, solana):"
    )
    return WAITING_COIN


async def price_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coin_id = update.message.text.strip().lower()
    logging.info("price_input called with coin: %s", coin_id)

    try:
        data = get_coin_price(coin_id)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            await update.message.reply_text(
                f"❌ Coin \"{coin_id}\" not found. Try again:"
            )
            return WAITING_COIN
        await update.message.reply_text("⚠️ API is temporarily unavailable, try again in a minute")
        return ConversationHandler.END
    except Exception:
        await update.message.reply_text("⚠️ API is temporarily unavailable, try again in a minute")
        return ConversationHandler.END

    name = data.get("name", coin_id)
    symbol = data.get("symbol", "").upper()
    market = data.get("market_data", {})
    price = market.get("current_price", {}).get("usd")
    change_24h = market.get("price_change_percentage_24h")
    market_cap = market.get("market_cap", {}).get("usd")

    message = (
        f"📊 {name} ({symbol})\n"
        f"💰 Price: {format_usd(price)}\n"
        f"📈 24h: {format_change(change_24h)}\n"
        f"💎 Market Cap: {format_usd(market_cap)}"
    )
    await update.message.reply_text(message)
    return ConversationHandler.END


async def price_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END


async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        coins = get_top_coins(5)
    except Exception:
        await update.message.reply_text("⚠️ API is temporarily unavailable, try again in a minute")
        return

    lines = ["🏆 Top 5 Cryptocurrencies\n"]
    for i, coin in enumerate(coins, start=1):
        name = coin.get("name", "Unknown")
        price = format_usd(coin.get("current_price"))
        change = format_change(coin.get("price_change_percentage_24h"))
        lines.append(f"{i}. {name} — {price} ({change})")

    await update.message.reply_text("\n".join(lines))


async def dominance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = get_global_data()
    except Exception:
        await update.message.reply_text("⚠️ API is temporarily unavailable, try again in a minute")
        return

    market = data.get("data", {}).get("market_cap_percentage", {})
    btc = market.get("btc", 0)
    eth = market.get("eth", 0)

    message = (
        "📊 Market Dominance\n\n"
        f"₿ Bitcoin: {btc:.1f}%\n"
        f"Ξ Ethereum: {eth:.1f}%"
    )
    await update.message.reply_text(message)


# ── main ────────────────────────────────────────────────────────────


async def post_init(app):
    commands = [
        ("start", "Start the bot"),
        ("price", "Check coin price"),
        ("top", "Top 5 cryptocurrencies"),
        ("dominance", "Market dominance"),
        ("help", "Help"),
    ]
    await app.bot.set_my_commands(commands)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 Available commands:\n\n"
        "/price — check coin price\n"
        "/top — top 5 coins by market cap\n"
        "/dominance — BTC and ETH dominance\n"
        "/help — this help message"
    )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    price_handler = ConversationHandler(
        entry_points=[CommandHandler("price", price_start)],
        states={
            WAITING_COIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, price_input)
            ],
        },
        fallbacks=[CommandHandler("cancel", price_cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(price_handler)
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("dominance", dominance))
    app.add_handler(CommandHandler("help", help_cmd))

    async def error_handler(update, context):
        logging.error("Exception: %s", context.error, exc_info=context.error)
        if update and update.effective_message:
            await update.effective_message.reply_text(
                f"⚠️ Error: {context.error}"
            )

    app.add_error_handler(error_handler)

    print("🤖 Crypto bot started...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
