import asyncio
import logging
import pandas as pd
import os
from datetime import datetime, timedelta

import google.genai as genai   # Yangi to'g'ri paket

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

# ================= GEMINI (Yangi usul) =================
client = genai.Client(api_key=GOOGLE_API_KEY)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# ================= TO‘LIQ SYSTEM PROMPT =================
SYSTEM_PROMPT = """
Siz Greenleaf Family korporatsiyasining rasmiy Aqlli Marketing Maslahatchi AI sisiz.
Marketing planini mukammal bilasiz va oddiy, aniq, ilhomlantiruvchi tarzda tushuntirasiz.

ASOSIY QOIDALAR:
- Javoblar qisqa va lo'nda bo'lsin, lekin kerak bo'lsa chuqurroq tushuntiring.
- Yangi hamkorlarni bosqichma-bosqich o'rgating.
- Har doim "biz bir jamoamiz" ruhida gapiring.

Greenleaf Marketing Planining asosiy qismlari:
- Paketlar: Platina (275 PV) eng mashhur paket.
- Referal bonusi: 5% (Platina va yuqorida)
- Komandniy (Binary) bonus (GB)
- Bonus s prodazh (SB) — status bo'yicha
- Voucher bonusi (2%)
- Liderskiy bonuslar va Direktorlar premiyalari (avtomobil, sayohat, kvartira)

4 Ustun va 10 Asosni ham yaxshi bilasiz.
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
    await message.answer(
        "🌟 GREENLEAF BIZNESNING 4 USTUNI\n\n"
        🏛 Tarmoqli marketingning 4 ta mustahkam ustuni
        Muvaffaqiyat tasodif emas, u — to‘g‘ri qurilgan arxitektura natijasidir. Agar biznesingiz o‘smayotgan bo‘lsa, demak, ushbu ustunlardan biri zaiflashgan.

        1️⃣-ustun: Uzluksizlik (Biznesdan bir kun ham chiqib ketmaslik)
        Bu tarmoqli marketingning "Oltin qoidasi".

        Mohiyati: Biznesingiz "SMS apparati" (aloqa vositasi) hech qachon o‘chmasligi kerak. Hatto dam olayotganingizda ham fikringiz biznesda bo‘lsin.

        Mashina effekti: Og‘ir mashinani itarayotganda to‘xtab qolsangiz, u nafaqat to‘xtaydi, balki orqaga qarab dumalaydi. Uni qayta joyidan jildirish uchun ikki barobar ko‘p kuch ketadi.

        Natija: 3 oy to‘xtovsiz ishlasangiz — farqni ko‘rasiz, 6 oy ishlasangiz — hayotingiz o‘zgaradi.

        2️⃣-ustun: Promoushn (Hurmat va e’tirof)
        Bu — hamkorlarga kuch berish san’ati.

        Mohiyati: Hurmat so‘zda va harakatda bo‘lishi, eng muhimi — chin yurakdan chiqishi shart.

        Maqsadi: Pastdagi hamkorlaringizga ishonch bag‘ishlash. Ular o‘z tashkilotini qura olishiga ishonishlari uchun ularni e’tirof etish (promoushn qilish) kerak.

        Qoida: Me’yorni biling, lekin asosiy maqsadni — insonni yetakchi sifatida ko‘tarishni unutmang.

        3️⃣-ustun: Ustozlik (Upline va Downline munosabatlari)
        Yolg‘iz harakat qilgan odam bu biznesda yutiladi.

        Mohiyati: Yuqori turuvchi yetakchi (ustoz) va shogird o‘rtasidagi doimiy maslahatlashuv.

        Maslahat qoidasi: Hech qachon mustaqil (ustozsiz) qaror qabul qilmang. Muvaffaqiyatli yetakchilardan nusxa ko‘chiring (modellashtirish).
    
        Yetakchi vazifasi: Shogirdlaringizga rahbar emas, yordamchi bo‘ling. Ularni e’tibordan chetda qoldirmang.

        4️⃣-ustun: Munosabatlar konsepsiyasi
        Bu — tizimning eng muhim va poydevor qismi.

        Mohiyati: Tarmoqli marketing — bu odamlar o‘rtasidagi munosabatlar biznesidir.

        Uzoq muddatli reja: Agar siz 25 yil davomida ishlaydigan va farzandlaringizga passiv daromad qoldiradigan tashkilot qurmoqchi bo‘lsangiz, uni munosabatlar ustiga quring.

        Barqarorlik: Faqat kuchli insoniy aloqalargina inqiroz vaqtida jamoani saqlab qola oladi.

        🎯 Xulosa:
        Ushbu to‘rtta ustunni o‘z ish uslubingizga tatbiq qilsangiz, siz shunchaki sotuvchi emas, balki global tarmoq mutaxassisiga aylanasiz.
      
    )

@dp.message(Command("marketingplan"))
async def cmd_marketingplan(message: types.Message):
    await message.answer(
        "📊 Greenleaf Marketing Planining asosiy qismlari:\n\n"
        "• **Platina paketi (275 PV)** — eng mashhur boshlang‘ich paket\n"
        "• **Referal bonusi** — 5%\n"
        "• **Binary (Komandniy) bonus** — chap va o‘ng guruh orqali\n"
        "• **Bonus s prodazh (SB)** — status bo‘yicha\n"
        "• Liderskiy bonuslar va Direktorlar mukofotlari\n\n"
        "Qaysi bonus yoki qism haqida **batafsil** ma’lumot kerak?"
    )

# Boshqa buyruqlar (qoshilish, taklif) oldingi kodda qolgan holatda qoldiring

# ================= ASOSIY JAVOB (Yangi google.genai) =================
@dp.message()
async def handle_text(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")
    load_catalog()

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{SYSTEM_PROMPT}\n\nKatalog:\n{catalog_data}\n\nFoydalanuvchi savoli: {message.text}"
        )

        await message.reply(response.text)

    except Exception as e:
        logging.error(f"Xato: {e}")
        if "429" in str(e) or "quota" in str(e).lower():
            await message.answer("⏳ API limiti tugadi. 1-2 daqiqa kuting.")
        else:
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
