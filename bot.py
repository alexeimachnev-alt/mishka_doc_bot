import os
import asyncio
from aiohttp import web, ClientSession
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, BufferedInputFile

from generator import generate_certificate

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

if not BOT_TOKEN:
    print("ВНИМАНИЕ: BOT_TOKEN не задан! Добавьте его в .env или в Environment Variables на Render.")

bot = Bot(token=BOT_TOKEN or "dummy_token")
dp = Dispatcher()

class CertForm(StatesGroup):
    number = State()
    company = State()
    inn = State()
    date = State()

@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 **Генератор сертификатов дилера**\n\n"
        "Шаг 1 из 4: Введите **номер сертификата** (например: `2708/25`):"
    )
    await state.set_state(CertForm.number)

@dp.message(CertForm.number)
async def process_num(message: Message, state: FSMContext):
    await state.update_data(number=message.text.strip())
    await message.answer("Шаг 2 из 4: Введите **название юрлица** (например: `ООО фирма \"Мосводопром\"`):")
    await state.set_state(CertForm.company)

@dp.message(CertForm.company)
async def process_company(message: Message, state: FSMContext):
    await state.update_data(company=message.text.strip())
    await message.answer("Шаг 3 из 4: Введите **ИНН** (например: `7721023832`):")
    await state.set_state(CertForm.inn)

@dp.message(CertForm.inn)
async def process_inn(message: Message, state: FSMContext):
    await state.update_data(inn=message.text.strip())
    await message.answer("Шаг 4 из 4: Введите **срок действия** (например: `27.08.2026`):")
    await state.set_state(CertForm.date)

@dp.message(CertForm.date)
async def process_date(message: Message, state: FSMContext):
    data = await state.get_data()
    valid_until = message.text.strip()
    await state.clear()

    await message.answer("⏳ Создаю сертификат, подождите...")

    img_buf, pdf_buf = generate_certificate(
        cert_num=data["number"],
        company_name=data["company"],
        inn=data["inn"],
        valid_until=valid_until
    )

    # 1. Отправка фото для быстрого просмотра
    photo_file = BufferedInputFile(img_buf.getvalue(), filename="certificate.jpg")
    await message.answer_photo(photo_file, caption=f"✅ Сертификат {data['number']} готов!\nНовый — /start")

    # 2. Отправка PDF высокого качества для печати
    pdf_name = f"Сертификат_{data['number'].replace('/', '_')}.pdf"
    pdf_file = BufferedInputFile(pdf_buf.getvalue(), filename=pdf_name)
    await message.answer_document(pdf_file)

async def healthcheck(request):
    """Эндпоинт для проверки активности Render"""
    return web.Response(text="Certificate Bot is alive and kicking 24/7!")

# Встроенный авто-пингатор (держит Render активным без сторонних сервисов)
async def self_ping():
    await asyncio.sleep(30)  # Даем серверу запуститься перед первым пингом
    
    url = RENDER_EXTERNAL_URL
    if not url:
        url = f"http://localhost:{PORT}"
        print(f"[Пингатор] RENDER_EXTERNAL_URL не задана. Пингуем локально: {url}")
    else:
        if not url.startswith("http"):
            url = f"https://{url}"

    print(f"[Пингатор] Автопинг запущен на адрес: {url}")
    
    while True:
        try:
            async with ClientSession() as session:
                async with session.get(url, timeout=15) as resp:
                    print(f"[Пингатор] Успешный пинг на {url} | Код: {resp.status}")
        except Exception as e:
            print(f"[Пингатор] Ошибка запроса: {e}")
            
        await asyncio.sleep(600)  # Пинг раз в 10 минут (Render засыпает через 15)

async def main():
    # 1. Запуск мини-сервера
    app = web.Application()
    app.router.add_get("/", healthcheck)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Веб-сервер слушает порт {PORT}")

    # 2. Фоновый самопинг
    asyncio.create_task(self_ping())

    # 3. Telegram-бот
    print("Бот готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
