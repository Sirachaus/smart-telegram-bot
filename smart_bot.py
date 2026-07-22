import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandlerimport logging
import wikipedia
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Your Telegram Bot Token
TOKEN = '8819821570:AAF1FI5UpWd3_l1E8jPSkjn07nnSlrhWl0k'

# Configure Wikipedia language to English
wikipedia.set_lang("en")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Clean Welcome Message
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Hello {user_first_name}! 👋\n\nI am your Smart Assistant! Ask me any question or topic, and I will search and explain it to you!"
    )

# Search & Answer Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text
    
    # Send a "typing..." action so the user knows the bot is searching
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Search Wikipedia for the user's query and get a 3-sentence summary
        summary = wikipedia.summary(user_query, sentences=3)
        await update.message.reply_text(f"📖 **Answer for '{user_query}':**\n\n{summary}")
    except wikipedia.exceptions.DisambiguationError as e:
        # If the search query has multiple meanings
        options = ", ".join(e.options[:5])
        await update.message.reply_text(f"Your question matches multiple topics! Did you mean one of these?\n👉 {options}")
    except wikipedia.exceptions.PageError:
        # If no page was found
        await update.message.reply_text(f"I couldn't find an exact article for '{user_query}'. Try searching with slightly different words!")
    except Exception as e:
        await update.message.reply_text("I encountered a connection error. Please check your network and try again!")

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
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Smart Bot is running...")
    app.run_polling()
import logging
import wikipedia
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = '8819821570:AAF1FI5UpWd3_l1E8jPSkjn07nnSlrhWl0k'

wikipedia.set_lang("en")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Hello {user_first_name}! 👋\n\nI am your Smart Assistant! Ask me any question or topic, and I will search and explain it to you!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        summary = wikipedia.summary(user_query, sentences=3)
        await update.message.reply_text(f"📖 **Answer for '{user_query}':**\n\n{summary}")
    except wikipedia.exceptions.DisambiguationError as e:
        options = ", ".join(e.options[:5])
        await update.message.reply_text(f"Your question matches multiple topics! Did you mean one of these?\n👉 {options}")
    except wikipedia.exceptions.PageError:
        await update.message.reply_text(f"I couldn't find an exact article for '{user_query}'. Try rephrasing your question!")
    except Exception:
        await update.message.reply_text("I encountered a connection error. Please try again!")

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
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Smart Bot is running...")
    app.run_polling()
import logging
import wikipedia
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = '8819821570:AAF1FI5UpWd3_l1E8jPSkjn07nnSlrhWl0k'

wikipedia.set_lang("en")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Hello {user_first_name}! 👋\n\nI am your Smart Assistant! Ask me any question or topic, and I will search and explain it to you!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        summary = wikipedia.summary(user_query, sentences=3)
        await update.message.reply_text(f"📖 **Answer for '{user_query}':**\n\n{summary}")
    except wikipedia.exceptions.DisambiguationError as e:
        options = ", ".join(e.options[:5])
        await update.message.reply_text(f"Your question matches multiple topics! Did you mean one of these?\n👉 {options}")
    except wikipedia.exceptions.PageError:
        await update.message.reply_text(f"I couldn't find an exact article for '{user_query}'. Try rephrasing your question!")
    except Exception:
        await update.message.reply_text("I encountered a connection error. Please try again!")

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
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Smart Bot is running...")
    app.run_polling()

import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Tiny dummy server so Render's Web Service stays happy
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is online and healthy!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# Start the server in a background thread
threading.Thread(target=run_dummy_server, daemon=True).start()

