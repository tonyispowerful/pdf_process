import re
from datetime import datetime

def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

def extract_date(text):
    match = re.search(r"(\d{4}[\-/年]\d{1,2}[\-/月]\d{1,2})", text)
    if match:
        try:
            return datetime.strptime(match.group(1).replace("年", "-").replace("月", "-").replace("日", ""), "%Y-%m-%d")
        except ValueError:
            pass
    return None

def extract_amount(text):
    match = re.search(r"(\d{1,3}(,\d{3})*(\.\d+)?|\d+(\.\d+)?)", text.replace(",", ""))
    return float(match.group(1)) if match else None