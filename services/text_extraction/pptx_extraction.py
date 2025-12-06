

from fastapi import HTTPException
from pptx import Presentation
import os
import subprocess

def extract_text_from_pptx(pptx_path: str):
    try:
        #Auto-convert .ppt → .pptx if needed
        if pptx_path.lower().endswith(".ppt"):
            
            raise HTTPException(status_code=500, detail=f"(.PPT) extension not supported. please upload a valid file format (.PPTX)")

        # Continue your original logic
        prs = Presentation(pptx_path)
        pages = []
        for i, slide in enumerate(prs.slides, start=1):
            slide_text = []
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    slide_text.append(shape.text)
            pages.append({"page_number": i, "text": "\n".join(slide_text)})

        return pages

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading PPTX: {str(e)}")
