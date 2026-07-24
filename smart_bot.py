import os
import logging
import asyncio
from datetime import datetime
import pytz
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import requests
import pandas as pd

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# --- CONFIGURATION ---
TOKEN = "8819821570:AAHWqwkMVMUOWEWwOaL-DcrSveEVvZphSY4"
ALLOWED_USER_IDS = [6124380017]
TRADING_SYMBOL = "BTCUSDT"

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

# --- LIVE MARKET DATA & WICK ANALYSIS MODULE ---
def fetch_and_analyze_market():
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={TRADING_SYMBOL}&interval=15m&limit=20"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if not isinstance(data, list) or len(data) == 0:
            return f"⚠️ Received empty data from exchange for {TRADING_SYMBOL}."
            
        columns = [
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'num_trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ]
        df = pd.DataFrame(data, columns=columns)
        
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['open'] = df['open'].astype(float)
        df['close'] = df['close'].astype(float)
        
        highest_wick = df['high'].max()
        lowest_wick = df['low'].min()
        current_price = df['close'].iloc[-1]
        
        analysis_text = (
            f"📈 **Market Analysis ({TRADING_SYMBOL})**\n"
            f"• Current Price: `{current_price}`\n"
            f"• Highest Wick: `{highest_wick}`\n"
            f"• Lowest Wick: `{lowest_wick}`\n"
            f"Status: Key institutional bounds mapped successfully via Pandas."
        )
        return analysis_text
    except Exception as e:
        logger.error(f"Data fetch error: {e}")
        return f"⚠️ Error fetching live data for {TRADING_SYMBOL}: {e}"

# --- MARKET WICK SCANNER LOOP ---
async def market_wick_scanner(application):
    eastern_tz = pytz.timezone('America/New_York')
    while True:
        try:
            now_eastern = datetime.now(eastern_tz)
            current_hour = now_eastern.hour
            current_minute = now_eastern.minute
            
            if current_hour == 12 and current_minute == 45:
                market_report = fetch_and_analyze_market()
                for admin_id in ALLOWED_USER_IDS:
                    try:
                        await application.bot.send_message(chat_id=admin_id, text=f"📊 **12:45 PM USA Scan:**\n{market_report}")
                    except Exception as e:
                        logger.error(f"Failed alert: {e}")
                await asyncio.sleep(70)

            elif current_hour == 13 and current_minute == 29:
                market_report = fetch_and_analyze_market()
                for admin_id in ALLOWED_USER_IDS:
                    try:
                        await application.bot.send_message(chat_id=admin_id, text=f"📊 **1:29 PM USA Adjustment:**\n{market_report}")
                    except Exception as e:
                        logger.error(f"Failed alert: {e}")
                await asyncio.sleep(70)
        except Exception as err:
            logger.error(f"Loop error: {err}")
        await asyncio.sleep(30)

async def post_init(application):
    asyncio.create_task(market_wick_scanner(application))

# --- TELEGRAM HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    await update.message.reply_text(
        "🤖 **Smart Bot Online & Analytics Ready!**\n\n"
        "✅ Web server health check active\n"
        "✅ USA Market Wick Scanner active\n"
        "✅ Live Pandas data processor online\n\n"
        "Use `/scan` to check live market wicks."
    )

async def manual_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    await update.message.reply_text("🔄 Pulling live market analysis...")
    report = fetch_and_analyze_market()
    await update.message.reply_text(report)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    await update.message.reply_text("💡 I am your automated quantitative trading assistant. Use `/scan` to view current Binance market metrics.")

# --- MAIN ---
def main():
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()

    application = (
        ApplicationBuilder()
        .token(TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("scan", manual_scan))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()

