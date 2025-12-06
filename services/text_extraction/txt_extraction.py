from fastapi import HTTPException

def extract_text_from_txt(txt_path: str):
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()
        return [{"page_number": 1, "text": text.strip()}]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading TXT: {str(e)}")
