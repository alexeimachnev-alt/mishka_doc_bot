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
    """Генерация 11-страничного договора с поддержкой pypdf 7.0+"""
    # Инициализируем writer напрямую через clone_from (требование pypdf 7.0+)
    writer = pypdf.PdfWriter(clone_from=DILER_DOC_PATH)

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
            # Стр. 6: Место 1 реквизитов дилера
            c.setFillColorRGB(1, 1, 1)
            c.rect(275, 595, 240, 160, fill=1, stroke=0)

            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 8.5)
            y_text = 745
            for line in req_lines:
                c.drawString(280, y_text, line)
                y_text -= 14

            c.drawString(390, 523, f"/ {dealer_fio_short.strip()} /")

        elif page_idx == 6:
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9)
            c.drawString(235, 769, f"№ {contract_num.strip()}")
            c.drawString(295, 769, contract_date.strip())

        elif page_idx == 7:
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9)
            c.drawString(390, 523, f"/ {dealer_fio_short.strip()} /")

        elif page_idx == 8:
            # Стр. 9: Место 2 реквизитов дилера
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9)
            c.drawString(235, 769, f"№ {contract_num.strip()}")
            c.drawString(295, 769, contract_date.strip())

            c.setFont("Arial", 8.5)
            y_text = 540
            for line in req_lines:
                c.drawString(280, y_text, line)
                y_text -= 14

            c.drawString(390, 317, f"/ {dealer_fio_short.strip()} /")

        elif page_idx == 9:
            c.setFillColorRGB(1, 1, 1)
            c.rect(70, 735, 450, 22, fill=1, stroke=0)

            c.setFillColorRGB(0, 0, 0)
            c.setFont("Arial", 9)
            c.drawString(75, 742, f"к Дилерскому договору № {contract_num.strip()}   от  {contract_date.strip()}")

        elif page_idx == 10:
            # Стр. 11: Место 3 реквизитов дилера
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
        page.merge_page(overlay_pdf.pages[0])

    final_buffer = io.BytesIO()
    writer.write(final_buffer)
    final_buffer.seek(0)
    return final_buffer
