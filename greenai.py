import asyncio
import logging
import os
import json
import pandas as pd
from datetime import datetime, timedelta

from openai import AsyncOpenAI
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# ================= SOZLAMALAR =================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY or not WEBHOOK_URL:
    raise ValueError("❌ TELEGRAM_TOKEN, OPENAI_API_KEY yoki WEBHOOK_URL topilmadi!")

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQAYDb5of_bCQCIBVpDj6VL3JMterNGELwCQDkPxtdyjLw5X8ODIS5oegBYWv3wUUBp2knWYUHvQDW-/pub?gid=1939417886&single=true&output=csv"

# ================= KATALOG =================
catalog_data = "Katalog yuklanmoqda..."
last_update = None
CACHE_MINUTES = 60

def load_catalog(force=False):
    global catalog_data, last_update
    if not force and last_update and (datetime.now() - last_update) < timedelta(minutes=CACHE_MINUTES):
        return
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        catalog_data = df.to_string(index=False, max_rows=150)
        last_update = datetime.now()
        print(f"✅ Katalog yangilandi: {len(df)} ta mahsulot")
    except Exception as e:
        print(f"❌ Katalog xatosi: {e}")
        catalog_data = "XATO: Katalog yuklanmadi."

# ================= STATISTIKA =================
STATS_FILE = "bot_users.json"

if not os.path.exists(STATS_FILE):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump({"total_users": 0, "users": []}, f, ensure_ascii=False)

def load_stats():
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_stats(data):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

stats = load_stats()

# ================= OPENAI =================
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# ================= TO‘LIQ SYSTEM PROMPT =================
SYSTEM_PROMPT = """
Siz Dilnoza AI sisiz — Greenleaf Family korporatsiyasining rasmiy, samimiy va aqlli ayol maslahatchisi.

4 TA MUSTAHKAM USTUN VA 10 ASOSNI MUKAMMAL BILING.
Marketing plan, paketlar, kuponlar va bonuslar haqida faqat rasmiy ma'lumot bering.

Javob uslubi: iliq, mehribon, "biz bir jamoamiz" ruhida.
Mahsulot haqida so'ralganda har doim quyidagi formatda javob bering:
✨ Greenleaf Sifati ✨
🧼 Mahsulot: ...
🆔 Kod: ...
💰 Narx: ... so'm
💎 Ball: ... PV
✅ [qisqa foydasi va tavsiya]
"""

# ================= BUYRUQLAR =================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("🌿 Assalomu alaykum! Men Dilnoza AI — Greenleaf Family rasmiy maslahatchisiman.")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if message.from_user.id != 601900410:   # ← BU YERGA O‘ZINGIZNING TELEGRAM ID INGIZNI YOZING!
        await message.answer("Bu buyruq faqat admin uchun!")
        return
    total = stats["total_users"]
    await message.answer(f"📊 Bot statistikasi\n\n👥 Botga a'zo bo‘lganlar: **{total} ta**")

# ================= ASOSIY JAVOB =================
@dp.message()
async def handle_text(message: types.Message):
    # ================= YANGI FOYDALANUVCHINI HISOBLASH =================
    user_id = message.from_user.id
    if user_id not in stats["users"]:
        stats["users"].append(user_id)
        stats["total_users"] = len(stats["users"])
        save_stats(stats)
        print(f"✅ Yangi foydalanuvchi: {user_id} | Jami: {stats['total_users']}")

    await bot.send_chat_action(message.chat.id, "typing")
    load_catalog()

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Katalog:\n{catalog_data}\n\nSavol: {message.text}"}
            ],
            temperature=0.7,
            max_tokens=900
        )
        await message.reply(response.choices[0].message.content)
    except Exception as e:
        logging.error(f"Xato: {e}")
        await message.answer("Texnik xatolik. Birozdan keyin qayta sinab ko‘ring.")

# ================= WEBHOOK =================
async def main():
    load_catalog(force=True)
    await bot.set_webhook(WEBHOOK_URL)

    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, "/")
    setup_application(app, dp, bot=bot)

    print("🚀 Greenleaf AI bot (Dilnoza) ishga tushdi!")
    print(f"Webhook URL: {WEBHOOK_URL}")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
