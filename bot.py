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

from generator import generate_certificate, generate_doverennost, generate_diler_contract

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

bot = Bot(token=BOT_TOKEN or "dummy_token")
dp = Dispatcher()

# Главное меню
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📄 Создать Сертификат"), KeyboardButton(text="📝 Создать Доверенность М-2")],
        [KeyboardButton(text="📑 Оформить Дилерский договор")]
    ],
    resize_keyboard=True
)

class CertForm(StatesGroup):
    number = State()
    company = State()
    inn = State()
    date = State()

class DovForm(StatesGroup):
    number = State()
    date_valid = State()
    fio = State()
    supplier = State()
    bill_info = State()
    passport_data = State()
    items = State()


# ==============================================================================
# СТАРТ И МЕНЮ
# ==============================================================================
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 **Генератор документов ООО «ПК МИШКА»**\n\n"
        "Выберите действие в меню внизу:\n"
        "• **«📄 Создать Сертификат»**\n"
        "• **«📝 Создать Доверенность М-2»**\n"
        "• **«📑 Оформить Дилерский договор»**\n\n"
        "💡 *Быстрые команды для создания в 1 строку:*\n"
        "`/dov` — Доверенность\n"
        "`/dogovor` — Дилерский договор",
        reply_markup=main_keyboard
    )


# ==============================================================================
# 1. СЕРТИФИКАТ ДИЛЕРА
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

    pdf_file = BufferedInputFile(pdf_buf.getvalue(), filename=f"Сертификат_{data['number'].replace('/', '_')}.pdf")
    await message.answer_document(pdf_file)


