import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

API_BASE = "https://api.coingecko.com/api/v3"

WAITING_COIN = 0


def format_usd(value):
    """Форматирует число в читаемую цену USD."""
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
    """Форматирует процент изменения с + или -."""
    if change is None:
        return "N/A"
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.1f}%"


# ── API helpers ─────────────────────────────────────────────────────


def get_coin_price(coin_id):
    """Получает данные о монете через CoinGecko API."""
    url = f"{API_BASE}/coins/{coin_id}"
    params = {
        "localization": "false",
        "tickers": "false",
        "community_data": "false",
        "developer_data": "false",
        "sparkline": "false",
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_top_coins(limit=5):
    """Получает топ монет по капитализации."""
    url = f"{API_BASE}/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": "false",
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_global_data():
    """Получает глобальные данные рынка."""
    url = f"{API_BASE}/global"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()


# ── Telegram handlers ──────────────────────────────────────────────


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я крипто бот.\n\n"
        "Доступные команды:\n"
        "/price — узнать цену монеты\n"
        "/top — топ 5 монет по капитализации\n"
        "/dominance — доминация BTC и ETH"
    )


async def price_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🪙 Введи название монеты (например bitcoin, ethereum, solana):"
    )
    return WAITING_COIN


async def price_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    coin_id = update.message.text.strip().lower()

    try:
        data = get_coin_price(coin_id)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            await update.message.reply_text(
                f"❌ Монета «{coin_id}» не найдена. Попробуй ещё раз:"
            )
            return WAITING_COIN
        await update.message.reply_text("⚠️ Ошибка API. Попробуй позже.")
        return ConversationHandler.END
    except Exception:
        await update.message.reply_text("⚠️ Ошибка соединения. Попробуй позже.")
        return ConversationHandler.END

    name = data.get("name", coin_id)
    symbol = data.get("symbol", "").upper()
    market = data.get("market_data", {})
    price = market.get("current_price", {}).get("usd")
    change_24h = market.get("price_change_percentage_24h")
    market_cap = market.get("market_cap", {}).get("usd")

    message = (
        f"📊 {name} ({symbol})\n"
        f"💰 Цена: {format_usd(price)}\n"
        f"📈 За 24ч: {format_change(change_24h)}\n"
        f"💎 Капитализация: {format_usd(market_cap)}"
    )
    await update.message.reply_text(message)
    return ConversationHandler.END


async def price_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Отменено.")
    return ConversationHandler.END


async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        coins = get_top_coins(5)
    except Exception:
        await update.message.reply_text("⚠️ Ошибка API. Попробуй позже.")
        return

    lines = ["🏆 Топ 5 криптовалют\n"]
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
        await update.message.reply_text("⚠️ Ошибка API. Попробуй позже.")
        return

    market = data.get("data", {}).get("market_cap_percentage", {})
    btc = market.get("btc", 0)
    eth = market.get("eth", 0)

    message = (
        "📊 Доминация рынка\n\n"
        f"₿ Bitcoin: {btc:.1f}%\n"
        f"Ξ Ethereum: {eth:.1f}%"
    )
    await update.message.reply_text(message)


# ── main ────────────────────────────────────────────────────────────


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

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

    print("🤖 Крипто-бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
