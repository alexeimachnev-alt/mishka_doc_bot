import io
from PIL import Image, ImageDraw, ImageFont

# ==============================================================================
# 1. СЕРТИФИКАТ ДИЛЕРА
# ==============================================================================
CERT_TEMPLATE_PATH = "cert_template.png"

FONT_FILE_SERIF = "times.ttf"
FONT_FILE_SANS = "arial.ttf"
FONT_FILE_BOLD = "arialbd.ttf"

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
    """Генерация сертификата дилера"""
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
# 2. ДОВЕРЕННОСТЬ М-2 (С ВЫВЕРЕННЫМИ КООРДИНАТАМИ ТАБЛИЦЫ)
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
    """Генерация доверенности М-2 с автоподбором шрифта и ровными ячейками"""
    image = Image.open(DOV_TEMPLATE_PATH).convert("RGB")
    draw = ImageDraw.Draw(image)

    font_main = ImageFont.truetype(FONT_FILE_SANS, size=24)
    font_bold = ImageFont.truetype(FONT_FILE_BOLD, size=28)
    font_small = ImageFont.truetype(FONT_FILE_SANS, size=20)
    font_table_default = ImageFont.truetype(FONT_FILE_SANS, size=21)
    COLOR_BLACK = (0, 0, 0)

    # 1. Отрывной корешок (слева вверху)
    draw.text((152, 205), number.strip(), font=font_main, fill=COLOR_BLACK, anchor="mm")
    draw.text((290, 205), date_issue.strip(), font=font_small, fill=COLOR_BLACK, anchor="mm")
    draw.text((430, 205), date_valid.strip(), font=font_small, fill=COLOR_BLACK, anchor="mm")
    draw.text((940, 205), fio.strip(), font=font_small, fill=COLOR_BLACK, anchor="mm")
    draw.text((310, 342), supplier.strip(), font=font_main, fill=COLOR_BLACK, anchor="mm")

    # 2. Основная часть (шапка и паспортные данные)
    draw.text((750, 545), 'ООО "ПК МИШКА"', font=font_main, fill=COLOR_BLACK, anchor="mm")
    draw.text((460, 625), number.strip(), font=font_bold, fill=COLOR_BLACK, anchor="lm")
    draw.text((475, 672), date_issue.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")
    draw.text((475, 705), date_valid.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")
    draw.text((900, 965), fio.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")

    draw.text((430, 1008), passport_series.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")
    draw.text((720, 1008), passport_number.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")
    draw.text((430, 1038), passport_issued_by.strip(), font=font_small, fill=COLOR_BLACK, anchor="lm")
    draw.text((430, 1068), passport_date.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")

    draw.text((430, 1108), supplier.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")
    draw.text((430, 1138), bill_info.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")

    # 3. Таблица товаров (высота каждой строки ровно 28px)
    row_centers_y = [1416, 1444, 1472, 1500]

    COL_NUM_X = 152      # Центр колонки 1 (№ п/п)
    COL_NAME_X = 225     # Левый край колонки 2 (Наименование товара)
    COL_UNIT_X = 999     # Центр колонки 3 (Единица измерения)
    COL_QTY_X = 1263     # Центр колонки 4 (Количество)
    MAX_NAME_WIDTH = 680

    for idx, item in enumerate(items[:4]):
        name, unit, qty = item
        y = row_centers_y[idx]

        # Автоподбор размера, чтобы длинное название не заходило за границы ячейки
        font_name = font_table_default
        name_str = name.strip()
        font_size = 21
        while font_size > 13 and draw.textlength(name_str, font=font_name) > MAX_NAME_WIDTH:
            font_size -= 1
            font_name = ImageFont.truetype(FONT_FILE_SANS, size=font_size)

        draw.text((COL_NUM_X, y), str(idx + 1), font=font_table_default, fill=COLOR_BLACK, anchor="mm")
        draw.text((COL_NAME_X, y), name_str, font=font_name, fill=COLOR_BLACK, anchor="lm")
        draw.text((COL_UNIT_X, y), unit.strip(), font=font_table_default, fill=COLOR_BLACK, anchor="mm")
        draw.text((COL_QTY_X, y), str(qty).strip(), font=font_table_default, fill=COLOR_BLACK, anchor="mm")

    jpg_buf = io.BytesIO()
    image.save(jpg_buf, format="JPEG", quality=95)
    jpg_buf.seek(0)

    pdf_buf = io.BytesIO()
    image.save(pdf_buf, format="PDF", resolution=200.0)
    pdf_buf.seek(0)

    return jpg_buf, pdf_buf
