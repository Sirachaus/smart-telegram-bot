import os
import logging
import asyncio
from datetime import datetime
import pytz
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from google import genai

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
ALLOWED_USER_IDS = [6124380017]

# Initialize the official Google GenAI client
client = genai.Client(api_key=GEMINI_API_KEY)

MARKET_LEARNING_MEMORY = []

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def is_authorized(user_id: int) -> bool:
    if not ALLOWED_USER_IDS:
        return True
    return user_id in ALLOWED_USER_IDS

# --- WEB SERVER HEALTH CHECK ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args):
        return

def run_web_server():
    server = HTTPServer(('0.0.0.0', 10000), SimpleHandler)
    server.serve_forever()

# --- SELF-LEARNING UNIVERSAL AI RESEARCH ENGINE ---
def universal_market_research_with_learning(query: str) -> str:
    try:
        memory_context = "\n".join(MARKET_LEARNING_MEMORY[-5:]) if MARKET_LEARNING_MEMORY else "No prior patterns recorded yet."
        
        prompt = (
            f"You are an advanced quantitative self-learning trading assistant. "
            f"Analyze the asset, pair, stock, index, or crypto requested: '{query}'.\n\n"
            f"Recent historical market learning database and pattern notes:\n{memory_context}\n\n"
            f"Provide a thorough institutional breakdown: current trend perspective, psychological market behavior, support/resistance levels, and any new behavioral anomalies detected. "
            f"Conclude with a single-line summary pattern insight that the system should learn from for future scans."
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        analysis_result = response.text
        
        MARKET_LEARNING_MEMORY.append(f"Asset: {query} | Timestamp: {datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M')} | Insight logged.")
        return analysis_result
    except Exception as e:
        logger.error(f"AI self-learning research error: {e}")
        return f"⚠️ Error processing self-learning module for '{query}': {e}"

# --- TELEGRAM HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    await update.message.reply_text(
        "🧠 **Self-Learning AI Trading & Research Bot Online!**\n\n"
        "I am fully configured with my Gemini cognitive engine and internal learning memory bank. I can scan **any asset, stock, crypto, index, or forex pair** and adapt to new market behaviors over time.\n\n"
        "💡 **Commands:**\n"
        "• `/scan [Asset]` - Deep dynamic research & pattern tracking\n"
        "• `/memory` - View active self-learning patterns stored by the bot\n"
        "• Or chat with me normally about any strategy or concept!"
    )

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("⚠️ Please specify an asset to scan. Example: `/scan EURUSD` or `/scan Gold`")
        return
    
    asset_query = " ".join(context.args)
    await update.message.reply_text(f"🔄 Executing self-learning scan and behavioral pattern analysis for `{asset_query}`...")
    
    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, universal_market_research_with_learning, asset_query)
    await update.message.reply_text(report)

async def view_memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    if not MARKET_LEARNING_MEMORY:
        await update.message.reply_text("🧠 Learning memory bank is currently empty. Run a few `/scan` commands to start building patterns!")
        return
    
    memory_text = "🧠 **Active Self-Learning Pattern Bank:**\n\n" + "\n".join([f"• {item}" for item in MARKET_LEARNING_MEMORY[-10:]])
    await update.message.reply_text(memory_text)

async def handle_conversational_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    
    user_message = update.message.text
    await update.message.chat.send_action("typing")
    
    try:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"You are an expert quantitative self-learning assistant. Answer accurately, taking market adaptability into account: {user_message}"
            )
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        logger.error(f"AI Chat Error: {e}")
        await update.message.reply_text("⚠️ Sorry, I encountered an error processing your query.")

def main():
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()

    application = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("scan", scan_command))
    application.add_handler(CommandHandler("memory", view_memory_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_conversational_ai))

    application.run_polling()

if __name__ == "__main__":
    main()

