BOT_TOKEN = "8741815015:AAFYgHfR0syP2PPzCYNm5ImOkrmx-KOiIFA"

from curl_cffi import requests as cffi_requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
import asyncio
import json
import re

CITY, PRICE = range(2)


def search_airbnb(city, max_price):
    """Ищет жильё на Airbnb через поисковую страницу."""
    search_url = f"https://www.airbnb.com/s/{city}/homes"
    params = {
        "price_max": str(max_price),
        "currency": "USD",
    }

    try:
        response = cffi_requests.get(
            search_url, params=params, impersonate="chrome110", timeout=15
        )
        response.raise_for_status()
        html = response.text

        # Ищем встроенные JSON-данные на странице
        match = re.search(
            r'<script[^>]*id="data-deferred-state-0"[^>]*>(.*?)</script>',
            html,
            re.DOTALL,
        )
        if not match:
            match = re.search(
                r'<script[^>]*id="data-deferred-state"[^>]*>(.*?)</script>',
                html,
                re.DOTALL,
            )
        if not match:
            return []

        data = json.loads(match.group(1))
        return _extract_listings(data, city)[:3]

    except Exception:
        return []


def _extract_listings(data, city):
    """Рекурсивно обходит JSON и собирает данные о листингах."""
    results = []
    seen_ids = set()

    def traverse(obj):
        if isinstance(obj, dict):
            # Листинг обычно содержит 'name' и 'id' числовой
            has_name = "name" in obj and isinstance(obj["name"], str)
            has_id = "id" in obj
            looks_like_listing = has_name and has_id and len(obj.get("name", "")) > 3

            if looks_like_listing:
                listing_id = str(obj["id"])
                # Пропускаем дубликаты и объекты без числового ID
                if listing_id.isdigit() and listing_id not in seen_ids:
                    seen_ids.add(listing_id)

                    # Цена
                    price = _extract_price(obj)

                    # Рейтинг
                    rating = (
                        obj.get("avgRating")
                        or obj.get("avgRatingLocalized")
                        or obj.get("rating")
                    )
                    rating_str = str(rating) if rating else "нет оценок"

                    results.append(
                        {
                            "name": obj["name"],
                            "city": city.capitalize(),
                            "price": price,
                            "rating": rating_str,
                            "url": f"https://www.airbnb.com/rooms/{listing_id}",
                        }
                    )

            for value in obj.values():
                traverse(value)

        elif isinstance(obj, list):
            for item in obj:
                traverse(item)

    traverse(data)
    return results


def _extract_price(obj):
    """Извлекает цену из разных форматов данных Airbnb."""
    # Прямое поле
    for key in ("formattedPrice", "priceString", "price"):
        val = obj.get(key)
        if isinstance(val, str) and val:
            return val

    # Вложенная структура pricing
    pricing = obj.get("pricingQuote") or obj.get("pricing") or {}
    if isinstance(pricing, dict):
        structured = pricing.get("structuredStayDisplayPrice", {})
        primary = structured.get("primaryLine", {})
        if primary.get("price"):
            return primary["price"]
        if pricing.get("price"):
            return str(pricing["price"])

    return "N/A"


# ── Telegram handlers ──────────────────────────────────────────────


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я помогу найти жильё на Airbnb.\n\n"
        "Команды:\n"
        "/search — начать поиск жилья\n\n"
        "Я спрошу город и максимальную цену за ночь, "
        "а затем покажу лучшие варианты 🏠"
    )


async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏙️ Введи город (например Paris):")
    return CITY


async def city_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text.strip()
    await update.message.reply_text("💰 Введи максимальную цену за ночь в USD:")
    return PRICE


async def price_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        max_price = int(text)
    except ValueError:
        await update.message.reply_text("⚠️ Введи число. Попробуй ещё раз:")
        return PRICE

    city = context.user_data["city"]
    await update.message.reply_text(
        f"🔍 Ищу жильё в {city} до ${max_price}/ночь..."
    )

    results = search_airbnb(city, max_price)

    if not results:
        await update.message.reply_text(
            "❌ Ничего не найдено, попробуй другой город"
        )
        return ConversationHandler.END

    for listing in results:
        message = (
            f"🏠 {listing['name']}\n"
            f"🏙️ {listing['city']}\n"
            f"💰 {listing['price']}/ночь\n"
            f"⭐ {listing['rating']}\n"
            f"🔗 {listing['url']}"
        )
        await update.message.reply_text(message)
        await asyncio.sleep(1)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Поиск отменён.")
    return ConversationHandler.END


# ── main ────────────────────────────────────────────────────────────


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("search", search_start)],
        states={
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city_input)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    print("🤖 Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
