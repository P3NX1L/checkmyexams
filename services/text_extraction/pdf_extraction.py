import fitz
from fastapi import HTTPException

def extract_text_from_pdf_original(pdf_path: str) -> str:
    try:
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text("text") + "\n"
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text: {str(e)}")
def extract_text_from_pdf(pdf_path: str):
    try:
        pages = []
        doc = fitz.open(pdf_path)
        print(f"[DEBUG][PDF] Total pages: {len(doc)}")
        for i, page in enumerate(doc):
            text = page.get_text("text")
            print(f"[DEBUG][PDF] Page {i+1} length: {len(text)}")
            pages.append({"page_number": i + 1, "text": text})
        doc.close()
        return pages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF extraction error: {e}")
