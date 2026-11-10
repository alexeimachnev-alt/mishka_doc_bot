import io
import os
from PIL import Image, ImageDraw, ImageFont
import pypdf
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit

# ==============================================================================
# НАСТРОЙКА И РЕГИСТРАЦИЯ ШРИФТОВ (TIMES NEW ROMAN & ARIAL)
# ==============================================================================
FONT_FILE_SERIF = "times.ttf" if os.path.exists("times.ttf") else "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
FONT_FILE_SERIF_BOLD = "timesbd.ttf" if os.path.exists("timesbd.ttf") else "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
FONT_FILE_SANS = "arial.ttf" if os.path.exists("arial.ttf") else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FONT_FILE_BOLD = "arialbd.ttf" if os.path.exists("arialbd.ttf") else "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

pdfmetrics.registerFont(TTFont("Times-Roman-Custom", FONT_FILE_SERIF))
pdfmetrics.registerFont(TTFont("Times-Bold-Custom", FONT_FILE_SERIF_BOLD))
pdfmetrics.registerFont(TTFont("Arial", FONT_FILE_SANS))
pdfmetrics.registerFont(TTFont("Arial-Bold", FONT_FILE_BOLD))


def _resolve_template_path(base_name: str) -> str:
    """Автоматический поиск шаблона (.png или .jpg)."""
    for ext in [".png", ".jpg", ".jpeg"]:
        candidate = f"{base_name}{ext}"
        if os.path.exists(candidate):
            return candidate
    return f"{base_name}.png"


# ==============================================================================
# 1. СЕРТИФИКАТ ДИЛЕРА
# ==============================================================================
def generate_certificate(
    cert_num: str,
    company_name: str,
    inn: str,
    valid_until: str
) -> tuple[io.BytesIO, io.BytesIO]:
    cert_path = _resolve_template_path("cert_template")
    image = Image.open(cert_path).convert("RGB")
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
    dov_path = _resolve_template_path("doverennost_template")
    image = Image.open(dov_path).convert("RGB")
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
# 3. ДИЛЕРСКИЙ ДОГОВОР ПК МИШКА (10 СТРАНИЦ, НОВЫЙ ШАБЛОН)
# ==============================================================================
DILER_DOC_PATH = "diler_dogovor_source.pdf"

