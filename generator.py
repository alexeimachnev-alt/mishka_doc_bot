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
    """Генерация 11-страничного договора с точным позиционированием всех полей"""
    writer = pypdf.PdfWriter(clone_from=DILER_DOC_PATH)

    # Чистим номер от лишнего знака №, если пользователь его ввел
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
            # --- СТР. 1: Номер, Дата и Преамбула ---
            # 1. Закрашиваем старый номер "23940" и желтую плашку
            c.setFillColorRGB(1, 1, 1)
            c.rect(300, 770, 70, 20, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial-Bold", 11)
            c.drawString(305, 776, clean_num)

            # 2. Закрашиваем старую дату и желтый фон
            c.setFillColorRGB(1, 1, 1)
            c.rect(420, 755, 120, 20, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9.5)
            c.drawString(425, 762, contract_date.strip())

            # 3. Закрашиваем строку преамбулы и пишем чисто без наложений
            c.setFillColorRGB(1, 1, 1)
            c.rect(60, 668, 475, 20, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9)
            preamble_full = f"{dealer_name.strip()}, {dealer_preamble.strip()},"
            c.drawString(64, 674, preamble_full)
            c.drawString(64 + c.stringWidth(preamble_full, "Arial", 9) + 4, 674, 'именуемая в дальнейшем "Дилер", с другой стороны,')

        elif page_idx == 5:
            # --- СТР. 6: Раздел 10 (Реквизиты и подписи) ---
            # Закрашиваем желтый квадрат реквизитов Дилера
            c.setFillColorRGB(1, 1, 1)
            c.rect(275, 540, 275, 185, fill=1, stroke=0)
            # Закрашиваем линию подписи Дилера справа
            c.rect(290, 425, 250, 35, fill=1, stroke=0)

            # Реквизиты Дилера на одном уровне с реквизитами ПК Мишка (y=707)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 8.5)
            y_text = 707
            for line in req_lines:
                c.drawString(280, y_text, line)
                y_text -= 14

            # Подпись Дилера строго на подчеркивании в правой колонке
            c.setFont("Arial", 9.5)
            c.drawString(292, 440, f"директор _______________ / {dealer_fio_short.strip()} /")

        elif page_idx == 6:
            # --- СТР. 7: Приложение №1 (Шапка над таблицей) ---
            # Закрашиваем строчку "к дилерскому договору № ... от « » 202 г."
            c.setFillColorRGB(1, 1, 1)
            c.rect(70, 755, 300, 16, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9.5)
            c.drawString(75, 760, f"к дилерскому договору № {clean_num} от {contract_date.strip()}")

        elif page_idx == 7:
            # --- СТР. 8: Приложение №1 (Подпись) ---
            c.setFillColorRGB(1, 1, 1)
            c.rect(290, 510, 250, 30, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9.5)
            c.drawString(292, 526, f"Генеральный директор ____________ / {dealer_fio_short.strip()} /")

        elif page_idx == 8:
            # --- СТР. 9: Приложение №2 ---
            # 1. Шапка над правилами
            c.setFillColorRGB(1, 1, 1)
            c.rect(70, 725, 300, 18, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9.5)
            c.drawString(75, 731, f"к Дилерскому договору № {clean_num} от {contract_date.strip()}")

            # 2. Реквизиты Дилера справа (ниже пункта 1.3, вровень с ПК Мишка)
            c.setFillColorRGB(1, 1, 1)
            c.rect(275, 315, 275, 165, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 8.5)
            y_text = 465
            for line in req_lines:
                c.drawString(280, y_text, line)
                y_text -= 14

            # 3. Подпись Дилера строго справа
            c.setFillColorRGB(1, 1, 1)
            c.rect(290, 235, 250, 30, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9.5)
            c.drawString(292, 247, f"Генеральный директор ____________ / {dealer_fio_short.strip()} /")

        elif page_idx == 9:
            # --- СТР. 10: Приложение №3 (Шапка над таблицей) ---
            # Закрашиваем желтую полосу со старыми пробелами
            c.setFillColorRGB(1, 1, 1)
            c.rect(70, 700, 470, 20, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9.5)
            c.drawString(75, 706, f"к Дилерскому договору № {clean_num} от {contract_date.strip()}")

        elif page_idx == 10:
            # --- СТР. 11: Приложение №3 (Конец) ---
            # 1. Реквизиты Дилера справа
            c.setFillColorRGB(1, 1, 1)
            c.rect(275, 545, 275, 165, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 8.5)
            y_text = 688
            for line in req_lines:
                c.drawString(280, y_text, line)
                y_text -= 14

            # 2. Подпись Дилера справа
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
