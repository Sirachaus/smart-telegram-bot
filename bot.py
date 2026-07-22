import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Quotes added around the token here!
TOKEN = '8819821570:AAF1FI5UpWd3_l1E8jPSkjn07nnSlrhWl0k'

# Enable basic logging to see errors in Termux
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Function to handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    await update.message.reply_text(f"Hello {user_first_name}! I am your custom Telegram bot running live from Termux.")

# Function to echo back regular text messages
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.reply_text(f"You said: {user_text}")

if __name__ == '__main__':
    # Build the application
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Add handlers for commands and text
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    
    print("Bot is running... Press Ctrl+C in Termux to stop.")
    app.run_polling()

app = ApplicationBuilder().token(TOKEN).build()
app = ApplicationBuilder().token(TOKEN).connect_timeout(30.0).read_timeout(30.0).build()

import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = '8819821570:AAF1FI5UpWd3_l1E8jPSkjn07nnSlrhWl0k'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 1. Custom /start welcome message (Termux removed!)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Hello {user_first_name}! 👋\nWelcome to Swizzy-bot! How can I assist you today?"
    )

# 2. Custom reply message (instead of just repeating what you say)
async def custom_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.lower()
    
    # Simple keyword responses
    if "how are you" in user_text:
        await update.message.reply_text("I'm doing great, thank you! How are you doing?")
    elif "help" in user_text:
        await update.message.reply_text("I can assist you with answering questions, automated customer service, and more!")
    else:
        await update.message.reply_text(f"Thanks for your message: '{update.message.text}'! My creator is working on adding more smart features to me.")

if __name__ == '__main__':
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .get_updates_connect_timeout(30.0)
        .get_updates_read_timeout(30.0)
        .build()
    )
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), custom_reply))
    
    print("Bot is running... Press Ctrl+C in Termux to stop.")
    app.run_polling()
