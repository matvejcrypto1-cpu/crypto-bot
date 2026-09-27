import asyncio
import os
import sys
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from handlers import router
from database import init_db

# Load variables from .env file
load_dotenv()

async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("Error: BOT_TOKEN environment variable is not set.", file=sys.stderr)
        print("Please set it using: export BOT_TOKEN='your_token'", file=sys.stderr)
        sys.exit(1)

    # Initialize database
    init_db()

    bot = Bot(token=token)
    dp = Dispatcher()
    
    dp.include_router(router)
    
    print("Bot is starting in polling mode...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped!")
