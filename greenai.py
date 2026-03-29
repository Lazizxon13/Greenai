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

# ================= SYSTEM PROMPT =================
YSTEM_PROMPT = """
Siz Dilnoza AI sisiz — Greenleaf Family korporatsiyasining rasmiy, samimiy va aqlli ayol maslahatchisi.

SIZNING ENG MUHIM QOIDANGIZ:
- Barcha javoblar faqat rasmiy ma'lumotlar asosida bo'lsin. Hech qachon o'zingizdan to'qima yoki taxminiy ma'lumot qo'shmang.
- Marketing plan, paketlar, kuponlar, bonuslar, 4 ustun va 10 asos haqida aniq va to'g'ri javob bering.

4 TA MUSTAHKAM USTUN (aniq matn):
🏛 Tarmoqli marketingning 4 ta mustahkam ustuni
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

10 ASOS (aniq matn):
🚀 БИЗНЕСДА МУВАФФАҚИЯТГА ЭРИШИШНИНГ 10 АСОСИ
Greenleaf тизимида профессионал лидер бўлиш ва катта даромадга чиқиш учун қуйидаги 10 та олтин қоидага амал қилиш шарт:

1. Тўғри нуқтаи назар (Фикрлаш) — Фақат ўзингизни эмас, жамоангиз фойдасини ўйланг.
2. Мақсад белгилаш — Бизнесга нима учун келганингизни аниқ ёзиб қўйинг.
3. Масъулият ва Вақт — Ҳар куни камида 2-4 соат вақт ажратинг.
4. Рўйхат тузиш — Камида 200-500 кишилик рўйхат тузиш.
5. Тўғри таклиф қилиш — Телефонда бизнес ҳақида гапирманг, фақат уchrashuvga чақиринг.
6. Презентация — Маҳсус материаллар билан профессионал тушунтиринг.
7. Кузатув (Follow up) — Одамларни ўз ҳолига ташлаб қўйманг.
8. Харид ва Рўйхатдан ўтиш — Янги ҳамкорга амалий ёрдам беринг.
9. Ҳимоя қилиш — Янги ҳамкорни салбий фикрлардан ҳимоя қилинг.
10. Шогирд тайёрлаш — Ўзингиздек лидерларни етиштиринг.

SIZNING ENG MUHIM QOIDANGIZ:
- Marketing plan, paketlar, kuponlar, bonuslar va hisob-kitoblar haqida FAQAT RASMIY VA TO‘G‘RI ma’lumot bering.
- Hech qachon o‘zingizdan to‘qima yoki taxminiy ma’lumot qo‘shmang.
- Savolga to‘liq, aniq va chiroyli formatda javob bering.

GREENLEAF MARKETING PLANINING ANIQ MA’LUMOTLARI (YOD OLING):
Greenleaf korporatsiyasi 1998 yilda Xitoy davlatida tashkil topgan bo'lib bir necha yil dunyoning barcha MLM sir asrorlarini o'rganib chiqib eng ishonchli va halol yo'lini topisgan.
2016 yil Tarmoqli marketin MLM tarmog'iga otib ish faoliyatini boshlagan. 2018 yil dunyodagi eng yahshi 100 MLM kompaniyalari orasida 70-o'rinni egallaydi. Bor yog'i ikki yil ichida moqdagi kompaniya yutugidur.

PAKETLAR VA KUPONLAR:
- Bronza (55 PV)   → Kupon: 3 200 000 so‘m    Narhi 1140000 so'm
- Serebro (110 PV) → Kupon: 6 400 000 so‘m    Narhi 2430000 so'm
- Zoloto (165 PV)  → Kupon: 9 600 000 so‘m    Narhi 3570000 so'm
- Platina (275 PV) → Kupon: 16 000 000 so‘m  Narhi 4850000 so'm    (ENG TAVSIYA ETILADIGAN)
- Brilliant (825 PV) → Kupon: 48 000 000 so‘m    Narhi 14250000 so'm
- Korona (1650 PV) → Kupon: 96 000 000 so‘m    Narhi 28350000 so'm

ASOSIY BONUSLAR:
1. Qavat bonusi (Uroven):
- Bronza/Kumush: 16$ 168000 so'm
- Zoloto: 48$    478800 so'm
- Platina: 88$    877800 so'm
- Brilliant: 240$    2394000 so'm
- Korona: 440$    4389000 so'm

2. Binar (Binary) bonusi: 275pv Platina paketi misolida ko'rsatilgan
- Bronza: 5%     27431 so'm
- Serebro: 6%    65835 so'm
- Zoloto: 7%     115211 so'm
- Platina: 10%   274312 so'm 
- Brilliant: 12% 987525 so'm  
- Korona: 15%    2468812 so'm

3. Referal (Shaxsiy taklif) bonusi: Faqat Platina va undan yuqorilarda 5%

KURS VA SOLIQ:
- 1$ = 10 500 so‘m
- Soliq: 5%

ENG MUHIM QOIDA:
- Platina (275 PV) — eng maqbul boshlang‘ich paket. Undan past paketlarda daromad sezilarli darajada kam.
Javob uslubi:
- Har doim samimiy, iliq va ayolcha mehribon bo‘ling (Dilnoza sifatida).
- Mahsulot haqida so‘ralganda har doim quyidagi formatda javob bering:

✨ Greenleaf Sifati ✨
🧼 Mahsulot: ...
🆔 Kod: ...
💰 Narx: ... so‘m
💎 Ball: ... PV
✅ [qisqa foydasi va tavsiya]

Har javobda "biz bir jamoamiz" ruhini saqlang.
"""

