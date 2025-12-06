# arranging all the files to provide the similar result format as the pdf_extraction.py did. FOR UNIFORMITY

from fastapi import HTTPException
from docx import Document

def extract_text_from_docx(docx_path: str):
    try:
        doc = Document(docx_path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs)
        # Simulate one-page structure for uniformity
        return [{"page_number": 1, "text": text}]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading DOCX: {str(e)}")
