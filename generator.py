import io
from PIL import Image, ImageDraw, ImageFont
import pypdf
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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
# 2. ДОВЕРЕННОСТЬ М-2
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

    # 1. Отрывной корешок
    draw.text((184, 205), number.strip(), font=font_main, fill=COLOR_BLACK, anchor="mm")
    draw.text((360, 205), date_issue.strip(), font=font_main, fill=COLOR_BLACK, anchor="mm")
    draw.text((551, 205), date_valid.strip(), font=font_main, fill=COLOR_BLACK, anchor="mm")
    draw.text((906, 205), fio.strip(), font=font_small, fill=COLOR_BLACK, anchor="mm")
    draw.text((311, 342), supplier.strip(), font=font_main, fill=COLOR_BLACK, anchor="mm")

    # 2. Основная часть
    draw.text((750, 545), 'ООО "ПК МИШКА"', font=font_main, fill=COLOR_BLACK, anchor="mm")
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

    # 3. Таблица товаров
    row_centers_y = [1416, 1444, 1472, 1500]

    COL_NAME_X = 225
    COL_UNIT_X = 999
    COL_QTY_X = 1263
    MAX_NAME_WIDTH = 680

    for idx, item in enumerate(items[:4]):
        name, unit, qty = item
        y = row_centers_y[idx]

        font_name = font_table_default
        name_str = name.strip()
        font_size = 21
        while font_size > 13 and draw.textlength(name_str, font=font_name) > MAX_NAME_WIDTH:
            font_size -= 1
            font_name = ImageFont.truetype(FONT_FILE_SANS, size=font_size)

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
    # Инициализация клонированием для совместимости с pypdf 7.0+
    writer = pypdf.PdfWriter(clone_from=DILER_DOC_PATH)

    clean_num = contract_num.strip().lstrip("№").strip()

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

    for page_idx in range(len(writer.pages)):
        page = writer.pages[page_idx]
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=A4)

        if page_idx == 0:
            # 1. Номер договора
            c.setFillColorRGB(1, 1, 1)
            c.rect(300, 770, 70, 20, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial-Bold", 11)
            c.drawString(305, 776, clean_num)

            # 2. Дата договора
            c.setFillColorRGB(1, 1, 1)
            c.rect(420, 755, 120, 20, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9.5)
            c.drawString(425, 762, contract_date.strip())

            # 3. Преамбула (перекрываем строку целиком)
            c.setFillColorRGB(1, 1, 1)
            c.rect(60, 668, 475, 20, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9)
            preamble_full = f"{dealer_name.strip()}, {dealer_preamble.strip()},"
            c.drawString(64, 674, preamble_full)
            c.drawString(64 + c.stringWidth(preamble_full, "Arial", 9) + 4, 674, 'именуемая в дальнейшем "Дилер", с другой стороны,')

        elif page_idx == 5:
            # Стр. 6: Место 1 реквизитов дилера
            c.setFillColorRGB(1, 1, 1)
            c.rect(275, 540, 275, 185, fill=1, stroke=0)
            c.rect(290, 425, 250, 35, fill=1, stroke=0)

            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 8.5)
            y_text = 707
            for line in req_lines:
                c.drawString(280, y_text, line)
                y_text -= 14

            c.setFont("Arial", 9.5)
            c.drawString(292, 440, f"директор _______________ / {dealer_fio_short.strip()} /")

        elif page_idx == 6:
            # Стр. 7: Приложение №1 (Шапка)
            c.setFillColorRGB(1, 1, 1)
            c.rect(70, 755, 300, 16, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9.5)
            c.drawString(75, 760, f"к дилерскому договору № {clean_num} от {contract_date.strip()}")

        elif page_idx == 7:
            # Стр. 8: Приложение №1 (Подпись)
            c.setFillColorRGB(1, 1, 1)
            c.rect(290, 510, 250, 30, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9.5)
            c.drawString(292, 526, f"Генеральный директор ____________ / {dealer_fio_short.strip()} /")

        elif page_idx == 8:
            # Стр. 9: Приложение №2
            c.setFillColorRGB(1, 1, 1)
            c.rect(70, 725, 300, 18, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9.5)
            c.drawString(75, 731, f"к Дилерскому договору № {clean_num} от {contract_date.strip()}")

            # Реквизиты дилера
            c.setFillColorRGB(1, 1, 1)
            c.rect(275, 315, 275, 165, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 8.5)
            y_text = 465
            for line in req_lines:
                c.drawString(280, y_text, line)
                y_text -= 14

            # Подпись дилера
            c.setFillColorRGB(1, 1, 1)
            c.rect(290, 235, 250, 30, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9.5)
            c.drawString(292, 247, f"Генеральный директор ____________ / {dealer_fio_short.strip()} /")

        elif page_idx == 9:
            # Стр. 10: Приложение №3 (Шапка над таблицей)
            c.setFillColorRGB(1, 1, 1)
            c.rect(70, 700, 470, 20, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9.5)
            c.drawString(75, 706, f"к Дилерскому договору № {clean_num} от {contract_date.strip()}")

        elif page_idx == 10:
            # Стр. 11: Приложение №3 (Конец)
            c.setFillColorRGB(1, 1, 1)
            c.rect(275, 545, 275, 165, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 8.5)
            y_text = 688
            for line in req_lines:
                c.drawString(280, y_text, line)
                y_text -= 14

            c.setFillColorRGB(1, 1, 1)
            c.rect(250, 470, 290, 30, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9.5)
            c.drawString(254, 483, f"Генеральный директор ____________ / {dealer_fio_short.strip()} /")

        c.showPage()
        c.save()
        packet.seek(0)

        overlay_pdf = pypdf.PdfReader(packet)
        page.merge_page(overlay_pdf.pages[0])

    final_buffer = io.BytesIO()
    writer.write(final_buffer)
    final_buffer.seek(0)
    return final_buffer