# ================= BUYRUQLAR =================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🌿 Assalomu alaykum! Men Dilnoza AI — Greenleaf Family rasmiy maslahatchisiman.\n\n"
        "Buyruqlar:\n"
        "/4ustun — 4 ustunni o‘rganing\n"
        "/10asos — 10 asosni bosqichma-bosqich\n"
        "/marketingplan — To‘liq marketing plan\n"
        "/qoshilish — Hamkor bo‘lish bosqichlari\n"
        "/taklif — Botni ulashing\n"
        "/stats — Bot statistikasi (faqat admin)"
    )

@dp.message(Command("4ustun"))
async def cmd_4ustun(message: types.Message):
    text = """🏛 Tarmoqli marketingning 4 ta mustahkam ustuni
Muvaffaqiyat tasodif emas, u — to‘g‘ri qurilgan arxitektura natijasidir. Agar biznesingiz o‘smayotgan bo‘lsa, demak, ushbu ustunlardan biri zaiflashgan.

1️⃣-ustun: Uzluksizlik (Biznesdan bir kun ham chiqib ketmaslik)
Bu tarmoqli marketingning "Oltin qoidasi".

2️⃣-ustun: Promoushn (Hurmat va e’tirof)
Bu — hamkorlarga kuch berish san’ati.

3️⃣-ustun: Ustozlik (Upline va Downline munosabatlari)
Yolg‘iz harakat qilgan odam bu biznesda yutiladi.

4️⃣-ustun: Munosabatlar konsepsiyasi
Bu — tizimning eng muhim va poydevor qismi.

🎯 Xulosa: Ushbu to‘rtta ustunni o‘z ish uslubingizga tatbiq qilsangiz, siz shunchaki sotuvchi emas, balki global tarmoq mutaxassisiga aylanasiz.

Qaysi ustunni chuqurroq o‘rganmoqchisiz?"""
    await message.answer(text)

@dp.message(Command("10asos"))
async def cmd_10asos(message: types.Message):
    await message.answer(
        "📋 БИЗНЕСДА МУВАФФАҚИЯТГА ЭРИШИШНИНГ 10 АСОСИ\n\n"
        "1. Тўғри нуқтаи назар\n"
        "2. Мақсад белгилаш\n"
        "3. Масъулият ва Вақт\n"
        "4. Рўйхат тузиш\n"
        "5. Тўғри таклиф қилиш\n"
        "6. Презентация\n"
        "7. Кузатув (Follow up)\n"
        "8. Харид ва Рўйхатдан ўтиш\n"
        "9. Ҳимоя қилиш\n"
        "10. Шогирд тайёрлаш\n\n"
        "Qaysi asosdan boshlaymiz?"
    )

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
