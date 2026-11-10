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
    source_path = "Dilerskiy_Dogovor_PK_Mishka_redaktirovanny.docx"
    doc = docx.Document(source_path)

    # 1. Update Paragraphs
    for p in doc.paragraphs:
        # Preamble replacement
        if "с одной стороны, и Индивидуальный предприниматель" in p.text:
            if dealer_preamble:
                new_dealer_str = f"{dealer_name}, {dealer_preamble}, именуемый в дальнейшем «Дилер»"
            else:
                new_dealer_str = f"{dealer_name}, именуемый в дальнейшем «Дилер»"

            target_str = "Индивидуальный предприниматель / Гражданка РФ Болталина Карина Николаевна, именуемая в дальнейшем «Дилер»"
            p.text = p.text.replace(target_str, new_dealer_str)

        # Contract number and signatures
        for run in p.runs:
            if "23940" in run.text:
                run.text = run.text.replace("23940", contract_num)
            if "«___» ____________ 202_ г." in run.text:
                run.text = run.text.replace("«___» ____________ 202_ г.", contract_date)
            if "Болталина К. Н." in run.text:
                clean_fio = dealer_fio_short.strip().strip("/").strip()
                run.text = run.text.replace("Болталина К. Н.", clean_fio)

    # 2. Update Tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                # Date in the top table
                if "«___» ____________ 202_ г." in cell.text:
                    for p in cell.paragraphs:
                        for run in p.runs:
                            if "«___» ____________ 202_ г." in run.text:
                                run.text = run.text.replace("«___» ____________ 202_ г.", contract_date)

                # Requisites in the bottom table
                if "Болталина Карина Николаевна" in cell.text and "Паспорт" in cell.text:
                    # Clear cell
                    cell.text = ""
                    # Rebuild cell paragraphs
                    for i, line in enumerate(custom_req_lines):
                        p = cell.add_paragraph()
                        # Apply Calibri 10.5 matching original layout
                        p.style = doc.styles['Normal']
                        if i == 0 or line == "Дилер":
                            p.add_run(line).bold = True
                        else:
                            p.add_run(line)

                    # Add signature
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
