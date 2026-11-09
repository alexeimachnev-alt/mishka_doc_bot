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

# Главное меню с кнопками
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📄 Создать Сертификат"), KeyboardButton(text="📝 Создать Доверенность М-2")],
        [KeyboardButton(text="📑 Оформить Дилерский договор")]
    ],
    resize_keyboard=True
)

# 1. Состояния для Сертификата
class CertForm(StatesGroup):
    number = State()
    company = State()
    inn = State()
    date = State()

# 2. Состояния для Доверенности М-2
class DovForm(StatesGroup):
    number = State()
    date_valid = State()
    fio = State()
    supplier = State()
    bill_info = State()
    passport_data = State()
    items = State()

# 3. Состояния для Дилерского договора (поступательное заполнение)
class ContractForm(StatesGroup):
    number = State()
    date = State()
    dealer_name = State()
    preamble = State()
    fio_short = State()
    address = State()
    inn_kpp = State()
    bank_details = State()
    phone = State()


# ==============================================================================
# СТАРТ И ГЛАВНОЕ МЕНЮ
# ==============================================================================
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 **Генератор документов ООО «ПК МИШКА»**\n\n"
        "Выберите нужный документ кнопкой внизу:\n"
        "• **«📄 Создать Сертификат»**\n"
        "• **«📝 Создать Доверенность М-2»**\n"
        "• **«📑 Оформить Дилерский договор»**\n\n"
        "Все документы заполняются пошагово с удобными подсказками.",
        reply_markup=main_keyboard
    )


