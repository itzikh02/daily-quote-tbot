from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from dotenv import load_dotenv
import os

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

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Respond to the /hello command."""
    user_name = update.effective_user.first_name
    await update.message.reply_text(f"Hello, {user_name}!")

# Main function to set up the bot
def main():
    # Create the bot application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("hello", hello))

    # Start polling for updates
    application.run_polling()

if __name__ == "__main__":
    main()