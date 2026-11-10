import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Регистрация шрифтов с поддержкой кириллицы
FONT_SANS = "arial.ttf" if os.path.exists("arial.ttf") else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FONT_BOLD = "arialbd.ttf" if os.path.exists("arialbd.ttf") else "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

pdfmetrics.registerFont(TTFont("Arial", FONT_SANS))
pdfmetrics.registerFont(TTFont("Arial-Bold", FONT_BOLD))

def generate_doverennost_pdf(data: dict) -> io.BytesIO:
    """Генерирует доверенность М-2 строго в формате PDF с подписями и печатью."""
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    width, height = A4  # 595.27 x 841.89 pt

    # Верхний корешок
    c.setLineWidth(0.75)
    c.rect(36, height - 120, width - 72, 80)
    
    c.setFont("Arial", 8)
    c.drawString(45, height - 55, "Номер дов.")
    c.drawString(100, height - 55, "Дата выдачи")
    c.drawString(170, height - 55, "Срок действия")
    c.drawString(245, height - 55, "Должность и ФИО доверенного лица")
    
    c.setFont("Arial-Bold", 9)
    c.drawString(45, height - 75, data.get('number', '15'))
    c.drawString(100, height - 75, data.get('date_issue', '13.10.2026'))
    c.drawString(170, height - 75, data.get('date_valid', '20.10.2026'))
    c.drawString(245, height - 75, data.get('fio', 'Мамыкин А.К.'))

    # Линия отреза
    c.setDash([3, 3], 0)
    c.line(36, height - 140, width - 36, height - 140)
    c.setDash([], 0)

    # Заголовок формы
    c.setFont("Arial", 8)
    c.drawString(36, height - 160, "Типовая межотраслевая форма № М-2")
    c.drawString(36, height - 172, "Утверждена постановлением Госкомстата России от 30.10.97 № 71а")
    
    # Таблица кодов справа
    c.rect(width - 160, height - 180, 124, 30)
    c.drawString(width - 150, height - 160, "Форма по ОКУД")
    c.drawString(width - 80, height - 160, "0315001")

    # Организация
    c.setFont("Arial", 10)
    c.drawString(36, height - 210, "Организация: ООО «ПК МИШКА»")
    
    # Номер доверенности
    c.setFont("Arial-Bold", 12)
    c.drawString(200, height - 235, f"ДОВЕРЕННОСТЬ № {data.get('number', '15')}")

    # Даты
    c.setFont("Arial", 10)
    c.drawString(36, height - 260, f"Дата выдачи: {data.get('date_issue', '13.10.2026')}")
    c.drawString(36, height - 280, f"Доверенность действительна по: {data.get('date_valid', '20.10.2026')}")

    # Адреса
    addr = "11524, г. Москва, ВН.ТЕР.Г. Муниципальный округ Перово, ул. Электродная, д. 11, этаж 4, пом. 10"
    c.setFont("Arial", 9)
    c.drawString(36, height - 310, f"Потребитель: {addr}")
    c.drawString(36, height - 330, f"Плательщик: {addr}")

    # Данные сотрудника
    c.drawString(36, height - 365, f"Доверенность выдана: {data.get('fio_job', 'экспедитор')} — {data.get('fio', 'Мамыкин Алексей Константинович')}")
    c.drawString(36, height - 385, f"Паспорт: серия {data.get('passport_series', '4621')} № {data.get('passport_number', '22318')}")
    c.drawString(36, height - 405, f"Кем выдан: {data.get('passport_issued_by', 'ГУ МВД России по Московской области')} от {data.get('passport_date', '24.02.2021')}")

    # Поставщик
    c.drawString(36, height - 435, f"На получение от: {data.get('supplier', 'ООО «СТАИРС ПРОФИ»')}")

    # Таблица ТМЦ
    c.setFont("Arial-Bold", 9)
    c.drawString(width / 2 - 120, height - 475, "Перечень товарно-материальных ценностей")

    y_table = height - 500
    c.rect(36, y_table - 20, width - 72, 20)
    c.setFont("Arial", 8)
    c.drawString(45, y_table - 14, "№")
    c.drawString(80, y_table - 14, "Наименование материальных ценностей")
    c.drawString(width - 150, y_table - 14, "Ед. изм.")
    c.drawString(width - 90, y_table - 14, "Количество")

    # Строки товаров
    items = data.get('items', [("Лестница односекционная приставная 08 ступеней", "шт", "100")])
    for idx, item in enumerate(items):
        y_row = y_table - 20 - (idx + 1) * 20
        c.rect(36, y_row, width - 72, 20)
        c.drawString(45, y_row + 6, str(idx + 1))
        c.drawString(80, y_row + 6, item[0])
        c.drawString(width - 150, y_row + 6, item[1])
        c.drawString(width - 90, y_row + 6, str(item[2]))

    # Подписи и печать
    y_sig = 180
    c.setFont("Arial", 10)
    c.drawString(36, y_sig + 40, "Руководитель")
    c.line(130, y_sig + 40, 260, y_sig + 40)
    c.drawString(320, y_sig + 40, "Хачатрян А.Р.")

    c.drawString(36, y_sig, "Главный бухгалтер")
    c.line(130, y_sig, 260, y_sig)
    c.drawString(320, y_sig, "Хачатрян А.Р.")

    # Вставка печати и подписей, если файлы изображений существуют
    if os.path.exists("extracted_img/image_0.png"):
        c.drawImage("extracted_img/image_0.png", 220, y_sig - 30, width=90, height=90, mask='auto')
    if os.path.exists("extracted_img/image_1.png"):
        c.drawImage("extracted_img/image_1.png", 140, y_sig + 35, width=90, height=35, mask='auto')
    if os.path.exists("extracted_img/image_2.png"):
        c.drawImage("extracted_img/image_2.png", 140, y_sig - 5, width=90, height=35, mask='auto')

    c.showPage()
    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer
