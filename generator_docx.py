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
        if "с одной стороны, и ООО МАЧНЕВ И КО, в лице" in p.text:
            if dealer_preamble:
                new_dealer_str = f"{dealer_name}, {dealer_preamble}, именуемый в дальнейшем «Дилер»"
            else:
                new_dealer_str = f"{dealer_name}, именуемый в дальнейшем «Дилер»"
            
            target_str = "ООО МАЧНЕВ И КО, в лице Генерального директора Мачнева А.И., действующего на основании Устава, именуемый в дальнейшем «Дилер»"
            p.text = p.text.replace(target_str, new_dealer_str)

        # Поиск и замена по отдельным run-ам для сохранения жирности
        for run in p.runs:
            if "111000" in run.text:
                run.text = run.text.replace("111000", contract_num)
            if "«11» ноября 2026г." in run.text:
                run.text = run.text.replace("«11» ноября 2026г.", contract_date)
            if "Мачнев А.И." in run.text:
                clean_fio = dealer_fio_short.strip().strip("/").strip()
                run.text = run.text.replace("Мачнев А.И.", clean_fio)

    # 2. Замена текста в таблицах
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                # Замена даты в верхней таблице
                if "«11» ноября 2026г." in cell.text:
                    for p in cell.paragraphs:
                        for run in p.runs:
                            if "«11» ноября 2026г." in run.text:
                                run.text = run.text.replace("«11» ноября 2026г.", contract_date)

                # Замена реквизитов Дилера в нижней таблице (ищем старое название "ООО МАЧНЕВ И КО")
                if "ООО МАЧНЕВ И КО" in cell.text:
                    # Очищаем ячейку
                    cell.text = ""
                    # Воссоздаем абзацы реквизитов
                    for i, line in enumerate(custom_req_lines):
                        p = cell.add_paragraph()
                        # Применяем оригинальный стиль Calibri 10.5
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
