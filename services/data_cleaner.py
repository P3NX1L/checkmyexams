import re
import unicodedata
import logging

logger = logging.getLogger(__name__)
def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\t", " ")
    text = re.sub(r'[ ]{2,}', ' ', text)
    return text.strip()


def remove_noise(text: str) -> str:
    lines = text.splitlines()
    cleaned = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if re.match(r'^Page\s+\d+(\s+of\s+\d+)?$', line, re.I):
            continue

        cleaned.append(line)

    return "\n".join(cleaned)


def semantic_cleanup(text: str) -> str:
    patterns = [
        r"(?im)^this\s+document\s+is\s+confidential.*$",
        r"(?im)^all\s+rights\s+reserved.*$",
        r"(?im)^do\s+not\s+distribute.*$",
        r"(?im)^click\s+here.*$",
    ]
    for p in patterns:
        text = re.sub(p, '', text)
    return text

def clean_text(raw_text: str) -> str:
    try:
        normalized = normalize_text(raw_text)
        denoised = remove_noise(normalized)
        cleaned = semantic_cleanup(denoised)
        return cleaned
    except:
        return raw_text
