import os
import asyncio
import datetime
from aiohttp import web, ClientSession
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    BufferedInputFile,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)

from generator import generate_certificate, generate_doverennost

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

bot = Bot(token=BOT_TOKEN or "dummy_token")
dp = Dispatcher()

# Главное меню с кнопками
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📄 Создать Сертификат"), KeyboardButton(text="📝 Создать Доверенность М-2")]
    ],
    resize_keyboard=True
)

# Состояния для Сертификата
class CertForm(StatesGroup):
    number = State()
    company = State()
    inn = State()
    date = State()

# Состояния для Доверенности М-2 (пошаговый режим)
class DovForm(StatesGroup):
    number = State()
    date_valid = State()
    fio = State()
    supplier = State()
    bill_info = State()
    passport_data = State()
    items = State()


# ==============================================================================
# КОМАНДА СТАРТ И МЕНЮ
# ==============================================================================
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 **Добро пожаловать в генератор документов ООО \"ПК МИШКА\"!**\n\n"
        "Выберите действие в меню внизу или используйте команды:\n"
        "• Нажмите **\"📄 Создать Сертификат\"**\n"
        "• Нажмите **\"📝 Создать Доверенность М-2\"**\n\n"
        "💡 *Доверенность можно также заполнить моментально одной командой /dov.*",
        reply_markup=main_keyboard
    )


