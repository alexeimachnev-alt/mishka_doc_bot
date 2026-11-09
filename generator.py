import io
from PIL import Image, ImageDraw, ImageFont

# ========================================================
# НАСТРОЙКИ СТИЛЯ (ШРИФТЫ, РАЗМЕРЫ, ЦВЕТА И КООРДИНАТЫ)
# ========================================================
TEMPLATE_PATH = "cert_template.png"

# 1. Файлы шрифтов
FONT_FILE_SERIF = "times.ttf"       # Для номера сертификата в шапке
FONT_FILE_SANS = "arial.ttf"        # Для названия компании и ИНН
FONT_FILE_BOLD = "arialbd.ttf"      # Для даты

# 2. Размеры шрифтов (можно менять под себя)
SIZE_CERT_NUM = 42      # Размер номера сертификата
SIZE_COMPANY  = 52      # Размер названия компании
SIZE_INN      = 38      # Размер ИНН
SIZE_DATE     = 40      # Размер даты окончания

# 3. Цвета текста (в формате RGB)
COLOR_CERT_NUM = (110, 128, 150)   # Приглушенный серо-голубой на синей плашке
COLOR_MAIN     = (27, 46, 75)      # Темно-синий для основного текста

# 4. Координаты (Y - высота по вертикали)
Y_CERT_NUM = 242   # Центр синей плашки
Y_COMPANY  = 445   # Строка компании
Y_INN      = 560   # Строка ИНН
Y_DATE     = 893   # Строка даты
X_DATE     = 970   # Начало даты (справа от текста)
# ========================================================


def generate_certificate(
    cert_num: str,
    company_name: str,
    inn: str,
    valid_until: str
) -> tuple[io.BytesIO, io.BytesIO]:
    """
    Генерирует сертификат и возвращает (jpg_stream, pdf_stream)
    """
    image = Image.open(TEMPLATE_PATH).convert("RGB")
    draw = ImageDraw.Draw(image)
    width, _ = image.size

    # Загрузка шрифтов с заданными размерами
    font_num = ImageFont.truetype(FONT_FILE_SERIF, size=SIZE_CERT_NUM)
    font_company = ImageFont.truetype(FONT_FILE_SANS, size=SIZE_COMPANY)
    font_inn = ImageFont.truetype(FONT_FILE_SANS, size=SIZE_INN)
    font_date = ImageFont.truetype(FONT_FILE_BOLD, size=SIZE_DATE)

    # 1. Номер сертификата (по центру)
    clean_num = cert_num.strip()
    if not clean_num.startswith("№"):
        clean_num = f"№{clean_num}"
    draw.text((width / 2, Y_CERT_NUM), clean_num, font=font_num, fill=COLOR_CERT_NUM, anchor="mm")

    # 2. Название компании (по центру)
    draw.text((width / 2, Y_COMPANY), company_name.strip(), font=font_company, fill=COLOR_MAIN, anchor="mm")

    # 3. ИНН (по центру)
    clean_inn = inn.strip()
    if not clean_inn.upper().startswith("ИНН"):
        clean_inn = f"ИНН:{clean_inn}"
    draw.text((width / 2, Y_INN), clean_inn, font=font_inn, fill=COLOR_MAIN, anchor="mm")

    # 4. Срок действия (по левому краю от X_DATE)
    draw.text((X_DATE, Y_DATE), valid_until.strip(), font=font_date, fill=COLOR_MAIN, anchor="lm")

    # Сохранение в JPG
    jpg_buffer = io.BytesIO()
    image.save(jpg_buffer, format="JPEG", quality=95)
    jpg_buffer.seek(0)

    # Сохранение в PDF
    pdf_buffer = io.BytesIO()
    image.save(pdf_buffer, format="PDF", resolution=150.0)
    pdf_buffer.seek(0)

    return jpg_buffer, pdf_buffer
