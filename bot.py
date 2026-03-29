import os
import asyncio
import requests
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import smtplib
from email.mime.text import MIMEText

# ================== ENV VARIABLES ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
EMAIL = os.getenv("EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

# ================== KEEP ALIVE (FOR RENDER) ==================
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "Bot is alive"

def run():
    app_flask.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ================== EMAIL FUNCTION ==================
def send_email(subject, message):
    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = EMAIL
        msg["To"] = TO_EMAIL

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()

        print("✅ Email sent")
    except Exception as e:
        print("❌ Email error:", e)

# ================== TELEGRAM COMMANDS ==================
users = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users.add(update.effective_chat.id)
    await update.message.reply_text("✅ You will receive restock alerts!")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📌 Feature coming soon")

# ================== STOCK CHECK LOOP ==================
URL = "https://www.firstcry.com/hotwheels/5/0/113?sort=popularity"

async def loop(app):
    while True:
        try:
            response = requests.get(URL)
            soup = BeautifulSoup(response.text, "html.parser")

            if "Out of stock" not in soup.text:
                msg = "🔥 Hot Wheels back in stock!"

                # Telegram alert
                for user in users:
                    await app.bot.send_message(chat_id=user, text=msg)

                # Email alert
                send_email("Hot Wheels Restock", msg)

                print("✅ Alert sent")

            else:
                print("⏳ Still out of stock")

        except Exception as e:
            print("❌ Error:", e)

        await asyncio.sleep(120)

# ================== MAIN ==================
async def main():
    keep_alive()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))

    asyncio.create_task(loop(app))

    await app.run_polling()

# ================== RUN ==================
if __name__ == "__main__":
    asyncio.run(main())