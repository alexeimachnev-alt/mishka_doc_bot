import io
import os
import tempfile
import subprocess
import docx

def generate_diler_contract_docx(
    contract_num: str,
    contract_date: str,
    dealer_name: str,
    dealer_preamble: str,
    dealer_fio_short: str,
    custom_req_lines: list[str]
) -> io.BytesIO:
    source_path = "Дилерский_договор_111000_ООО_МАЧНЕВ_И_КО.docx"
    doc = docx.Document(source_path)

    # 1. Замена текста в абзацах
    for p in doc.paragraphs:
        # Преамбула
        if "с одной стороны, и" in p.text and ("Дилер" in p.text or "именуемый" in p.text or "именуемая" in p.text):
            if "ООО МАЧНЕВ И КО" in p.text or "Индивидуальный предприниматель" in p.text or "Гражданка" in p.text:
                parts = p.text.split("с одной стороны, и")
                if len(parts) == 2:
                    prefix = parts[0] + "с одной стороны, и "
                    if dealer_preamble:
                        new_dealer_str = f"{dealer_name}, {dealer_preamble}, именуемый в дальнейшем «Дилер»"
                    else:
                        new_dealer_str = f"{dealer_name}, именуемый в дальнейшем «Дилер»"
                    
                    # Ищем где заканчивается блок дилера
                    for keyword in ["именуемый в дальнейшем «Дилер»", "именуемая в дальнейшем «Дилер»"]:
                        if keyword in parts[1]:
                            suffix_parts = parts[1].split(keyword)
                            if len(suffix_parts) >= 2:
                                suffix = keyword + suffix_parts[1]
                                p.text = prefix + new_dealer_str + suffix
                                break

        # Поиск и замена по отдельным run-ам для сохранения жирности
        for run in p.runs:
            if "111000" in run.text:
                run.text = run.text.replace("111000", contract_num)
            if "Мачнев А.И." in run.text:
                clean_fio = dealer_fio_short.strip().strip("/").strip()
                run.text = run.text.replace("Мачнев А.И.", clean_fio)

    # Общий проход для гарантии замены номера договора
    for p in doc.paragraphs:
        for run in p.runs:
            if "111000" in run.text:
                run.text = run.text.replace("111000", contract_num)
            if "Мачнев А.И." in run.text:
                clean_fio = dealer_fio_short.strip().strip("/").strip()
                run.text = run.text.replace("Мачнев А.И.", clean_fio)

    # 2. Замена текста в таблицах
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                # Замена даты в верхней таблице или шапках
                if "ноября" in cell.text or "202_" in cell.text or "2026" in cell.text:
                    for p in cell.paragraphs:
                        for run in p.runs:
                            if any(d in run.text for d in ["2026", "202_", "ноября", "от"]):
                                run.text = contract_date

                # Замена номера договора в приложениях
                if "№" in cell.text and ("от" in cell.text or "Договору" in cell.text):
                    for p in cell.paragraphs:
                        for run in p.runs:
                            if "111000" in run.text:
                                run.text = run.text.replace("111000", contract_num)

                # Замена реквизитов Дилера в нижней таблице
                if "МАЧНЕВ" in cell.text or "Паспорт" in cell.text or "ИНН/КПП" in cell.text or "Р/с" in cell.text or "Юр. адрес" in cell.text:
                    # Очищаем ячейку
                    cell.text = ""
                    # Воссоздаем абзацы реквизитов
                    for i, line in enumerate(custom_req_lines):
                        p = cell.add_paragraph()
                        p.style = doc.styles['Normal']
                        if i == 0 or line == "Дилер":
                            p.add_run(line).bold = True
                        else:
                            p.add_run(line)

                    # Добавляем строку с подписью
                    p = cell.add_paragraph("\nДилер\n\n")
                    p.runs[0].bold = True
                    clean_fio = dealer_fio_short.strip().strip("/").strip()
                    p.add_run(f"___________ / {clean_fio} /")

    # Проверка шапок приложений на наличие номера договора
    for p in doc.paragraphs:
        if "к Дилерскому договору №" in p.text:
            for run in p.runs:
                if "111000" in run.text:
                    run.text = run.text.replace("111000", contract_num)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


def convert_docx_to_pdf(docx_buf: io.BytesIO) -> io.BytesIO | None:
    """Конвертирует DOCX в PDF с помощью LibreOffice (если установлен на сервере)."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_docx:
            tmp_docx.write(docx_buf.getvalue())
            tmp_docx_path = tmp_docx.name

        out_dir = os.path.dirname(tmp_docx_path)
        subprocess.run([
            "libreoffice", "--headless", "--convert-to", "pdf",
            tmp_docx_path, "--outdir", out_dir
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        pdf_path = tmp_docx_path.replace(".docx", ".pdf")
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_buf = io.BytesIO(f.read())
            os.remove(pdf_path)
            os.remove(tmp_docx_path)
            return pdf_buf
    except Exception as e:
        print("PDF Conversion error:", e)
    return None
