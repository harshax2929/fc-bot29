import asyncio
import json
import os
import requests
import smtplib
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask
from threading import Thread

import os

# ================= ENV VARIABLES =================

BOT_TOKEN = os.getenv("8616624568:AAHaQVvj6yCeHbR249I5bFf9NP6HPfwGnxU")
EMAIL = os.getenv("topnotchbollywood@gmail.com")
APP_PASSWORD = os.getenv("mrec rzgy ofhw vivb")
TO_EMAIL = os.getenv("topnotchbollywood@gmail.com")

# ================= SAFETY CHECK =================

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing in environment variables")

if not EMAIL:
    raise ValueError("❌ EMAIL is missing in environment variables")

if not APP_PASSWORD:
    raise ValueError("❌ APP_PASSWORD is missing in environment variables")

if not TO_EMAIL:
    raise ValueError("❌ TO_EMAIL is missing in environment variables")

URL = "https://www.firstcry.com/hotwheels/5/0/113?sort=popularity"

USERS_FILE = "users.json"
STOCK_FILE = "stock.json"
WATCHLIST_FILE = "watchlist.json"

# KEEP ALIVE (for Render)
app_flask = Flask('')
@app_flask.route('/')
def home():
    return "Running"

def run():
    app_flask.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

# FILE HANDLING
def load_data(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return set(json.load(f))
    return set()

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(list(data), f)

users = load_data(USERS_FILE)
previous_stock = load_data(STOCK_FILE)
watchlist = load_data(WATCHLIST_FILE)
seen_watchlist = set()

# EMAIL FUNCTION
def send_email(message):
    try:
        msg = MIMEText(message)
        msg["Subject"] = "🔥 HotWheels Restock"
        msg["From"] = EMAIL
        msg["To"] = TO_EMAIL

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("Email error:", e)

# COMMANDS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users.add(update.effective_chat.id)
    save_data(USERS_FILE, users)
    await update.message.reply_text("✅ You will receive restock alerts!")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = context.args[0]
        watchlist.add(url)
        save_data(WATCHLIST_FILE, watchlist)
        await update.message.reply_text("✅ Added to watchlist")
    except:
        await update.message.reply_text("Usage: /add <url>")

# SEARCH
def fetch_stock():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(URL, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
    except:
        return set()

    products = soup.select("div.l1")
    stock = set()

    for p in products:
        name = p.select_one(".product-title")
        sold = p.select_one(".sold-out")

        if name and not sold:
            stock.add(name.get_text(strip=True))

    return stock

# WATCHLIST
def check_product(url):
    try:
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        return soup.select_one(".sold-out") is None
    except:
        return False

# LOOP
async def loop(app):
    global previous_stock

    while True:
        # ALL PRODUCTS
        current = fetch_stock()
        new_items = current - previous_stock

        for item in new_items:
            msg = f"🔥 Restocked: {item}"
            for user in users:
                await app.bot.send_message(user, msg)
            send_email("Hot Wheels Restock", msg)

        previous_stock = current
        save_data(STOCK_FILE, previous_stock)

        # WATCHLIST
        for url in watchlist:
            if url not in seen_watchlist and check_product(url):
                seen_watchlist.add(url)
                msg = f"🎯 Watchlist Restock:\n{url}"
                for user in users:
                    await app.bot.send_message(user, msg)
                send_email("Watchlist Restock", msg)

        await asyncio.sleep(120)
send_email("🔥 Gmail test successful")
# MAIN
keep_alive()

async def on_startup(app):
    asyncio.create_task(loop(app))

app = ApplicationBuilder().token("8616624568:AAHaQVvj6yCeHbR249I5bFf9NP6HPfwGnxU").post_init(on_startup).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", add))

app.run_polling()