def _draw_dealer_block(
    c: canvas.Canvas,
    x_col: float,
    y_header_base: float,
    y_first_line_base: float,
    y_rect_bottom: float,
    y_rect_top: float,
    x_sig_line: float,
    y_sig_base: float,
    req_lines: list[str],
    dealer_fio_short: str
):
    """
    Полностью перекрывает желтые выделения в колонке Дилера и блоке подписи,
    затем выводит заголовок «Дилер», реквизиты (с автопереносом строк) и подпись
    оригинальным шрифтом Times New Roman (10.08 pt).
    """
    # 1. Закрашиваем всю желтую зону реквизитов и заголовка «Дилер»
    c.setFillColorRGB(1, 1, 1)
    c.rect(x_col - 1.5, y_rect_bottom - 2.0, 266.0, (y_rect_top - y_rect_bottom) + 4.0, fill=1, stroke=0)

    # 2. Заголовок «Дилер» (Times-Bold, 10.08 pt)
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Times-Bold-Custom", 10.08)
    c.drawString(x_col, y_header_base, "Дилер")

    # 3. Разбиваем строки реквизитов с учетом ширины колонки (252 pt)
    wrapped_lines = []
    max_width = 252.0
    for idx, raw_line in enumerate(req_lines):
        text_line = raw_line.strip()
        if not text_line:
            continue
        parts = simpleSplit(text_line, "Times-Roman-Custom", 10.08, max_width)
        wrapped_lines.extend(parts)
        # После первой строки (наименования/ФИО дилера) делаем небольшой отступ, как в оригинале
        if idx == 0 and len(req_lines) <= 9:
            wrapped_lines.append("")

    # Если строк много (например, паспортные данные + адрес), убираем пустую строку-разделитель
    non_empty_count = len([x for x in wrapped_lines if x])
    if len(wrapped_lines) > 11 and "" in wrapped_lines:
        wrapped_lines.remove("")

    # Подбираем межстрочный интервал, чтобы все строки идеально поместились в блок
    font_size = 10.08
    step_y = 11.52
    if len(wrapped_lines) > 11:
        font_size = 9.5
        step_y = 10.4

    c.setFont("Times-Roman-Custom", font_size)
    curr_y = y_first_line_base
    for w_line in wrapped_lines[:13]:
        if w_line:
            c.drawString(x_col, curr_y, w_line)
        curr_y -= step_y

    # 4. Закрашиваем и вписываем строку подписи Дилера
    c.setFillColorRGB(1, 1, 1)
    c.rect(x_sig_line - 2.0, y_sig_base - 3.5, 140.0, 15.0, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Times-Roman-Custom", 10.08)
    clean_fio = dealer_fio_short.strip().strip("/").strip()
    c.drawString(x_sig_line, y_sig_base, f"___________/ {clean_fio} /")


def generate_diler_contract(
    contract_num: str,
    contract_date: str,
    dealer_name: str,
    dealer_preamble: str,
    dealer_fio_short: str,
    dealer_address: str = "",
    dealer_inn_kpp: str = "",
    dealer_rs: str = "",
    dealer_ks: str = "",
    dealer_bank: str = "",
    dealer_bik: str = "",
    dealer_phone: str = "",
    custom_req_lines: list[str] | None = None
) -> io.BytesIO:
    source_path = DILER_DOC_PATH
    if not os.path.exists(source_path) and os.path.exists("Дилерский договор ПК МИШКА .pdf"):
        source_path = "Дилерский договор ПК МИШКА .pdf"

    writer = pypdf.PdfWriter(clone_from=source_path)

    clean_num = contract_num.strip().lstrip("№").strip()
    clean_date = contract_date.strip()

    if custom_req_lines is not None:
        req_lines = custom_req_lines
    else:
        req_lines = [
            dealer_name.strip(),
            f"Адрес: {dealer_address.strip()}" if not dealer_address.strip().lower().startswith("адрес") else dealer_address.strip(),
            f"ИНН/КПП: {dealer_inn_kpp.strip()}",
            f"Расчетный счет: {dealer_rs.strip()}",
            f"Кор. счет: {dealer_ks.strip()}",
            f"Банк: {dealer_bank.strip()}",
            f"БИК: {dealer_bik.strip()}",
            f"Тел.: {dealer_phone.strip()}"
        ]

    for page_idx in range(len(writer.pages)):
        page = writer.pages[page_idx]
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=A4)

        if page_idx == 0:
            # 1. Номер договора (желтый блок [310.32, 775.2, 349.44, 789.12])
            c.setFillColorRGB(1, 1, 1)
            c.rect(309.0, 773.5, 90.0, 17.5, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Times-Bold-Custom", 12.0)
            c.drawString(310.37, 777.84, f"№{clean_num}")

            # 2. Дата договора (желтый блок [398.88, 761.04, 510.72, 773.04])
            c.setFillColorRGB(1, 1, 1)
            c.rect(396.0, 759.0, 150.0, 16.0, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Times-Roman-Custom", 10.56)
            c.drawString(398.88, 763.20, clean_date)

            # 3. Преамбула (желтый блок [64.32, 672.72, 234.72, 685.68] + черная линия подчеркивания)
            c.setFillColorRGB(1, 1, 1)
            c.rect(62.0, 670.5, 485.0, 17.5, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)

            preamble_part = dealer_preamble.strip().strip(",")
            if preamble_part:
                full_preamble_line = f'{dealer_name.strip()}, {preamble_part}, именуемый в дальнейшем "Дилер", с другой стороны,'
            else:
                full_preamble_line = f'{dealer_name.strip()}, именуемый в дальнейшем "Дилер", с другой стороны,'

            # Автоматический подбор размера шрифта (от 11.04 до 8.5 pt), чтобы строка легла ровно в одну линию
            p_size = 11.04
            while p_size > 8.0 and pdfmetrics.stringWidth(full_preamble_line, "Times-Roman-Custom", p_size) > 472.0:
                p_size -= 0.2

            c.setFont("Times-Roman-Custom", p_size)
            c.drawString(63.77, 675.36, full_preamble_line)

        elif page_idx == 5:
            # Стр. 6: Приложение №1 (желтые блоки [73.44, 729.84, 553.92, 754.80])
            c.setFillColorRGB(1, 1, 1)
            c.rect(72.0, 728.0, 485.0, 28.5, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Times-Roman-Custom", 11.04)
            c.drawString(74.87, 744.72, f"к дилерскому договору № {clean_num} от {clean_date}")

        elif page_idx == 6:
            # Стр. 7: Реквизиты и подпись к Приложению №1
            _draw_dealer_block(
                c=c,
                x_col=294.0,
                y_header_base=782.64,
                y_first_line_base=769.68,
                y_rect_bottom=653.5,
                y_rect_top=792.5,
                x_sig_line=416.78,
                y_sig_base=573.12,
                req_lines=req_lines,
                dealer_fio_short=dealer_fio_short
            )

        elif page_idx == 7:
            # Стр. 8: Приложение №2 (Шапка + Реквизиты + Подпись)
            # 1. Шапка Приложения №2 (желтый блок [73.44, 714.48, 553.92, 726.48])
            c.setFillColorRGB(1, 1, 1)
            c.rect(72.0, 713.0, 485.0, 15.0, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Times-Roman-Custom", 11.04)
            c.drawString(74.87, 717.12, f"к Дилерскому договору № {clean_num} от {clean_date}")

            # 2. Реквизиты и подпись Дилера на стр. 8
            _draw_dealer_block(
                c=c,
                x_col=294.0,
                y_header_base=468.72,
                y_first_line_base=455.76,
                y_rect_bottom=339.5,
                y_rect_top=478.5,
                x_sig_line=416.78,
                y_sig_base=259.20,
                req_lines=req_lines,
                dealer_fio_short=dealer_fio_short
            )

        elif page_idx == 8:
            # Стр. 9: Приложение №3 (желтые блоки [73.44, 764.88, 553.92, 787.20])
            c.setFillColorRGB(1, 1, 1)
            c.rect(72.0, 763.5, 485.0, 25.0, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Times-Roman-Custom", 11.04)
            c.drawString(74.87, 778.32, f"к Дилерскому договору № {clean_num} от {clean_date}")

        elif page_idx == 9:
            # Стр. 10: Реквизиты и подпись к Приложению №3
            _draw_dealer_block(
                c=c,
                x_col=286.56,
                y_header_base=753.36,
                y_first_line_base=740.40,
                y_rect_bottom=624.0,
                y_rect_top=763.2,
                x_sig_line=409.34,
                y_sig_base=543.84,
                req_lines=req_lines,
                dealer_fio_short=dealer_fio_short
            )

        c.showPage()
        c.save()
        packet.seek(0)

        overlay_pdf = pypdf.PdfReader(packet)
        page.merge_page(overlay_pdf.pages[0])

    final_buffer = io.BytesIO()
    writer.write(final_buffer)
    final_buffer.seek(0)
    return final_buffer
