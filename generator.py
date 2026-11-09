import io
from PIL import Image, ImageDraw, ImageFont
import pypdf
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Регистрируем шрифты для векторной накладки ReportLab
pdfmetrics.registerFont(TTFont("Arial", "arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", "arialbd.ttf"))

# ==============================================================================
# 1. СЕРТИФИКАТ ДИЛЕРА
# ==============================================================================
CERT_TEMPLATE_PATH = "cert_template.png"

FONT_FILE_SERIF = "times.ttf"
FONT_FILE_SANS = "arial.ttf"
FONT_FILE_BOLD = "arialbd.ttf"

def generate_certificate(
    cert_num: str,
    company_name: str,
    inn: str,
    valid_until: str
) -> tuple[io.BytesIO, io.BytesIO]:
    image = Image.open(CERT_TEMPLATE_PATH).convert("RGB")
    draw = ImageDraw.Draw(image)
    width, _ = image.size

    font_num = ImageFont.truetype(FONT_FILE_SERIF, size=42)
    font_company = ImageFont.truetype(FONT_FILE_SANS, size=52)
    font_inn = ImageFont.truetype(FONT_FILE_SANS, size=38)
    font_date = ImageFont.truetype(FONT_FILE_BOLD, size=40)

    clean_num = cert_num.strip()
    if not clean_num.startswith("№"):
        clean_num = f"№{clean_num}"
    draw.text((width / 2, 242), clean_num, font=font_num, fill=(110, 128, 150), anchor="mm")
    draw.text((width / 2, 445), company_name.strip(), font=font_company, fill=(27, 46, 75), anchor="mm")

    clean_inn = inn.strip()
    if not clean_inn.upper().startswith("ИНН"):
        clean_inn = f"ИНН:{clean_inn}"
    draw.text((width / 2, 560), clean_inn, font=font_inn, fill=(27, 46, 75), anchor="mm")
    draw.text((970, 893), valid_until.strip(), font=font_date, fill=(27, 46, 75), anchor="lm")

    jpg_buf = io.BytesIO()
    image.save(jpg_buf, format="JPEG", quality=95)
    jpg_buf.seek(0)

    pdf_buf = io.BytesIO()
    image.save(pdf_buf, format="PDF", resolution=150.0)
    pdf_buf.seek(0)

    return jpg_buf, pdf_buf


