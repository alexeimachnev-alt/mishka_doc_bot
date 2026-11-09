import io
from PIL import Image, ImageDraw, ImageFont

DOV_TEMPLATE_PATH = "doverennost_template.png"
FONT_FILE_SANS = "arial.ttf"
FONT_FILE_BOLD = "arialbd.ttf"

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
    """Генерация доверенности М-2 с точным выравниванием ячеек таблицы"""
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
    draw.text((310, 342), supplier.strip(), font=font_small, fill=COLOR_BLACK, anchor="mm")

    # 2. Основная часть (шапка и реквизиты)
    draw.text((750, 545), 'ООО "ПК МИШКА"', font=font_main, fill=COLOR_BLACK, anchor="mm")
    draw.text((460, 625), number.strip(), font=font_bold, fill=COLOR_BLACK, anchor="lm")
    draw.text((475, 672), date_issue.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")
    draw.text((475, 705), date_valid.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")
    draw.text((900, 965), fio.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")

    # Паспортные данные
    draw.text((430, 1008), passport_series.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")
    draw.text((720, 1008), passport_number.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")
    draw.text((430, 1038), passport_issued_by.strip(), font=font_small, fill=COLOR_BLACK, anchor="lm")
    draw.text((430, 1068), passport_date.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")

    # Поставщик и основание
    draw.text((430, 1108), supplier.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")
    draw.text((430, 1138), bill_info.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")

    # 3. ТАБЛИЦА ТОВАРОВ (Ровно по центру каждой ячейки)
    # Высоты строк (Y-центры ячеек между горизонтальными линиями):
    row_centers_y = [1416, 1444, 1472, 1500]

    # Координаты колонок:
    COL_NUM_X = 152    # Центр колонки 1 (Номер по порядку)
    COL_NAME_X = 225   # Левый край колонки 2 (+ паддинг от линии)
    COL_UNIT_X = 999   # Центр колонки 3 (Единица измерения)
    COL_QTY_X = 1263   # Центр колонки 4 (Количество)
    MAX_NAME_WIDTH = 680  # Максимальная ширина текста названия (918 - 225 - 13)

    for idx, item in enumerate(items[:4]):
        name, unit, qty = item
        y = row_centers_y[idx]

        # Автоподбор размера шрифта под длину наименования
        font_name = font_table_default
        name_str = name.strip()
        font_size = 21
        while font_size > 13 and draw.textlength(name_str, font=font_name) > MAX_NAME_WIDTH:
            font_size -= 1
            font_name = ImageFont.truetype(FONT_FILE_SANS, size=font_size)

        # Колонка 1: Номер строки (1, 2, 3...)
        draw.text((COL_NUM_X, y), str(idx + 1), font=font_table_default, fill=COLOR_BLACK, anchor="mm")

        # Колонка 2: Наименование товара (выравнивание по левому краю с паддингом)
        draw.text((COL_NAME_X, y), name_str, font=font_name, fill=COLOR_BLACK, anchor="lm")

        # Колонка 3: Единица измерения (точно по центру ячейки)
        draw.text((COL_UNIT_X, y), unit.strip(), font=font_table_default, fill=COLOR_BLACK, anchor="mm")

        # Колонка 4: Количество (точно по центру ячейки)
        draw.text((COL_QTY_X, y), str(qty).strip(), font=font_table_default, fill=COLOR_BLACK, anchor="mm")

    # Выгрузка
    jpg_buf = io.BytesIO()
    image.save(jpg_buf, format="JPEG", quality=95)
    jpg_buf.seek(0)

    pdf_buf = io.BytesIO()
    image.save(pdf_buf, format="PDF", resolution=200.0)
    pdf_buf.seek(0)

    return jpg_buf, pdf_buf
