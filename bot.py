import json
import logging
import os
import random
import sqlite3
from datetime import time
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from telegram import Update
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
DB_PATH = Path("db/users.db")
QUOTES_PATH = Path("quotes.json")
TIMEZONE = ZoneInfo("Asia/Jerusalem")
DAILY_QUOTE_TIME = time(hour=9, minute=0, tzinfo=TIMEZONE)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def connect_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                subscribed INTEGER NOT NULL DEFAULT 0
            )
            """
        )


def save_user(update: Update) -> None:
    user = update.effective_user
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name
            """,
            (user.id, user.username, user.first_name, user.last_name),
        )


def get_random_quote() -> dict:
    with QUOTES_PATH.open("r", encoding="utf-8") as file:
        quotes = json.load(file)
    if not quotes:
        raise ValueError("quotes.json does not contain any quotes.")
    return random.choice(quotes)


def get_subscriber_ids() -> list[int]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT user_id FROM users WHERE subscribed = 1"
        ).fetchall()
    return [row[0] for row in rows]


def format_quote(quote: dict) -> str:
    return f"{quote['quote']}\n\n- {quote['name']}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    save_user(update)
    name = update.effective_user.first_name or "there"
    await update.message.reply_text(
        f"Hello, {name}! Use /quote for a random quote or /subscribe to receive a daily quote."
    )


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    save_user(update)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE users SET subscribed = 1 WHERE user_id = ?",
            (update.effective_user.id,),
        )
    await update.message.reply_text("You are now subscribed to the daily quote.")


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    save_user(update)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE users SET subscribed = 0 WHERE user_id = ?",
            (update.effective_user.id,),
        )
    await update.message.reply_text("You have been unsubscribed from the daily quote.")


async def quote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        selected_quote = get_random_quote()
        await update.message.reply_text(format_quote(selected_quote))
    except (OSError, json.JSONDecodeError, KeyError, ValueError):
        logger.exception("Could not load a random quote.")
        await update.message.reply_text("Sorry, a quote is unavailable right now.")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not ADMIN_ID or str(update.effective_user.id) != ADMIN_ID:
        logger.warning(
            "Unauthorized broadcast attempt by Telegram user %s",
            update.effective_user.id,
        )
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast Your message")
        return

    message = " ".join(context.args)
    sent = 0
    failed = 0
    for user_id in get_subscriber_ids():
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
            sent += 1
        except TelegramError:
            logger.exception("Broadcast failed for user %s", user_id)
            failed += 1

    await update.message.reply_text(
        f"Broadcast completed. Sent: {sent}. Failed: {failed}."
    )


async def daily_quote(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        message = format_quote(get_random_quote())
    except (OSError, json.JSONDecodeError, KeyError, ValueError):
        logger.exception("Could not prepare the daily quote.")
        return

    for user_id in get_subscriber_ids():
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
        except TelegramError:
            logger.exception("Daily quote delivery failed for user %s", user_id)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("An error occurred while handling an update.", exc_info=context.error)


def main() -> None:
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is not set.")

    connect_db()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quote", quote))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_error_handler(error_handler)

    if application.job_queue is None:
        raise RuntimeError(
            "JobQueue is unavailable. Install python-telegram-bot[job-queue]."
        )

    application.job_queue.run_daily(
        daily_quote,
        time=DAILY_QUOTE_TIME,
        name="daily_quote",
    )
    logger.info(
        "Bot is starting. Daily quotes are scheduled for 09:00 Asia/Jerusalem."
    )
    application.run_polling()


if __name__ == "__main__":
    main()
