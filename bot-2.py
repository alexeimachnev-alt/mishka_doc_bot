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

from generator import generate_certificate
from generator_docx import generate_diler_contract_docx, convert_docx_to_pdf
from generator_excel import generate_doverennost_xlsx, convert_xlsx_to_pdf

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

bot = Bot(token=BOT_TOKEN or "dummy_token")
dp = Dispatcher()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📄 Создать Сертификат"), KeyboardButton(text="📝 Создать Доверенность М-2")],
        [KeyboardButton(text="📑 Оформить Дилерский договор")]
    ],
    resize_keyboard=True
)

dealer_type_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏢 Юрлицо / ИП (реквизиты счета)"), KeyboardButton(text="👤 Физлицо (паспортные данные)")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

class ContractForm(StatesGroup):
    dealer_type = State()
    number = State()
    date = State()
    dealer_name = State()
    preamble = State()
    fio_short = State()
    address = State()
    bank_details = State()
    fiz_passport = State()

class DoverennostForm(StatesGroup):
    number = State()
    dates = State()
    fio_job = State()
    passport = State()
    supplier = State()
    item = State()

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 **Генератор документов ООО «ПК МИШКА»**\n\n"
        "Выберите нужный документ кнопкой внизу.",
        reply_markup=main_keyboard
    )

