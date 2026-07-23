8819821570:AAEa0--l0oSAFaDka1HeWmtIpU45eh2d0SE

import os
import glob
import asyncio
import threading
import logging
from datetime import datetime
import pytz
from http.server import HTTPServer, BaseHTTPRequestHandler

import requests
from bs4 import BeautifulSoup
import wikipedia
import yfinance as yf
import yt_dlp
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- CONFIGURATION ---
TOKEN = '8819821570:AAF1FI5UpWd3_l1E8jPSkjn07nnSlrhW10k'
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")

# Default chat ID for proactive market alerts (populated automatically on /start)
ALERT_CHAT_ID = None

# Initialize Gemini Client
ai_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

# --- DUMMY WEB SERVER FOR RENDER HEALTH CHECKS ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        return  # Suppress HTTP logging noise

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# --- LOGGING SETUP ---
wikipedia.set_lang("en")
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- HELPER TECHNICAL FUNCTIONS ---
def compute_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / (loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def analyze_candles_and_levels(df):
    """Calculates highest/lowest wicks, key support/resistance, and dynamic SL/TP levels."""
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    current_price = latest['Close']
    high_wick = df['High'].tail(10).max()
    low_wick = df['Low'].tail(10).min()

    # Average True Range (ATR) approximation for volatility-based SL/TP
    data_range = (df['High'] - df['Low']).tail(14).mean()

    # Key Support & Resistance based on recent wick extremes
    support = low_wick
    resistance = high_wick

    # Bullish vs Bearish bias
    ma_20 = df['Close'].rolling(window=20).mean().iloc[-1]
    is_bullish = current_price > ma_20

    if is_bullish:
        stop_loss = support - (data_range * 0.5)
        take_profit = current_price + ((current_price - stop_loss) * 2.0)  # 1:2 Risk-Reward
        signal = "BUY / LONG"
    else:
        stop_loss = resistance + (data_range * 0.5)
        take_profit = current_price - ((stop_loss - current_price) * 2.0)  # 1:2 Risk-Reward
        signal = "SELL / SHORT"

    return {
        "current_price": current_price,
        "high_wick": high_wick,
        "low_wick": low_wick,
        "support": support,
        "resistance": resistance,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "signal": signal,
        "ma_20": ma_20
    }

def fetch_financial_news():
    """Fetches top financial headlines via RSS news scraping."""
    url = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US"
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("item")[:5]
        news_list = []
        for item in items:
            title = item.title.text if item.title else "No Title"
            news_list.append(f"• {title}")
        return "\n".join(news_list) if news_list else "No news available at the moment."
    except Exception as e:
        return f"Could not fetch news headlines: {e}"

# --- BOT COMMAND HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ALERT_CHAT_ID
    ALERT_CHAT_ID = update.effective_chat.id

    welcome_text = (
        "🤖 *Welcome to Super Bot & Trading Hub!*\n\n"
        "Here are my available commands:\n"
        "• `/ai <question>` - Ask Gemini AI\n"
        "• `/wiki <topic>` - Search Wikipedia\n"
        "• `/trade <symbol>` - Real-time market analysis, wicks, SL & TP\n"
        "• `/news` - Scrape latest market headlines & institutional context\n"
        "• `/download <link>` - Download TikTok / Social videos\n\n"
        "⏰ *Automated USA Market Loops:* Active! Automated alerts send at 1:29 PM and 2:45 PM US Eastern Time."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ai_client:
        await update.message.reply_text("⚠️ GEMINI_API_KEY is missing on Render.")
        return

    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("Please provide a prompt! Example: `/ai Explain interest rate decisions`")
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
        await update.message.reply_text("Please specify a topic! Example: `/wiki Inflation`")
        return

    try:
        summary = wikipedia.summary(query, sentences=3)
        await update.message.reply_text(f"📖 *{query.title()}*\n\n{summary}", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("❌ Topic not found on Wikipedia.")

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📰 Fetching latest market headlines...")
    headlines = fetch_financial_news()
    await update.message.reply_text(f"🌐 *Latest Market News Headlines:*\n\n{headlines}", parse_mode="Markdown")

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide a link! Example: `/download https://www.tiktok.com/@user/video/123456`")
        return

    url = context.args[0]
    await update.message.reply_text("📥 Processing & downloading media...")

    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloaded_media.%(ext)s',
        'quiet': True,
        'max_filesize': 50 * 1024 * 1024  # 50MB max for Telegram
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        files = glob.glob("downloaded_media.*")
        if files:
            filepath = files[0]
            with open(filepath, 'rb') as video_file:
                await update.message.reply_video(video=video_file, caption="✅ Here is your downloaded video!")
            os.remove(filepath)
        else:
            await update.message.reply_text("❌ Download completed but file was not found.")
    except Exception as e:
        await update.message.reply_text(f"❌ Download failed: {e}")

async def trade_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please specify an asset ticker!\nExample: `/trade BTC-USD` or `/trade ^GSPC` or `/trade EURUSD=X`")
        return

    symbol = context.args[0].upper()
    await update.message.reply_text(f"📊 Analyzing market structure & levels for `{symbol}`...", parse_mode="Markdown")

    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1mo", interval="1d")

        if df.empty or len(df) < 14:
            await update.message.reply_text(f"❌ Could not retrieve data for `{symbol}`.")
            return

        rsi = compute_rsi(df)
        tech = analyze_candles_and_levels(df)
        news = fetch_financial_news()

        prompt = (
            f"Act as a professional market strategist and trader. Analyze symbol {symbol}:\n"
            f"- Current Price: ${tech['current_price']:.4f}\n"
            f"- Highest Wick (10d): ${tech['high_wick']:.4f}\n"
            f"- Lowest Wick (10d): ${tech['low_wick']:.4f}\n"
            f"- 20-Day SMA: ${tech['ma_20']:.4f}\n"
            f"- 14-Day RSI: {rsi:.2f}\n"
            f"- Algorithmic Signal: {tech['signal']}\n"
            f"- Calculated Stop Loss: ${tech['stop_loss']:.4f}\n"
            f"- Calculated Take Profit: ${tech['take_profit']:.4f}\n"
            f"- Recent Market News Headlines:\n{news}\n\n"
            f"Provide a clear decision summary:\n"
            f"1. **Market Bias & Big Player Activity** (Institutional Context based on news/wicks)\n"
            f"2. **Trade Setup & Action Plan** (Buy / Sell / Wait)\n"
            f"3. **Exact Level Guidance** (Entry Zone, Stop Loss, Take Profit Target, Risk-Reward)"
        )

        if ai_client:
            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            report = response.text
        else:
            report = (
                f"• Signal: *{tech['signal']}*\n"
                f"• Current Price: ${tech['current_price']:.4f}\n"
                f"• Highest Wick: ${tech['high_wick']:.4f}\n"
                f"• Lowest Wick: ${tech['low_wick']:.4f}\n"
                f"• Stop Loss: ${tech['stop_loss']:.4f}\n"
                f"• Take Profit: ${tech['take_profit']:.4f}\n"
            )

        await update.message.reply_text(f"📈 *Trade & Structure Analysis: `{symbol}`*\n\n{report}", parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Error during trade analysis: {e}")

# --- AUTOMATED USA TIME SCHEDULER LOOP ---
async def usa_time_loop(app):
    """Monitors US Eastern Time and triggers automated market scans at 13:29 EST and 14:45 EST."""
    est_tz = pytz.timezone('US/Eastern')
    triggered_today = set()

    while True:
        try:
            now_est = datetime.now(est_tz)
            time_str = now_est.strftime("%H:%M")
            date_str = now_est.strftime("%Y-%m-%d")

            # Check for 13:29 EST (1:29 PM) and 14:45 EST (2:45 PM)
            if time_str in ["13:29", "14:45"]:
                trigger_key = f"{date_str}_{time_str}"
                if trigger_key not in triggered_today and ALERT_CHAT_ID:
                    triggered_today.add(trigger_key)

                    msg = f"🔔 *Automated USA Market Loop Triggered ({time_str} EST)*\nChecking key assets for high/low wicks, adjustments, and news..."
                    await app.bot.send_message(chat_id=ALERT_CHAT_ID, text=msg, parse_mode="Markdown")

                    # Auto scan S&P 500, Bitcoin, Gold, and EUR/USD
for symbol in ["^GSPC", "BTC-USD", "GC=F", "EURUSD=X"]:

                       
                            df = yf.Ticker(symbol).history(period="1mo", interval="1d")
                            if not df.empty and len(df) >= 14:
                                tech = analyze_candles_and_levels(df)
                                alert = (
                                    f"📊 *Scheduled Alert: `{symbol}`*\n"
                                    f"• Signal: *{tech['signal']}*\n"
                                    f"• Current: ${tech['current_price']:.2f}\n"
                                    f"• High Wick: ${tech['high_wick']:.2f} | Low Wick: ${tech['low_wick']:.2f}\n"
                                    f"• Calculated SL: ${tech['stop_loss']:.2f}\n"
                                    f"• Calculated TP: ${tech['take_profit']:.2f}\n"
                                )
                                await app.bot.send_message(chat_id=ALERT_CHAT_ID, text=alert, parse_mode="Markdown")
                        except Exception as inner_e:
                            logging.error(f"Error scanning {symbol}: {inner_e}")

            # Reset triggers list past midnight EST
            if time_str == "00:01":
                triggered_today.clear()

        except Exception as e:
            logging.error(f"Error in USA loop: {e}")

        await asyncio.sleep(30)  # Check every 30 seconds

# --- MAIN ENGINE ---
async def main():
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
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CommandHandler("download", download_media))
    app.add_handler(CommandHandler("trade", trade_analysis))

    # Start automated background loop task
    asyncio.create_task(usa_time_loop(app))

    print("Smart Bot with All Modules is running...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    # Keep application running
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())















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