# ==============================================================================
# СЦЕНАРИЙ 1: СЕРТИФИКАТ ДИЛЕРА
# ==============================================================================
@dp.message(F.text == "📄 Создать Сертификат")
@dp.message(Command("cert"))
async def start_cert(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Шаг 1 из 4: Введите **номер сертификата** (например: `2708/25`):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(CertForm.number)

@dp.message(CertForm.number)
async def cert_num(message: Message, state: FSMContext):
    await state.update_data(number=message.text.strip())
    await message.answer("Шаг 2 из 4: Введите **название юрлица** (например: `ООО фирма \"Мосводопром\"`):")
    await state.set_state(CertForm.company)

@dp.message(CertForm.company)
async def cert_company(message: Message, state: FSMContext):
    await state.update_data(company=message.text.strip())
    await message.answer("Шаг 3 из 4: Введите **ИНН** (например: `7721023832`):")
    await state.set_state(CertForm.inn)

@dp.message(CertForm.inn)
async def cert_inn(message: Message, state: FSMContext):
    await state.update_data(inn=message.text.strip())
    await message.answer("Шаг 4 из 4: Введите **срок действия** (например: `27.08.2026`):")
    await state.set_state(CertForm.date)

@dp.message(CertForm.date)
async def cert_date(message: Message, state: FSMContext):
    data = await state.get_data()
    valid_until = message.text.strip()
    await state.clear()

    await message.answer("⏳ Создаю сертификат...")

    img_buf, pdf_buf = generate_certificate(
        cert_num=data["number"],
        company_name=data["company"],
        inn=data["inn"],
        valid_until=valid_until
    )

    photo_file = BufferedInputFile(img_buf.getvalue(), filename="certificate.jpg")
    await message.answer_photo(photo_file, caption=f"✅ Сертификат {data['number']} готов!", reply_markup=main_keyboard)

    pdf_name = f"Сертификат_{data['number'].replace('/', '_')}.pdf"
    pdf_file = BufferedInputFile(pdf_buf.getvalue(), filename=pdf_name)
    await message.answer_document(pdf_file)


# ==============================================================================
# СЦЕНАРИЙ 2: ДОВЕРЕННОСТЬ М-2
# ==============================================================================
# 1. Быстрая команда /dov в одну строку
@dp.message(Command("dov"))
async def quick_dov(message: Message):
    text = message.text.replace("/dov", "").strip()
    if not text:
        await message.answer(
            "📋 **Быстрое создание доверенности М-2 в одну строку**\n\n"
            "Отправьте данные через разделитель `|`:\n"
            "```text\n"
            "/dov Номер | СрокПо | ФИО | Поставщик | Счет | Серия | НомерПаспорта | КемВыдан | ДатаВыдачиПаспорта | Товар1:ед:кол, Товар2:ед:кол\n"
            "```\n"
            "*Пример готовой команды:*\n"
            "`/dov 15 | 20.10.2026 | Мамыкин Алексей Константинович | ООО \"СТАИРС ПРОФИ\" | счету №1397 от 01 октября 2026 | 4621 | 22318 | ГУ МВД России по Московской области | 24.02.2021 | Лестница приставная 08 ступ:шт:100, Заглушка 54 синяя:шт:400`",
            reply_markup=main_keyboard
        )
        return

    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 9:
        await message.answer("⚠️ Не хватает данных. Проверьте разделители `|` (должно быть минимум 9 полей).")
        return

    num = parts[0]
    date_valid = parts[1]
    fio = parts[2]
    supplier = parts[3]
    bill_info = parts[4]
    p_series = parts[5]
    p_num = parts[6]
    p_by = parts[7]
    p_date = parts[8]
    date_issue = datetime.datetime.now().strftime("%d.%m.%Y")

    items = []
    if len(parts) >= 10:
        raw_items = parts[9].split(",")
        for it in raw_items:
            sub = [s.strip() for s in it.split(":")]
            if len(sub) == 3:
                items.append((sub[0], sub[1], sub[2]))
            elif len(sub) == 1:
                items.append((sub[0], "шт", "1"))

    await message.answer("⏳ Генерирую доверенность...")

    img_buf, pdf_buf = generate_doverennost(
        number=num,
        date_issue=date_issue,
        date_valid=date_valid,
        fio=fio,
        supplier=supplier,
        passport_series=p_series,
        passport_number=p_num,
        passport_issued_by=p_by,
        passport_date=p_date,
        bill_info=bill_info,
        items=items
    )

    photo_file = BufferedInputFile(img_buf.getvalue(), filename="doverennost.jpg")
    await message.answer_photo(photo_file, caption=f"✅ Доверенность №{num} готова! (повторяющиеся поля заполнены автоматически)", reply_markup=main_keyboard)

    pdf_file = BufferedInputFile(pdf_buf.getvalue(), filename=f"Доверенность_№{num}.pdf")
    await message.answer_document(pdf_file)


# 2. Пошаговое создание через кнопку меню
@dp.message(F.text == "📝 Создать Доверенность М-2")
async def start_dov_step(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📝 **Создание доверенности М-2 (пошагово)**\n\n"
        "Шаг 1 из 6: Введите **номер доверенности** (например: `15`):",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(DovForm.number)

@dp.message(DovForm.number)
async def dov_step_num(message: Message, state: FSMContext):
    await state.update_data(number=message.text.strip())
    await message.answer("Шаг 2 из 6: Введите **срок действия доверенности (по какую дату)** (например: `20.10.2026`):")
    await state.set_state(DovForm.date_valid)

@dp.message(DovForm.date_valid)
async def dov_step_date(message: Message, state: FSMContext):
    await state.update_data(date_valid=message.text.strip())
    await message.answer("Шаг 3 из 6: Введите **ФИО сотрудника** (например: `Мамыкин Алексей Константинович`):\n*(Оно автоматически заполнится и в корешке, и в теле документа)*")
    await state.set_state(DovForm.fio)

@dp.message(DovForm.fio)
async def dov_step_fio(message: Message, state: FSMContext):
    await state.update_data(fio=message.text.strip())
    await message.answer("Шаг 4 из 6: Введите **поставщика** (например: `ООО \"СТАИРС ПРОФИ\"`):\n*(Заполнится сразу в обоих местах)*")
    await state.set_state(DovForm.supplier)

@dp.message(DovForm.supplier)
async def dov_step_supplier(message: Message, state: FSMContext):
    await state.update_data(supplier=message.text.strip())
    await message.answer("Шаг 5 из 6: Введите **документ-основание** (например: `счету №1397 от 01 октября 2026`):")
    await state.set_state(DovForm.bill_info)

@dp.message(DovForm.bill_info)
async def dov_step_bill(message: Message, state: FSMContext):
    await state.update_data(bill_info=message.text.strip())
    await message.answer(
        "Шаг 6 из 6: Введите **паспортные данные** через запятую:\n"
        "`Серия, Номер, Кем выдан, Дата выдачи`\n\n"
        "*Пример:*\n`4621, 22318, ГУ МВД России по Московской области, 24.02.2021`"
    )
    await state.set_state(DovForm.passport_data)

@dp.message(DovForm.passport_data)
async def dov_step_passport(message: Message, state: FSMContext):
    parts = [p.strip() for p in message.text.split(",")]
    if len(parts) < 4:
        await message.answer("⚠️ Укажите все 4 значения через запятую: Серия, Номер, Кем выдан, Дата выдачи.")
        return
    await state.update_data(
        p_series=parts[0],
        p_num=parts[1],
        p_by=parts[2],
        p_date=parts[3]
    )
    await message.answer(
        "📦 Введите **перечень товаров** (до 4 строк).\n"
        "Формат: `Название : ед.изм : кол-во` (каждый товар с новой строки).\n\n"
        "*Пример:*\n"
        "Лестница односекционная 08 ступеней : шт : 100\n"
        "Заглушка пластиковая 54 синяя : шт : 400"
    )
    await state.set_state(DovForm.items)

@dp.message(DovForm.items)
async def dov_step_items(message: Message, state: FSMContext):
    data = await state.get_data()
    lines = [l.strip() for l in message.text.split("\n") if l.strip()]
    items = []
    for line in lines:
        parts = [p.strip() for p in line.split(":")]
        if len(parts) == 3:
            items.append((parts[0], parts[1], parts[2]))
        elif len(parts) == 1:
            items.append((parts[0], "шт", "1"))

    await state.clear()
    await message.answer("⏳ Создаю доверенность...")

    date_issue = datetime.datetime.now().strftime("%d.%m.%Y")
    img_buf, pdf_buf = generate_doverennost(
        number=data["number"],
        date_issue=date_issue,
        date_valid=data["date_valid"],
        fio=data["fio"],
        supplier=data["supplier"],
        passport_series=data["p_series"],
        passport_number=data["p_num"],
        passport_issued_by=data["p_by"],
        passport_date=data["p_date"],
        bill_info=data["bill_info"],
        items=items
    )

    photo_file = BufferedInputFile(img_buf.getvalue(), filename="doverennost.jpg")
    await message.answer_photo(photo_file, caption=f"✅ Доверенность №{data['number']} готова!", reply_markup=main_keyboard)

    pdf_file = BufferedInputFile(pdf_buf.getvalue(), filename=f"Доверенность_№{data['number']}.pdf")
    await message.answer_document(pdf_file)


# ==============================================================================
# СЕРВЕР И АВТО-ПИНГАТОР ДЛЯ RENDER (24/7)
# ==============================================================================
async def healthcheck(request):
    return web.Response(text="Mishka Docs Bot is running 24/7!")

async def self_ping():
    await asyncio.sleep(30)
    url = RENDER_EXTERNAL_URL
    if not url:
        url = f"http://localhost:{PORT}"
        print(f"[Пингатор] RENDER_EXTERNAL_URL не задана. Локальный пинг: {url}")
    else:
        if not url.startswith("http"):
            url = f"https://{url}"
    print(f"[Пингатор] Автопинг включен: {url}")

    while True:
        try:
            async with ClientSession() as session:
                async with session.get(url, timeout=15) as resp:
                    print(f"[Пингатор] Пинг отправлен | Статус: {resp.status}")
        except Exception as e:
            print(f"[Пингатор] Ошибка: {e}")
        await asyncio.sleep(600)

async def main():
    app = web.Application()
    app.router.add_get("/", healthcheck)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Веб-сервер слушает порт {PORT}")

    asyncio.create_task(self_ping())

    # Сбрасываем зависшие обновления Telegram для исключения конфликтов
    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