# ==============================================================================
# 1. ДОВЕРЕННОСТЬ М-2 (EXCEL -> PDF)
# ==============================================================================
@dp.message(F.text == "📝 Создать Доверенность М-2")
@dp.message(Command("dov"))
async def start_dov_step(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📝 **Оформление Доверенности М-2 (по ГОСТу с печатью)**\n\n"
        "Шаг 1: Введите **номер доверенности**:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(DoverennostForm.number)

@dp.message(DoverennostForm.number)
async def dov_step_num(message: Message, state: FSMContext):
    await state.update_data(number=message.text.strip())
    await message.answer("Шаг 2: Введите **дату выдачи** и **срок действия** (каждую с новой строки).\n*Пример:*\n2023-11-01\n2023-11-15")
    await state.set_state(DoverennostForm.dates)

@dp.message(DoverennostForm.dates)
async def dov_step_dates(message: Message, state: FSMContext):
    lines = message.text.strip().split('\n')
    await state.update_data(
        date_issue=lines[0] if len(lines) > 0 else "",
        date_valid=lines[1] if len(lines) > 1 else ""
    )
    await message.answer("Шаг 3: Введите **должность** и **ФИО** доверенного лица (с новой строки).\n*Пример:*\nменеджер\nПетров Петр Петрович")
    await state.set_state(DoverennostForm.fio_job)

@dp.message(DoverennostForm.fio_job)
async def dov_step_fio(message: Message, state: FSMContext):
    lines = message.text.strip().split('\n')
    await state.update_data(
        fio_job=lines[0] if len(lines) > 0 else "",
        fio=lines[1] if len(lines) > 1 else ""
    )
    await message.answer("Шаг 4: Введите **паспортные данные** (Серия, Номер, Кем выдан, Дата выдачи — всё с новой строки).\n*Пример:*\n1234\n567890\nОВД Тверского района г. Москвы\n12.12.2020")
    await state.set_state(DoverennostForm.passport)

@dp.message(DoverennostForm.passport)
async def dov_step_passport(message: Message, state: FSMContext):
    lines = message.text.strip().split('\n')
    await state.update_data(
        passport_series=lines[0] if len(lines) > 0 else "",
        passport_number=lines[1] if len(lines) > 1 else "",
        passport_issued_by=lines[2] if len(lines) > 2 else "",
        passport_date=lines[3] if len(lines) > 3 else ""
    )
    await message.answer("Шаг 5: Введите наименование **поставщика**:\n*Пример:* ООО «Ромашка»")
    await state.set_state(DoverennostForm.supplier)

@dp.message(DoverennostForm.supplier)
async def dov_step_supplier(message: Message, state: FSMContext):
    await state.update_data(supplier=message.text.strip())
    await message.answer("Шаг 6: Укажите **ТМЦ к получению** (Наименование, ед.изм., кол-во — через перенос строки).\n*Пример:*\nКабель силовой\nм\n150")
    await state.set_state(DoverennostForm.item)

@dp.message(DoverennostForm.item)
async def dov_step_finish(message: Message, state: FSMContext):
    lines = message.text.strip().split('\n')
    await state.update_data(
        item_name=lines[0] if len(lines) > 0 else "",
        item_unit=lines[1] if len(lines) > 1 else "",
        item_qty=lines[2] if len(lines) > 2 else ""
    )
    
    data = await state.get_data()
    await state.clear()
    
    await message.answer("⏳ Генерирую доверенность М-2 (XLSX и PDF)...", reply_markup=main_keyboard)
    try:
        # Генерируем Excel
        xlsx_buf = generate_doverennost_xlsx(data)
        xlsx_file = BufferedInputFile(xlsx_buf.getvalue(), filename=f"Доверенность_М2_№{data['number']}.xlsx")
        await message.answer_document(xlsx_file, caption=f"✅ Доверенность №{data['number']} (Excel)")

        # Конвертируем в PDF через LibreOffice
        pdf_buf = convert_xlsx_to_pdf(xlsx_buf)
        if pdf_buf:
            pdf_file = BufferedInputFile(pdf_buf.getvalue(), filename=f"Доверенность_М2_№{data['number']}.pdf")
            await message.answer_document(pdf_file, caption=f"✅ Доверенность №{data['number']} (PDF)")
        else:
            await message.answer("⚠️ Сервер не смог сгенерировать PDF, но Excel-документ готов!")
    except Exception as e:
        await message.answer(f"❌ Ошибка генерации: {e}")

# ==============================================================================
# 2. ДИЛЕРСКИЙ ДОГОВОР
# ==============================================================================
@dp.message(F.text == "📑 Оформить Дилерский договор")
@dp.message(Command("dogovor"))
async def start_contract_step(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📑 **Оформление Дилерского договора (формат DOCX)**\n\n"
        "Выберите тип Дилера кнопкой внизу:",
        reply_markup=dealer_type_keyboard
    )
    await state.set_state(ContractForm.dealer_type)

@dp.message(ContractForm.dealer_type)
async def contract_step_type(message: Message, state: FSMContext):
    is_fiz = "физлицо" in message.text.lower()
    await state.update_data(is_fiz=is_fiz)
    await message.answer("Шаг 1: Введите **номер договора** (например: `23940`):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ContractForm.number)

@dp.message(ContractForm.number)
async def contract_step_num(message: Message, state: FSMContext):
    await state.update_data(number=message.text.strip())
    today_str = datetime.datetime.now().strftime("«%d» %m %Y г.")
    await message.answer(f"Шаг 2: Введите **дату договора** (или отправьте `сегодня` для даты {today_str}):")
    await state.set_state(ContractForm.date)

@dp.message(ContractForm.date)
async def contract_step_date(message: Message, state: FSMContext):
    d_text = message.text.strip()
    if d_text.lower() == "сегодня":
        months_ru = {1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая", 6: "июня", 7: "июля", 8: "августа", 9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"}
        now = datetime.datetime.now()
        d_text = f"«{now.day:02d}» {months_ru[now.month]} {now.year} г."
    await state.update_data(date=d_text)

    data = await state.get_data()
    if data.get("is_fiz"):
        await message.answer("Шаг 3: Введите **полное ФИО Дилера (физлица)**:\n*Пример:* `Болталина Карина Николаевна`")
    else:
        await message.answer("Шаг 3: Введите **полное наименование компании Дилера / ИП**:\n*Пример:* `ООО «Мосводопром»`")
    await state.set_state(ContractForm.dealer_name)

@dp.message(ContractForm.dealer_name)
async def contract_step_name(message: Message, state: FSMContext):
    await state.update_data(dealer_name=message.text.strip())
    data = await state.get_data()
    if data.get("is_fiz"):
        await state.update_data(preamble="")
        await message.answer("Шаг 4: Введите **фамилию и инициалы для подписи**:\n*Пример:* `Болталина К.Н.`")
        await state.set_state(ContractForm.fio_short)
    else:
        await message.answer("Шаг 4: Введите **должность, ФИО руководителя и основание** (или `-`):\n*Пример:* `в лице Генерального директора Иванова И.И., действующего на основании Устава`")
        await state.set_state(ContractForm.preamble)

@dp.message(ContractForm.preamble)
async def contract_step_preamble(message: Message, state: FSMContext):
    p_text = message.text.strip()
    if p_text in ["-", "—", "нет"]: p_text = ""
    await state.update_data(preamble=p_text)
    await message.answer("Шаг 5: Введите **фамилию и инициалы руководителя для подписи**:\n*Пример:* `Иванов И.И.`")
    await state.set_state(ContractForm.fio_short)

@dp.message(ContractForm.fio_short)
async def contract_step_fio(message: Message, state: FSMContext):
    await state.update_data(fio_short=message.text.strip())
    data = await state.get_data()

    if data.get("is_fiz"):
        await message.answer(
            "Шаг 5: Введите **паспортные данные, адрес регистрации и телефон** (каждый пункт с новой строки):\n"
            "1. Серия и номер паспорта\n2. Дата выдачи\n3. Кем выдан\n4. Адрес регистрации\n5. Контактный телефон"
        )
        await state.set_state(ContractForm.fiz_passport)
    else:
        await message.answer("Шаг 6: Введите **юридический адрес** и **ИНН/КПП** (с новой строки):")
        await state.set_state(ContractForm.address)

@dp.message(ContractForm.fiz_passport)
async def contract_step_fiz_finish(message: Message, state: FSMContext):
    lines = [l.strip() for l in message.text.split("\n") if l.strip()]
    p_ser_num = lines[0] if len(lines) > 0 else "—"
    p_date = lines[1] if len(lines) > 1 else "—"
    p_by = lines[2] if len(lines) > 2 else "—"
    p_addr = lines[3] if len(lines) > 3 else "—"
    p_phone = lines[4] if len(lines) > 4 else "—"

    data = await state.get_data()
    await state.clear()

    req_lines = [
        data["dealer_name"],
        f"Паспорт: серия {p_ser_num}",
        f"Выдан: {p_date} {p_by}",
        f"Адрес регистрации: {p_addr}",
        f"Тел.: {p_phone}",
        "Эл. почта: ____________________"
    ]
    await process_contract_generation(message, data, req_lines)

@dp.message(ContractForm.address)
async def contract_step_addr(message: Message, state: FSMContext):
    lines = [l.strip() for l in message.text.split("\n") if l.strip()]
    addr = lines[0] if len(lines) > 0 else message.text.strip()
    inn_kpp = lines[1] if len(lines) > 1 else "—"
    await state.update_data(address=addr, inn_kpp=inn_kpp)
    await message.answer("Шаг 7: Введите **банковские реквизиты и телефон** (каждый пункт с новой строки):\n1. Р/с\n2. К/с\n3. Банк\n4. БИК\n5. Телефон")
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

    req_lines = [
        data["dealer_name"],
        f"Юр. адрес: {data['address']}",
        f"ИНН/КПП: {data['inn_kpp']}",
        f"Р/с: {rs}",
        f"Банк: {bank}",
        f"К/с: {ks}",
        f"БИК: {bik}",
        f"Тел.: {phone}",
        "Эл. почта: ____________________"
    ]
    await process_contract_generation(message, data, req_lines)

async def process_contract_generation(message: Message, data: dict, req_lines: list):
    await message.answer("⏳ Генерирую документы (DOCX и PDF)...", reply_markup=main_keyboard)
    try:
        docx_buf = generate_diler_contract_docx(
            contract_num=data["number"],
            contract_date=data["date"],
            dealer_name=data["dealer_name"],
            dealer_preamble=data.get("preamble", ""),
            dealer_fio_short=data["fio_short"],
            custom_req_lines=req_lines
        )

        docx_file = BufferedInputFile(docx_buf.getvalue(), filename=f"Дилерский_договор_№{data['number']}_{data['dealer_name']}.docx")
        await message.answer_document(docx_file, caption=f"✅ Договор №{data['number']} в формате WORD (DOCX)")

        pdf_buf = convert_docx_to_pdf(docx_buf)
        if pdf_buf:
            pdf_file = BufferedInputFile(pdf_buf.getvalue(), filename=f"Дилерский_договор_№{data['number']}_{data['dealer_name']}.pdf")
            await message.answer_document(pdf_file, caption=f"✅ Договор №{data['number']} в формате PDF")
        else:
            await message.answer("⚠️ Сервер не смог сгенерировать PDF (не установлен LibreOffice), но документ Word полностью готов к использованию!")
    except Exception as e:
        await message.answer(f"❌ Ошибка генерации: {e}")

async def healthcheck(request):
    return web.Response(text="Mishka Docs Bot is running 24/7!")

async def self_ping():
    await asyncio.sleep(30)
    url = RENDER_EXTERNAL_URL or f"http://localhost:{PORT}"
    if not url.startswith("http"): url = f"https://{url}"
    while True:
        try:
            async with ClientSession() as session:
                await session.get(url, timeout=15)
        except Exception:
            pass
        await asyncio.sleep(600)

async def main():
    app = web.Application()
    app.router.add_get("/", healthcheck)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    asyncio.create_task(self_ping())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
