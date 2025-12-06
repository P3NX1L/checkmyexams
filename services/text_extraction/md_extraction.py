
from fastapi import HTTPException

def extract_text_from_md(md_path: str):
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Clean markdown syntax (removing unnecessary symbols) (keep headers)
        content = content.replace("#", "").replace("*", "").replace("-", "")
        return [{"page_number": 1, "text": content.strip()}]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading MD: {str(e)}")