# ==============================================================================
# 2. ДОВЕРЕННОСТЬ М-2 (ТОЧНЫЕ КООРДИНАТЫ ЯЧЕЕК И ШАПКИ)
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
    image = Image.open(DOV_TEMPLATE_PATH).convert("RGB")
    draw = ImageDraw.Draw(image)

    font_main = ImageFont.truetype(FONT_FILE_SANS, size=24)
    font_bold = ImageFont.truetype(FONT_FILE_BOLD, size=28)
    font_small = ImageFont.truetype(FONT_FILE_SANS, size=20)
    font_table_default = ImageFont.truetype(FONT_FILE_SANS, size=21)
    COLOR_BLACK = (0, 0, 0)

    # 1. Отрывной корешок (слева вверху) — центры колонок: 184, 360, 551, 906
    draw.text((184, 205), number.strip(), font=font_main, fill=COLOR_BLACK, anchor="mm")
    draw.text((360, 205), date_issue.strip(), font=font_main, fill=COLOR_BLACK, anchor="mm")
    draw.text((551, 205), date_valid.strip(), font=font_main, fill=COLOR_BLACK, anchor="mm")
    draw.text((906, 205), fio.strip(), font=font_small, fill=COLOR_BLACK, anchor="mm")
    draw.text((311, 342), supplier.strip(), font=font_main, fill=COLOR_BLACK, anchor="mm")

    # 2. Основная часть (шапка и реквизиты)
    draw.text((750, 545), 'ООО "ПК МИШКА"', font=font_main, fill=COLOR_BLACK, anchor="mm")
    # Номер смещен правее слова "ДОВЕРЕННОСТЬ №"
    draw.text((720, 625), number.strip(), font=font_bold, fill=COLOR_BLACK, anchor="lm")
    draw.text((475, 672), date_issue.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")
    draw.text((475, 703), date_valid.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")
    draw.text((900, 965), fio.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")

    # Паспортные данные
    draw.text((430, 1008), passport_series.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")
    draw.text((720, 1008), passport_number.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")
    draw.text((430, 1038), passport_issued_by.strip(), font=font_small, fill=COLOR_BLACK, anchor="lm")
    draw.text((430, 1068), passport_date.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")

    # Поставщик и основание
    draw.text((430, 1108), supplier.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")
    draw.text((430, 1138), bill_info.strip(), font=font_main, fill=COLOR_BLACK, anchor="lm")

    # 3. Таблица товаров (строки 1, 2, 3, 4)
    row_centers_y = [1416, 1444, 1472, 1500]

    COL_NAME_X = 225     # Отступ в графе наименования
    COL_UNIT_X = 999     # Центр колонки единиц измерения
    COL_QTY_X = 1263     # Центр колонки количества
    MAX_NAME_WIDTH = 680

    for idx, item in enumerate(items[:4]):
        name, unit, qty = item
        y = row_centers_y[idx]

        # Автоподбор размера шрифта под длину текста
        font_name = font_table_default
        name_str = name.strip()
        font_size = 21
        while font_size > 13 and draw.textlength(name_str, font=font_name) > MAX_NAME_WIDTH:
            font_size -= 1
            font_name = ImageFont.truetype(FONT_FILE_SANS, size=font_size)

        # Номера строк не рисуем (1, 2, 3, 4 уже присутствуют на бланке)
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


# ==============================================================================
# 3. ДИЛЕРСКИЙ ДОГОВОР ПК МИШКА (11 СТРАНИЦ)
# ==============================================================================
DILER_DOC_PATH = "diler_dogovor_source.pdf"

def generate_diler_contract(
    contract_num: str,
    contract_date: str,
    dealer_name: str,
    dealer_preamble: str,
    dealer_fio_short: str,
    dealer_address: str,
    dealer_inn_kpp: str,
    dealer_rs: str,
    dealer_ks: str,
    dealer_bank: str,
    dealer_bik: str,
    dealer_phone: str
) -> io.BytesIO:
    """Генерация 11-страничного Дилерского договора с заполнением всех 3 мест реквизитов дилера"""
    orig_reader = pypdf.PdfReader(DILER_DOC_PATH)
    output = pypdf.PdfWriter()

    # Формируем строки реквизитов (по образцу ООО "ПК Мишка")
    req_lines = [
        dealer_name.strip(),
        dealer_address.strip(),
        f"ИНН/КПП: {dealer_inn_kpp.strip()}",
        f"Р/с: {dealer_rs.strip()}",
        f"к/с: {dealer_ks.strip()}",
        f"Банк: {dealer_bank.strip()}",
        f"БИК: {dealer_bik.strip()}",
        f"Тел.: {dealer_phone.strip()}"
    ]

    for page_idx in range(len(orig_reader.pages)):
        orig_page = orig_reader.pages[page_idx]

        # Создаем накладку для текущей страницы
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=A4)

        if page_idx == 0:
            # --- СТР. 1: Номер, Дата и Преамбула ---
            # Белые плашки поверх желтых меток
            c.setFillColorRGB(1, 1, 1)
            c.rect(320, 770, 80, 20, fill=1, stroke=0)
            c.rect(430, 747, 130, 20, fill=1, stroke=0)
            c.rect(50, 665, 200, 20, fill=1, stroke=0)

            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial-Bold", 11)
            c.drawString(322, 775, f"№{contract_num.strip()}")
            c.setFont("Arial", 10)
            c.drawString(435, 752, contract_date.strip())
            c.setFont("Arial", 9.5)
            c.drawString(55, 670, f"{dealer_name.strip()}, {dealer_preamble.strip()}")

        elif page_idx == 5:
            # --- СТР. 6: Раздел 10 (МЕСТО №1 РЕКВИЗИТОВ ДИЛЕРА) ---
            # Белая плашка поверх большого желтого квадрата
            c.setFillColorRGB(1, 1, 1)
            c.rect(275, 595, 240, 160, fill=1, stroke=0)

            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 8.5)
            y_text = 745
            for line in req_lines:
                c.drawString(280, y_text, line)
                y_text -= 14

            # Подпись дилера
            c.drawString(390, 523, f"/ {dealer_fio_short.strip()} /")

        elif page_idx == 6:
            # --- СТР. 7: Приложение №1 (Шапка) ---
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9)
            c.drawString(235, 769, f"№ {contract_num.strip()}")
            c.drawString(295, 769, contract_date.strip())

        elif page_idx == 7:
            # --- СТР. 8: Приложение №1 (Подпись) ---
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9)
            c.drawString(390, 523, f"/ {dealer_fio_short.strip()} /")

        elif page_idx == 8:
            # --- СТР. 9: Приложение №2 (МЕСТО №2 РЕКВИЗИТОВ ДИЛЕРА) ---
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9)
            c.drawString(235, 769, f"№ {contract_num.strip()}")
            c.drawString(295, 769, contract_date.strip())

            # Вставляем реквизиты дилера справа
            c.setFont("Arial", 8.5)
            y_text = 540
            for line in req_lines:
                c.drawString(280, y_text, line)
                y_text -= 14

            c.drawString(390, 317, f"/ {dealer_fio_short.strip()} /")

        elif page_idx == 9:
            # --- СТР. 10: Приложение №3 (Шапка) ---
            # Белая плашка поверх желтой полосы
            c.setFillColorRGB(1, 1, 1)
            c.rect(70, 735, 450, 22, fill=1, stroke=0)

            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9)
            c.drawString(75, 742, f"к Дилерскому договору № {contract_num.strip()}   от  {contract_date.strip()}")

        elif page_idx == 10:
            # --- СТР. 11: Приложение №3 (МЕСТО №3 РЕКВИЗИТОВ ДИЛЕРА) ---
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 8.5)
            y_text = 680
            for line in req_lines:
                c.drawString(280, y_text, line)
                y_text -= 14

            c.drawString(390, 482, f"/ {dealer_fio_short.strip()} /")

        c.showPage()
        c.save()
        packet.seek(0)

        overlay_pdf = pypdf.PdfReader(packet)
        orig_page.merge_page(overlay_pdf.pages[0])
        output.add_page(orig_page)

    final_buffer = io.BytesIO()
    output.write(final_buffer)
    final_buffer.seek(0)
    return final_buffer
