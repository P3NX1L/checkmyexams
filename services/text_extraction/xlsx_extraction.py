from fastapi import HTTPException
import pandas as pd

def extract_text_from_xlsx(xlsx_path: str):
    try:
        xls = pd.ExcelFile(xlsx_path)
        pages = []
        for i, sheet in enumerate(xls.sheet_names, start=1):
            df = pd.read_excel(xls, sheet_name=sheet)
            text = df.to_string(index=False)
            pages.append({"page_number": i, "text": text})
        return pages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading XLSX: {str(e)}")
