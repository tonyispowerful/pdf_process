import re

# 将中文大写金额转换为阿拉伯数字
import cn2an
from datetime import datetime

def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

# 清理ocr扫描后的文本
def clean_ocr_text(text):
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        line = line.strip()
        # 去除乱码符号（Â、�、‰等）
        line = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9，。！？；（）%《》“”‘’、·—\-]", "", line)
        # 去除无意义短行
        if len(line) >= 3:
            cleaned.append(line)
    return "\n".join(cleaned)


def extract_date(text):
    match = re.search(r"(\d{4}[\-/年]\d{1,2}[\-/月]\d{1,2})", text)
    if match:
        try:
            return datetime.strptime(match.group(1).replace("年", "-").replace("月", "-").replace("日", ""), "%Y-%m-%d")
        except ValueError:
            pass
    return None


def extract_amount(text):
    text = text.replace(",", "")
    results = []

    # 1. 提取阿拉伯数字金额（如 120万元、5000元）
    arabic_pattern = r"(\d+(?:\.\d+)?)(?:\s*)?(万元|元)"
    for match in re.finditer(arabic_pattern, text):
        num_str, unit = match.groups()
        try:
            amount = float(num_str)
            if unit == "万元":
                amount *= 10000
            results.append(amount)
        except:
            continue

    # 2. 提取中文大写金额（如 壹佰贰拾万元整、伍仟元）
    chinese_pattern = r"[人民币]?[零〇一二两三四五六七八九壹贰叁肆伍陆柒捌玖拾佰仟万亿]+[元圆](整|正)?"
    for match in re.finditer(chinese_pattern, text):
        full_match = match.group()
        try:
            amount = cn2an.cn2an(full_match, "smart")
            results.append(float(amount))
        except:
            continue

    return results if results else None

