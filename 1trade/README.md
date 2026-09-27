# Telegram Bot with aiogram 3.x

A simple Telegram bot created in Python using the `aiogram` 3.x library. 
It supports multiple languages (English and Russian) with language preferences stored in a local SQLite database.

## Prerequisites

- Python 3.8 or higher
- A Telegram Bot Token

## How to get a Bot Token

1. Open Telegram and search for **@BotFather**
2. Start a chat and send the `/newbot` command
3. Follow the instructions to choose a name and a username for your bot
4. Once completed, BotFather will give you a token (e.g., `123456789:ABCdefGHIjklmNOPQrsTUVwxyZ`). Keep it secret!

## Installation

1. Clone or download this repository.
2. It's recommended to create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Bot

Before running the bot, you need to set the `BOT_TOKEN` environment variable.

**On Windows (Command Prompt):**
```cmd
set BOT_TOKEN=your_token_here
python bot.py
```

**On Windows (PowerShell):**
```powershell
$env:BOT_TOKEN="your_token_here"
python bot.py
```

**On Linux/macOS:**
```bash
export BOT_TOKEN=your_token_here
python bot.py
```

## Structure

- `bot.py` - Entry point, bot initialization and polling.
- `handlers.py` - Command and callback query handlers.
- `database.py` - SQLite database initialization and queries.
- `texts.py` - Localized string dictionary.
- `requirements.txt` - Project dependencies.