# ==============================================================================
# 1. СЕРТИФИКАТ ДИЛЕРА (ПОШАГОВО)
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
# 2. ДОВЕРЕННОСТЬ М-2 (ПОШАГОВО И БЫСТРО)
# ==============================================================================
@dp.message(Command("dov"))
async def quick_dov(message: Message):
    text = message.text.replace("/dov", "").strip()
    if not text:
        await message.answer(
            "📋 **Создание доверенности М-2**\n"
            "Нажмите кнопку внизу или отправьте данные одной строкой через `|`:\n"
            "`/dov 7 | 13.11.2026 | Мачнев Алексей Игоревич | ООО СДВ ИНЖИНИРИНГ | счету №1488 от 09.11.2026 | 45 14 | 160544 | ГУ МВД ГОРОДА МОСКВЫ | 13.05.2013 | Лестница : шт : 100 ; Заглушка : шт : 400`",
            reply_markup=main_keyboard
        )
        return

    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 9:
        await message.answer("⚠️ Не хватает данных. Проверьте разделители `|` (минимум 9 полей).")
        return

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
        number=parts[0],
        date_issue=date_issue,
        date_valid=parts[1],
        fio=parts[2],
        supplier=parts[3],
        passport_series=parts[5],
        passport_number=parts[6],
        passport_issued_by=parts[7],
        passport_date=parts[8],
        bill_info=parts[4],
        items=items
    )

    photo_file = BufferedInputFile(img_buf.getvalue(), filename="doverennost.jpg")
    await message.answer_photo(photo_file, caption=f"✅ Доверенность №{parts[0]} готова!", reply_markup=main_keyboard)

    pdf_file = BufferedInputFile(pdf_buf.getvalue(), filename=f"Доверенность_№{parts[0]}.pdf")
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
    await message.answer("Шаг 4 из 6: Введите **название поставщика** (например: `ООО СДВ ИНЖИНИРИНГ`):")
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
# 3. ДИЛЕРСКИЙ ДОГОВОР (ПОСТУПАТЕЛЬНОЕ ЗАПОЛНЕНИЕ)
# ==============================================================================
@dp.message(F.text == "📑 Оформить Дилерский договор")
@dp.message(Command("dogovor"))
async def start_contract_step(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📑 **Оформление Дилерского договора (по шагам)**\n\n"
        "Шаг 1 из 7: Введите **номер договора** (например: `23940`):",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(ContractForm.number)

@dp.message(ContractForm.number)
async def contract_step_num(message: Message, state: FSMContext):
    await state.update_data(number=message.text.strip())
    # Предлагаем текущую дату или ручной ввод
    today_str = datetime.datetime.now().strftime("«%d» %m %Y г.")
    await message.answer(
        f"Шаг 2 из 7: Введите **дату договора** (или отправьте `сегодня` для даты {today_str}):\n\n"
        "*Пример:* `«10» ноября 2026 г.`"
    )
    await state.set_state(ContractForm.date)

@dp.message(ContractForm.date)
async def contract_step_date(message: Message, state: FSMContext):
    d_text = message.text.strip()
    if d_text.lower() == "сегодня":
        d_text = datetime.datetime.now().strftime("«%d» %m %Y г.")
    await state.update_data(date=d_text)
    
    await message.answer(
        "Шаг 3 из 7: Введите **полное наименование компании Дилера / Покупателя**:\n\n"
        "*Пример:* `ООО «Мосводопром»` или `ИП Иванов Иван Иванович`"
    )
    await state.set_state(ContractForm.dealer_name)

@dp.message(ContractForm.dealer_name)
async def contract_step_name(message: Message, state: FSMContext):
    await state.update_data(dealer_name=message.text.strip())
    await message.answer(
        "Шаг 4 из 7: Введите **должность, ФИО руководителя и основание** (для первой страницы):\n\n"
        "*Пример:* `в лице Генерального директора Иванова И.И., действующего на основании Устава`"
    )
    await state.set_state(ContractForm.preamble)

@dp.message(ContractForm.preamble)
async def contract_step_preamble(message: Message, state: FSMContext):
    await state.update_data(preamble=message.text.strip())
    await message.answer(
        "Шаг 5 из 7: Введите **фамилию и инициалы руководителя для подписи**:\n\n"
        "*Пример:* `Иванов И.И.`"
    )
    await state.set_state(ContractForm.fio_short)

@dp.message(ContractForm.fio_short)
async def contract_step_fio(message: Message, state: FSMContext):
    await state.update_data(fio_short=message.text.strip())
    await message.answer(
        "Шаг 6 из 7: Введите **юридический адрес** и **ИНН/КПП** (через символ `/` или с новой строки):\n\n"
        "*Пример:*\n"
        "111524, г. Москва, ул. Электродная, д. 11\n"
        "7721023832 / 772101001"
    )
    await state.set_state(ContractForm.address)

@dp.message(ContractForm.address)
async def contract_step_addr(message: Message, state: FSMContext):
    lines = [l.strip() for l in message.text.split("\n") if l.strip()]
    if len(lines) >= 2:
        addr = lines[0]
        inn_kpp = lines[1]
    else:
        # Если введено одной строкой через запятую
        parts = message.text.split(",")
        addr = ",".join(parts[:-1]).strip() if len(parts) > 1 else parts[0].strip()
        inn_kpp = parts[-1].strip() if len(parts) > 1 else "—"

    await state.update_data(address=addr, inn_kpp=inn_kpp)
    await message.answer(
        "Шаг 7 из 7: Введите **банковские реквизиты и телефон** (каждый пункт с новой строки):\n\n"
        "1. Расчетный счет\n"
        "2. Корр. счет\n"
        "3. Название банка\n"
        "4. БИК\n"
        "5. Телефон\n\n"
        "*Пример:*\n"
        "40702810438710002682\n"
        "30101810400000000225\n"
        "ПАО Сбербанк\n"
        "044525225\n"
        "+7(910)009-00-65"
    )
    await state.set_state(ContractForm.bank_details)

@dp.message(ContractForm.bank_details)
async def contract_step_finish(message: Message, state: FSMContext):
    lines = [l.strip() for l in message.text.split("\n") if l.strip()]
    rs = lines[0] if len(lines) > 0 else "—"
    ks = lines[1] if len(lines) > 1 else "—"
    bank = lines[2] if len(lines) > 2 else "—"
    bik = lines[3] if len(lines) > 3 else "—"
    phone = lines[4] if len(lines) > 4 else "—"

    data = await state.get_data()
    await state.clear()

    await message.answer("⏳ Создаю 11-страничный Дилерский договор...", reply_markup=main_keyboard)

    try:
        pdf_buf = generate_diler_contract(
            contract_num=data["number"],
            contract_date=data["date"],
            dealer_name=data["dealer_name"],
            dealer_preamble=data["preamble"],
            dealer_fio_short=data["fio_short"],
            dealer_address=data["address"],
            dealer_inn_kpp=data["inn_kpp"],
            dealer_rs=rs,
            dealer_ks=ks,
            dealer_bank=bank,
            dealer_bik=bik,
            dealer_phone=phone
        )

        doc_file = BufferedInputFile(pdf_buf.getvalue(), filename=f"Дилерский_договор_№{data['number']}_{data['dealer_name']}.pdf")
        await message.answer_document(doc_file, caption=f"✅ Дилерский договор №{data['number']} успешно оформлен во всех 11 страницах!")
    except Exception as e:
        await message.answer(f"❌ Ошибка при формировании договора: {e}", reply_markup=main_keyboard)


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
