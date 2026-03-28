import asyncio
import logging
import pandas as pd
import google.generativeai as genai
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# ================= SOZLAMALAR =================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

if not TELEGRAM_TOKEN or not GOOGLE_API_KEY:
    raise ValueError("❌ TELEGRAM_TOKEN yoki GOOGLE_API_KEY topilmadi! Render.com da Environment Variables ni tekshiring.")

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
genai.configure(api_key=GOOGLE_API_KEY)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# ================= SYSTEM PROMPT =================
SYSTEM_PROMPT = """
Siz Greenleaf Family korporatsiyasining rasmiy Aqlli Marketing Maslahatchi AI sisiz.
Siz marketing planini mukammal bilasiz va uni oddiy, aniq va ilhomlantiruvchi tarzda tushuntirasiz.

ASOSIY QOIDALAR:
- Har doim rasmiy marketing planga asoslanib javob bering.
- Javoblar qisqa, lo'nda va amaliy bo'lsin.
- Yangi hamkorlarga bosqichma-bosqich o'rgating.
- Maqsad: odamlarni biznesga jalb qilish va ularni muvaffaqiyatli shogird qilish.

Greenleaf Marketing Planining asosiy elementlari:
1. Paketlar: Bronza (55 PV), Serebro (110 PV), Zoloto (165 PV), Platina (275 PV), Brilliant (825 PV), Korona (1650 PV).
2. Referal bonusi — Platina va yuqorida 5%.
3. Komandniy bonus (GB) — binary tizim.
4. Bonus s prodazh (SB), Voucher bonusi, Liderskiy bonuslar va boshqalar.

4 Ustun va 10 Asosni ham mukammal bilasiz.

Javob uslubi: samimiy, ilhomlantiruvchi, "biz bir jamoamiz" ruhida gapiring.
"""

# ================= BUYRUQLAR =================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🌿 Assalomu alaykum! Greenleaf Family rasmiy AI Maslahatchisi oldingizda.\n\n"
        "Mahsulotlar, marketing plan, bonuslar, 4 ustun va 10 asos haqida savollaringiz bo‘lsa — yozing!\n\n"
        "Buyruqlar:\n"
        "/4ustun — 4 ustunni o‘rganing\n"
        "/10asos — 10 asosni bosqichma-bosqich\n"
        "/marketingplan — To‘liq marketing plan\n"
        "/qoshilish — Hamkor bo‘lish bosqichlari\n"
        "/taklif — Botni ulashing"
    )

@dp.message(Command("4ustun"))
async def cmd_4ustun(message: types.Message):
    await message.answer("🌟 GREENLEAF BIZNESNING 4 USTUNI\n\n1. Mahsulot sifati\n2. Marketing plani\n3. O‘qitish\n4. Muunosabatlar va G‘amxo‘rlik (eng muhimi)\n\nQaysi ustunni chuqurroq bilmoqchisiz?")

@dp.message(Command("marketingplan"))
async def cmd_marketingplan(message: types.Message):
    await message.answer("📊 Greenleaf Marketing Plan:\n\n• Platina paketi (275 PV) — eng mashhur\n• Referal bonusi 5%\n• Binary (Komandniy) bonus\n• Liderskiy bonuslar\n\nQaysi bonus haqida batafsil ma’lumot kerak?")

@dp.message(Command("qoshilish"))
async def cmd_join(message: types.Message):
    await message.answer("✅ Hamkor bo‘lish uchun:\n1. Ro‘yxatdan o‘ting\n2. Platina yoki boshqa paketni tanlang\n3. Shaxsiy aktivlikni boshlang\n\nHozir ro‘yxatdan o‘tmoqchimisiz?")

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
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction=SYSTEM_PROMPT
        )

        full_prompt = f"Katalog:\n{catalog_data}\n\nFoydalanuvchi savoli: {message.text}"

        response = model.generate_content(
            full_prompt,
            generation_config={"temperature": 0.7, "max_output_tokens": 800}
        )

        await message.reply(response.text)

    except Exception as e:
        error_str = str(e).lower()
        if "429" in error_str or "quota" in error_str:
            await message.answer("⏳ API limiti tugadi. 1-2 daqiqa kuting.")
        else:
            logging.error(f"Xato: {e}")
            await message.answer("Texnik xatolik yuz berdi. Birozdan keyin qayta sinab ko‘ring.")

# ================= ISHGA TUSHIRISH =================
async def main():
    print("🚀 Greenleaf AI Maslahatchi boti ishga tushmoqda...")
    load_catalog(force=True)
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())