# ==============================================================================
# 2. ДОВЕРЕННОСТЬ М-2
# ==============================================================================
@dp.message(Command("dov"))
async def quick_dov(message: Message):
    text = message.text.replace("/dov", "").strip()
    if not text:
        await message.answer(
            "📋 **Создание доверенности М-2 в одну строку**\n\n"
            "Формат команды через `|` (товары разделяются `;`):\n"
            "```text\n"
            "/dov Номер | СрокПо | ФИО | Поставщик | Счет | Серия | НомерПаспорта | КемВыдан | ДатаВыдачи | Товар 1 : шт : 10 ; Товар 2 : шт : 20\n"
            "```\n\n"
            "*Пример готовой команды:*\n"
            "`/dov 7 | 13.11.2026 | Мачнев Алексей Игоревич | ООО СДВ ИНЖИНИРИНГ | счету №1488 от 09.11.2026 | 45 14 | 160544 | ГУ МВД ГОРОДА МОСКВЫ | 13.05.2013 | Лестница приставная 08 ступ : шт : 100 ; Заглушка 54 синяя : шт : 400`",
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
        raw_items = [x for x in parts[9].replace(";", "\n").split("\n") if x.strip()]
        for it in raw_items:
            sub = [s.strip() for s in it.split(":")]
            if len(sub) == 3:
                items.append((sub[0], sub[1], sub[2]))
            elif len(sub) == 1:
                items.append((sub[0], "шт", "1"))

    await message.answer("⏳ Создаю доверенность...")

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
    await message.answer_photo(photo_file, caption=f"✅ Доверенность №{num} готова!", reply_markup=main_keyboard)

    pdf_file = BufferedInputFile(pdf_buf.getvalue(), filename=f"Доверенность_№{num}.pdf")
    await message.answer_document(pdf_file)


@dp.message(F.text == "📝 Создать Доверенность М-2")
async def start_dov_step(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Шаг 1 из 6: Введите **номер доверенности** (например: `7`):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(DovForm.number)

@dp.message(DovForm.number)
async def dov_step_num(message: Message, state: FSMContext):
    await state.update_data(number=message.text.strip())
    await message.answer("Шаг 2 из 6: Введите **срок действия (по какую дату)** (например: `13.11.2026`):")
    await state.set_state(DovForm.date_valid)

@dp.message(DovForm.date_valid)
async def dov_step_date(message: Message, state: FSMContext):
    await state.update_data(date_valid=message.text.strip())
    await message.answer("Шаг 3 из 6: Введите **ФИО сотрудника** (например: `Мачнев Алексей Игоревич`):")
    await state.set_state(DovForm.fio)

@dp.message(DovForm.fio)
async def dov_step_fio(message: Message, state: FSMContext):
    await state.update_data(fio=message.text.strip())
    await message.answer("Шаг 4 из 6: Введите **поставщика** (например: `ООО СДВ ИНЖИНИРИНГ`):")
    await state.set_state(DovForm.supplier)

@dp.message(DovForm.supplier)
async def dov_step_supplier(message: Message, state: FSMContext):
    await state.update_data(supplier=message.text.strip())
    await message.answer("Шаг 5 из 6: Введите **номер и дату счета** (например: `счету №1488 от 09.11.2026`):")
    await state.set_state(DovForm.bill_info)

@dp.message(DovForm.bill_info)
async def dov_step_bill(message: Message, state: FSMContext):
    await state.update_data(bill_info=message.text.strip())
    await message.answer(
        "Шаг 6 из 6: Введите **паспортные данные** через запятую:\n"
        "`Серия, Номер, Кем выдан, Дата выдачи`\n\n"
        "*Пример:*\n`45 14, 160544, ГУ МВД ГОРОДА МОСКВЫ, 13.05.2013`"
    )
    await state.set_state(DovForm.passport_data)

@dp.message(DovForm.passport_data)
async def dov_step_passport(message: Message, state: FSMContext):
    parts = [p.strip() for p in message.text.split(",")]
    if len(parts) < 4:
        await message.answer("⚠️ Введите 4 значения через запятую: Серия, Номер, Кем выдан, Дата выдачи.")
        return
    await state.update_data(
        p_series=parts[0],
        p_num=parts[1],
        p_by=parts[2],
        p_date=parts[3]
    )
    await message.answer(
        "📦 Введите **перечень товаров** (до 4 строк, каждая позиция с новой строки):\n"
        "Формат: `Название : ед : количество`\n\n"
        "*Пример:*\n"
        "Лестница приставная 08 ступ : шт : 100\n"
        "Заглушка 54 синяя : шт : 400"
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
# 3. ДИЛЕРСКИЙ ДОГОВОР
# ==============================================================================
@dp.message(F.text == "📑 Оформить Дилерский договор")
@dp.message(Command("dogovor"))
async def cmd_dogovor(message: Message):
    text = message.text.replace("/dogovor", "").replace("📑 Оформить Дилерский договор", "").strip()

    if not text:
        await message.answer(
            "📑 **Генерация 11-страничного Дилерского договора**\n\n"
            "Отправьте данные Дилера через разделитель `|`:\n\n"
            "```text\n"
            "/dogovor Номер | Дата | Название Дилера | Преамбула (в лице кого и на основании чего) | ФИО Директора (кратко) | Юр.адрес | ИНН/КПП | Р/счет | Корр.счет | Банк | БИК | Телефон\n"
            "```\n\n"
            "*Пример готовой команды:*\n"
            "`/dogovor 23940 | 10 ноября 2026 г. | ООО «Мосводопром» | в лице Генерального директора Иванова И.И., действующего на основании Устава | Иванов И.И. | 111524, г. Москва, ул. Электродная, д. 11 | 7721023832/772101001 | 40702810438710002682 | 30101810400000000225 | ПАО Сбербанк | 044525225 | +7(910)009-00-65`",
            reply_markup=main_keyboard
        )
        return

    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 12:
        await message.answer("⚠️ Не хватает данных. Проверьте, чтобы было 12 полей через символ `|`.")
        return

    await message.answer("⏳ Формирую 11-страничный договор...")

    try:
        pdf_buf = generate_diler_contract(
            contract_num=parts[0],
            contract_date=parts[1],
            dealer_name=parts[2],
            dealer_preamble=parts[3],
            dealer_fio_short=parts[4],
            dealer_address=parts[5],
            dealer_inn_kpp=parts[6],
            dealer_rs=parts[7],
            dealer_ks=parts[8],
            dealer_bank=parts[9],
            dealer_bik=parts[10],
            dealer_phone=parts[11]
        )

        doc_file = BufferedInputFile(pdf_buf.getvalue(), filename=f"Дилерский_договор_№{parts[0]}_{parts[2]}.pdf")
        await message.answer_document(doc_file, caption=f"✅ Дилерский договор №{parts[0]} готов во всех 11 страницах!")
    except Exception as e:
        await message.answer(f"❌ Ошибка при формировании договора: {e}")


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

    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
