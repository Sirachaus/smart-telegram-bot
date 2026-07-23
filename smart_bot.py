import os
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import wikipedia
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- CONFIGURATION ---
TOKEN = '8819821570:AAF1FI5UpWd3_l1E8jPSkjn07nnSlrhW10k'
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")

# Initialize Gemini Client if key exists
ai_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

# --- DUMMY WEB SERVER FOR RENDER HEALTH CHECKS ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        return  # Suppress HTTP server log spam

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

# Start dummy server in background
threading.Thread(target=run_web_server, daemon=True).start()

# --- LOGGING SETUP ---
wikipedia.set_lang("en")
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- BOT COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 *Welcome to Super Bot!*\n\n"
        "• `/ai <question>` - Ask Gemini AI\n"
        "• `/wiki <topic>` - Search Wikipedia"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ai_client:
        await update.message.reply_text("⚠️ GEMINI_API_KEY is missing on Render.")
        return

    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("Please provide a prompt! Example: `/ai What is Python?`")
        return

    await update.message.reply_text("🧠 Thinking...")
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def wiki(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Please specify a topic! Example: `/wiki Python`")
        return

    try:
        summary = wikipedia.summary(query, sentences=3)
        await update.message.reply_text(f"📖 *{query.title()}*\n\n{summary}", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("❌ Topic not found on Wikipedia.")

# --- MAIN ENGINE ---
if __name__ == '__main__':
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ai", ai_chat))
    app.add_handler(CommandHandler("wiki", wiki))

    print("Smart Bot is running...")
    app.run_polling()

