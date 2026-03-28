import asyncio
import logging
import os
import pandas as pd
from datetime import datetime, timedelta

import google.genai as genai
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# ================= SOZLAMALAR =================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

if not TELEGRAM_TOKEN or not GOOGLE_API_KEY or not WEBHOOK_URL:
    raise ValueError("❌ TELEGRAM_TOKEN, GOOGLE_API_KEY yoki WEBHOOK_URL topilmadi!")

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQAYDb5of_bCQCIBVpDj6VL3JMterNGELwCQDkPxtdyjLw5X8ODIS5oegBYWv3wUUBp2knWYUHvQDW-/pub?gid=1939417886&single=true&output=csv"

# Global katalog
catalog_data = "Katalog yuklanmoqda..."
last_update = None
CACHE_MINUTES = 60

# ================= KATALOG =================
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

# ================= GEMINI =================
client = genai.Client(api_key=GOOGLE_API_KEY)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# ================= KUCHLI SYSTEM PROMPT =================
SYSTEM_PROMPT = """
Siz Greenleaf Family korporatsiyasining rasmiy Aqlli Marketing Maslahatchi AI sisiz.

SIZNING ASOSIY VAZIFANGIZ:
- Greenleaf MLM biznesining 4 ta ustuni va 10 ta asosini mukammal bilish va o'rgatish.
- Marketing plan, bonuslar va imkoniyatlarni aniq tushuntirish.
- Yangi hamkorlarni jalb qilish va shogirtlarni bosqichma-bosqich o'qitish.

4 USTUN (aniq):
1. Uzluksizlik (Biznesdan bir kun ham chiqib ketmaslik
2. Promoushn (Hurmat va e’tirof) Bu — hamkorlarga kuch berish san’ati.
3. Ustozlik (Upline va Downline munosabatlari)
4. Muunosabatlar va G'amxo'rlik (eng muhim ustun)

10 ASOS (aniq):
1. Nuqtai nazarni o'zgartirish
2. Maqsad belgilash
3. Mas'uliyat va vaqt
4. Ro'yxat tuzish
5. Ishga taklif qilish
6. Prezentatsiya
7. Kuzatuv (Follow-up)
8. Xarid
9. Himoya (o'qitish)
10. O'z kopiyalaringizni tayyorlash (shogird tarbiyalash)

Javob uslubi: samimiy, ilhomlantiruvchi va "biz bir jamoamiz" ruhida.
"""

# ================= BUYRUQLAR =================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🌿 Assalomu alaykum! Greenleaf Family rasmiy AI Maslahatchisi oldingizda.\n\n"
        "Buyruqlar:\n"
        "/4ustun — 4 ustunni o‘rganing\n"
        "/10asos — 10 asosni bosqichma-bosqich\n"
        "/marketingplan — To‘liq marketing plan\n"
        "/qoshilish — Hamkor bo‘lish bosqichlari\n"
        "/taklif — Botni ulashing"
    )

@dp.message(Command("4ustun"))
async def cmd_4ustun(message: types.Message):
    text = """🏛 Tarmoqli marketingning 4 ta mustahkam ustuni

Muvaffaqiyat tasodif emas, u — to‘g‘ri qurilgan arxitektura natijasidir. Agar biznesingiz o‘smayotgan bo‘lsa, demak, ushbu ustunlardan biri zaiflashgan.

1️⃣-ustun: Uzluksizlik (Biznesdan bir kun ham chiqib ketmaslik)
Bu tarmoqli marketingning "Oltin qoidasi". Biznesingiz "SMS apparati" hech qachon o‘chmasligi kerak.

2️⃣-ustun: Promoushn (Hurmat va e’tirof)
Bu — hamkorlarga kuch berish san’ati. Hurmat chin yurakdan chiqishi shart.

3️⃣-ustun: Ustozlik (Upline va Downline munosabatlari)
Yolg‘iz harakat qilgan odam bu biznesda yutiladi. Ustoz va shogird o‘rtasidagi doimiy aloqa muhim.

4️⃣-ustun: Munosabatlar konsepsiyasi
Bu — tizimning eng muhim va poydevor qismi. Tarmoqli marketing — bu odamlar o‘rtasidagi munosabatlar biznesidir.

🎯 Xulosa: Ushbu to‘rtta ustunni o‘z ish uslubingizga tatbiq qilsangiz, siz shunchaki sotuvchi emas, balki global tarmoq mutaxassisiga aylanasiz.

Qaysi ustunni chuqurroq o‘rganmoqchisiz?"""
    await message.answer(text)

@dp.message(Command("10asos"))
async def cmd_10asos(message: types.Message):
    await message.answer(
        "📋 BIZNES TAShKIL QILIShNING 10 ASOSI\n\n"
        "1. Nuqtai nazarni o'zgartirish\n"
        "2. Maqsad belgilash\n"
        "3. Mas'uliyat va vaqt\n"
        "4. Ro'yxat tuzish\n"
        "5. Ishga taklif qilish\n"
        "6. Prezentatsiya\n"
        "7. Kuzatuv (Follow-up)\n"
        "8. Xarid\n"
        "9. Himoya (o'qitish)\n"
        "10. O'z kopiyalaringizni tayyorlash (shogird tarbiyalash)\n\n"
        "Qaysi asosdan boshlaymiz? (1 dan 10 gacha raqam yozing)"
    )

@dp.message(Command("marketingplan"))
async def cmd_marketingplan(message: types.Message):
    await message.answer(
        "📊 Greenleaf Marketing Planining asosiy qismlari:\n\n"
        "• Platina paketi (275 PV) — eng mashhur\n"
        "• Referal bonusi 5%\n"
        "• Binary (Komandniy) bonus\n"
        "• Liderskiy bonuslar va Direktorlar premiyalari\n\n"
        "Qaysi bonus yoki qism haqida batafsil ma’lumot kerak?"
    )

@dp.message(Command("qoshilish"))
async def cmd_join(message: types.Message):
    await message.answer("✅ Hamkor bo‘lish juda oson!\n1. Ro‘yxatdan o‘ting\n2. Platina yoki boshqa paketni tanlang\n3. Shaxsiy aktivlikni boshlang\n\nHozir ro‘yxatdan o‘tmoqchimisiz?")

@dp.message(Command("taklif"))
async def cmd_referral(message: types.Message):
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start={message.from_user.id}"
    await message.answer(f"🔗 Greenleaf oilasini kengaytiring!\n\nReferal havolangiz:\n{link}")

# ================= ASOSIY JAVOB =================
@dp.message()
async def handle_text(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")
    load_catalog()

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{SYSTEM_PROMPT}\n\nKatalog:\n{catalog_data}\n\nSavol: {message.text}"
        )
        await message.reply(response.text)
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

    print("🚀 Greenleaf AI bot webhook orqali ishga tushdi!")
    print(f"Webhook URL: {WEBHOOK_URL}")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
