from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
import os, random, json

# source .venv/bin/activate - to activate the virtual environment

# Load environment variables from .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if BOT_TOKEN is None:
    raise ValueError("BOT_TOKEN environment variable is not set.")


# Define the command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user_name = update.effective_user.first_name
    await update.message.reply_text(f"Hello, {user_name}! How can I help you?")

async def quote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Respond to the /quote command."""
    with open("quotes.json", "r") as file:
        quotes = json.load(file)
        quote = random.choice(quotes) 
    await update.message.reply_text(f"{quote['quote']}\n\n_{quote['name']}_", parse_mode="Markdown")

# Main function to set up the bot
def main():
    # Create the bot application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quote", quote))

    # Start polling for updates
    application.run_polling()

if __name__ == "__main__":
    main()