import asyncio
import logging
import os
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

# ================= OPENAI =================
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

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
1. Uzluksizlik (Biznesdan bir kun ham chiqib ketmaslik)
2. Promoushn (Hurmat va e’tirof) — hamkorlarga kuch berish san’ati.
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

MAHSULOT HAQIDA JAVOB BERISH QOIDASI:
Foydalanuvchi mahsulot haqida so'raganda har doim quyidagi chiroyli formatda javob bering:

✨ Greenleaf Sifati ✨
🧼 Mahsulot: [to'liq nomi va qisqa tavsifi]
🆔 Kod: [kod]
💰 Narx: [narx] so'm
💎 Ball: [ball] PV
✅ [qisqa foydasi va tavsiya]

Javob uslubi: samimiy, ilhomlantiruvchi va "biz bir jamoamiz" ruhida bo'lsin.
Hech qachon quruq va rasmiy bo'lmang.
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
    await message.answer(
        "🌟 GREENLEAF BIZNESNING 4 USTUNI\n\n"
        "1. Mahsulot sifati va talabi\n"
        "2. Marketing plani (daromad tizimi)\n"
        "3. O‘qitish va rivojlanish\n"
        "4. **Muunosabatlar va G‘amxo‘rlik** — eng kuchli ustun!\n\n"
        "Qaysi ustunni chuqurroq bilmoqchisiz?"
    )

# ================= ASOSIY JAVOB (OpenAI) =================
@dp.message()
async def handle_text(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")
    load_catalog()

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Katalog:\n{catalog_data}\n\nFoydalanuvchi savoli: {message.text}"}
            ],
            temperature=0.7,
            max_tokens=800
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

    print("🚀 Greenleaf AI bot OpenAI bilan webhook orqali ishga tushdi!")
    print(f"Webhook URL: {WEBHOOK_URL}")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
