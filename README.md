# Daily Quote Telegram Bot

A Telegram bot that shares inspirational quotes, either on demand or as a scheduled daily message.

## Features

- Send a random quote with `/quote`.
- Subscribe or unsubscribe from daily quotes.
- Deliver one daily quote to subscribers at 09:00 Israel time.
- Store subscriber information in a local SQLite database.
- Allow the configured administrator to broadcast a message to subscribers.

## Commands

| Command | Description |
| --- | --- |
| `/start` | Register and display the welcome message |
| `/quote` | Get a random quote |
| `/subscribe` | Subscribe to daily quotes |
| `/unsubscribe` | Stop receiving daily quotes |
| `/broadcast <message>` | Send a message to all subscribers (administrator only) |

## Requirements

- Python 3.9 or newer
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

## Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/itzikh02/daily-quote-tbot.git
   cd daily-quote-tbot
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root:

   ```env
   BOT_TOKEN=your_telegram_bot_token
   ADMIN_ID=your_telegram_numeric_user_id
   ```

   Keep this file private. It is excluded from Git.

5. Start the bot:

   ```bash
   python bot.py
   ```

The SQLite database is created automatically at `db/users.db` when the bot starts.

## Daily schedule

Daily quotes are scheduled for 09:00 in the `Asia/Jerusalem` time zone. The schedule follows Israel's daylight-saving-time changes.

## Project structure

```text
.
├── bot.py
├── quotes.json
├── requirements.txt
├── .env.example
└── db/
    └── .gitkeep
```
