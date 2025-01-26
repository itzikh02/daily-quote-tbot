from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
import os, random, json, sqlite3, time, schedule, threading, asyncio

load_dotenv()
ADMIN_ID = os.getenv("ADMIN_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")


# source .venv/bin/activate - to activate the virtual environment

def run_polling(application):
    """Run the Telegram bot polling inside an event loop."""
    asyncio.run(application.run_polling())

# connect or create the database
def connect_db():
    with sqlite3.connect('./db/users.db') as conn:
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        subscribed INTEGER DEFAULT 0)
    ''')

# Define the command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_name = update.effective_user.username
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name

    with sqlite3.connect('./db/users.db') as conn:
        c = conn.cursor()
        c.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
        ''', (user_id, user_name, first_name, last_name))

    await update.message.reply_text(f"Hello, {user_name}! How can I help you?")

# allow the user to subcribe to the bot
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_name = update.effective_user.username

    with sqlite3.connect('./db/users.db') as conn:
        c = conn.cursor()
        c.execute('''
        UPDATE users
        SET subscribed = 1
        WHERE user_id = ?
        ''', (user_id,))

    await update.message.reply_text(f"Thanks, {user_name}! You have been subscribed to the bot.")

# allow the user to unsubscribe from the bot
async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_name = update.effective_user.username

    with sqlite3.connect('./db/users.db') as conn:
        c = conn.cursor()
        c.execute('''
        UPDATE users
        SET subscribed = 0
        WHERE user_id = ?
        ''', (user_id,))

    await update.message.reply_text(f"Thanks, {user_name}! You have been unsubscribed from the bot.")

async def quote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Respond to the /quote command."""
    with open("quotes.json", "r") as file:
        quotes = json.load(file)
        quote = random.choice(quotes) 
    await update.message.reply_text(f"{quote['quote']}\n\n_{quote['name']}_", parse_mode="Markdown")

# SEND MESSAGE TO ALL SUBSCRIBED USERS

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != str(ADMIN_ID):
        # await update.message.reply_text("You are not authorized to use this command.")
        print(f"Unauthorized access to broadcast command by user {update.effective_user.id}")
        return

    if not context.args:
        await update.message.reply_text("Please provide a message to broadcast.")
        return

    text = " ".join(context.args)

    with sqlite3.connect('./db/users.db') as conn:
        c = conn.cursor()
        c.execute('''
            SELECT user_id
            FROM users
            WHERE subscribed = 1
        ''')
        user_ids = c.fetchall()

    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id[0], text=text)
        except Exception as e:
            print(f"Failed to send message to {user_id[0]}: {e}")

    await update.message.reply_text("Message sent to all subscribers.")

# daily quote to subscribed users

async def daily_quote() -> None:
    """Send a daily quote to all subscribed users."""
    with open("quotes.json", "r") as file:
        quotes = json.load(file)
        quote = random.choice(quotes)

    # Send daily quote to all subscribed users
    with sqlite3.connect('./db/users.db') as conn:
        c = conn.cursor()
        c.execute('''
            SELECT user_id
            FROM users
            WHERE subscribed = 1
        ''')
        user_ids = c.fetchall()

    for user_id in user_ids:
        try:
            # Assuming context is available in this scope
            await bot.send_message(chat_id=user_id[0], text=f"{quote['quote']}\n\n_{quote['name']}_", parse_mode="Markdown")
        except Exception as e:
            print(f"Failed to send message to {user_id[0]}: {e}")

# Function to schedule daily quotes
def schedule_daily_quote():
    schedule.every().day.at("09:00").do(run_daily_quote)
    print(f"Scheduled daily quote task. Time now is {time.strftime('%H:%M:%S')}")
    while True:
        schedule.run_pending()  # Check for pending tasks and run them
        time.sleep(60)  # Wait 1 minute between checks

# Wrapper function to trigger daily quote
def run_daily_quote():
    asyncio.run(daily_quote())

# Main function to set up the bot
def main():
    connect_db()

    if BOT_TOKEN is None:
        raise ValueError("BOT_TOKEN environment variable is not set.")
    
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quote", quote))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CommandHandler("broadcast", broadcast))

    # Start polling for updates
    
    # Start the daily quote scheduler in a separate thread
    threading.Thread(target=schedule_daily_quote).start()

    # Run the Telegram bot polling in the main thread
    run_polling(application)
    
if __name__ == "__main__":
    main()
