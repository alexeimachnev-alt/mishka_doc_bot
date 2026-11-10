import io
import os
import tempfile
import subprocess
import openpyxl

def generate_doverennost_xlsx(data: dict) -> io.BytesIO:
    # Загружаем ГОСТовский шаблон из предыдущего шага
    file_path = "Доверенность м2 с печатями и подписью заполнять в середине.xlsx"
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active

    # Заполняем ячейки ГОСТовского шаблона
    ws['N17'] = data.get('number', '')
    ws['H19'] = data.get('date_issue', '')
    ws['H20'] = data.get('date_valid', '')
    ws['F31'] = data.get('fio_job', '')
    ws['L31'] = data.get('fio', '')
    
    ws['F33'] = data.get('passport_series', '')
    ws['M33'] = data.get('passport_number', '')
    ws['F34'] = data.get('passport_issued_by', '')
    ws['F35'] = data.get('passport_date', '')
    
    ws['F37'] = data.get('supplier', '')
    
    # ТМЦ (заполняем первую свободную строку таблицы)
    ws['B41'] = data.get('item_name', 'Товарно-материальные ценности по договору')
    ws['I41'] = data.get('item_unit', 'шт')
    ws['K41'] = data.get('item_qty', '1')

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

def convert_xlsx_to_pdf(xlsx_buf: io.BytesIO) -> io.BytesIO | None:
    """Конвертирует XLSX в PDF с помощью LibreOffice."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_xlsx:
            tmp_xlsx.write(xlsx_buf.getvalue())
            tmp_xlsx_path = tmp_xlsx.name

        out_dir = os.path.dirname(tmp_xlsx_path)
        subprocess.run([
            "libreoffice", "--headless", "--convert-to", "pdf",
            tmp_xlsx_path, "--outdir", out_dir
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        pdf_path = tmp_xlsx_path.replace(".xlsx", ".pdf")
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_buf = io.BytesIO(f.read())
            os.remove(pdf_path)
            os.remove(tmp_xlsx_path)
            return pdf_buf
    except Exception as e:
        print("PDF Conversion error (XLSX):", e)
    return None
