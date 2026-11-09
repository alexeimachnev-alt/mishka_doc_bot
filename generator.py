import io
from PIL import Image, ImageDraw, ImageFont

# ==============================================================================
# НАСТРОЙКИ СТИЛЯ СЕРТИФИКАТА ДИЛЕРА
# ==============================================================================
CERT_TEMPLATE_PATH = "cert_template.png"
FONT_FILE_SERIF = "times.ttf"       # Для номера сертификата в шапке
FONT_FILE_SANS = "arial.ttf"        # Для названия компании и ИНН
FONT_FILE_BOLD = "arialbd.ttf"      # Для даты

SIZE_CERT_NUM = 42
SIZE_COMPANY  = 52
SIZE_INN      = 38
SIZE_DATE     = 40

COLOR_CERT_NUM = (110, 128, 150)
COLOR_MAIN     = (27, 46, 75)

Y_CERT_NUM = 242
Y_COMPANY  = 445
Y_INN      = 560
Y_DATE     = 893
X_DATE     = 970

def generate_certificate(
    cert_num: str,
    company_name: str,
    inn: str,
    valid_until: str
) -> tuple[io.BytesIO, io.BytesIO]:
    """Генерация сертификата дилера (JPG и PDF)"""
    image = Image.open(CERT_TEMPLATE_PATH).convert("RGB")
    draw = ImageDraw.Draw(image)
    width, _ = image.size

    font_num = ImageFont.truetype(FONT_FILE_SERIF, size=SIZE_CERT_NUM)
    font_company = ImageFont.truetype(FONT_FILE_SANS, size=SIZE_COMPANY)
    font_inn = ImageFont.truetype(FONT_FILE_SANS, size=SIZE_INN)
    font_date = ImageFont.truetype(FONT_FILE_BOLD, size=SIZE_DATE)

    clean_num = cert_num.strip()
    if not clean_num.startswith("№"):
        clean_num = f"№{clean_num}"
    draw.text((width / 2, Y_CERT_NUM), clean_num, font=font_num, fill=COLOR_CERT_NUM, anchor="mm")
    draw.text((width / 2, Y_COMPANY), company_name.strip(), font=font_company, fill=COLOR_MAIN, anchor="mm")

    clean_inn = inn.strip()
    if not clean_inn.upper().startswith("ИНН"):
        clean_inn = f"ИНН:{clean_inn}"
    draw.text((width / 2, Y_INN), clean_inn, font=font_inn, fill=COLOR_MAIN, anchor="mm")
    draw.text((X_DATE, Y_DATE), valid_until.strip(), font=font_date, fill=COLOR_MAIN, anchor="lm")

    jpg_buf = io.BytesIO()
    image.save(jpg_buf, format="JPEG", quality=95)
    jpg_buf.seek(0)

    pdf_buf = io.BytesIO()
    image.save(pdf_buf, format="PDF", resolution=150.0)
    pdf_buf.seek(0)

    return jpg_buf, pdf_buf


# ==============================================================================
# НАСТРОЙКИ ДОВЕРЕННОСТИ М-2
# ==============================================================================
DOV_TEMPLATE_PATH = "doverennost_template.png"

def generate_doverennost(
    number: str,
    date_issue: str,
    date_valid: str,
    fio: str,
    supplier: str,
    passport_series: str,
    passport_number: str,
    passport_issued_by: str,
    passport_date: str,
    bill_info: str,
    items: list[tuple[str, str, str]]
) -> tuple[io.BytesIO, io.BytesIO]:
    """Генерация доверенности М-2 с автоматическим заполнением повторяющихся полей"""
    image = Image.open(DOV_TEMPLATE_PATH).convert("RGB")
    draw = ImageDraw.Draw(image)

    font_main = ImageFont.truetype(FONT_FILE_SANS, size=24)
    font_bold = ImageFont.truetype(FONT_FILE_BOLD, size=28)
    font_small = ImageFont.truetype(FONT_FILE_SANS, size=20)
    COLOR_BLACK = (0, 0, 0)

    # 1. Заполнение отрывного корешка (вверху слева)
    draw.text((190, 205), number, font=font_main, fill=COLOR_BLACK, anchor="mm")
    draw.text((365, 205), date_issue, font=font_main, fill=COLOR_BLACK, anchor="mm")
    draw.text((555, 205), date_valid, font=font_main, fill=COLOR_BLACK, anchor="mm")
    draw.text((940, 205), fio, font=font_small, fill=COLOR_BLACK, anchor="mm")
    draw.text((310, 342), supplier, font=font_main, fill=COLOR_BLACK, anchor="mm")

    # 2. Заполнение основной части (повторяющиеся поля подставляются автоматически)
    draw.text((750, 545), 'ООО "ПК МИШКА"', font=font_main, fill=COLOR_BLACK, anchor="mm")
    draw.text((750, 625), number, font=font_bold, fill=COLOR_BLACK, anchor="mm")
    draw.text((475, 672), date_issue, font=font_main, fill=COLOR_BLACK, anchor="lm")
    draw.text((475, 705), date_valid, font=font_main, fill=COLOR_BLACK, anchor="lm")
    draw.text((900, 965), fio, font=font_main, fill=COLOR_BLACK, anchor="lm")

    # Паспортные данные
    draw.text((430, 1008), passport_series, font=font_main, fill=COLOR_BLACK, anchor="lm")
    draw.text((720, 1008), passport_number, font=font_main, fill=COLOR_BLACK, anchor="lm")
    draw.text((430, 1038), passport_issued_by, font=font_small, fill=COLOR_BLACK, anchor="lm")
    draw.text((430, 1068), passport_date, font=font_main, fill=COLOR_BLACK, anchor="lm")

    # Поставщик и основание
    draw.text((430, 1108), supplier, font=font_main, fill=COLOR_BLACK, anchor="lm")
    draw.text((430, 1138), bill_info, font=font_main, fill=COLOR_BLACK, anchor="lm")

    # 3. Таблица ТМЦ (до 4 строк)
    row_y = [1428, 1458, 1488, 1518]
    for idx, item in enumerate(items[:4]):
        name, unit, qty = item
        y = row_y[idx]
        draw.text((220, y), name, font=font_small, fill=COLOR_BLACK, anchor="lm")
        draw.text((1000, y), unit, font=font_small, fill=COLOR_BLACK, anchor="mm")
        draw.text((1280, y), str(qty), font=font_small, fill=COLOR_BLACK, anchor="mm")

    jpg_buf = io.BytesIO()
    image.save(jpg_buf, format="JPEG", quality=95)
    jpg_buf.seek(0)

    pdf_buf = io.BytesIO()
    image.save(pdf_buf, format="PDF", resolution=200.0)
    pdf_buf.seek(0)

    return jpg_buf, pdf_buf
