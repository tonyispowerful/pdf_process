import re
import cn2an # 将中文大写金额转换为阿拉伯数字
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
        line = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9，。！？；（）%《》""''、·—-]", "", line)
        # 去除无意义短行
        if len(line) >= 3:
            cleaned.append(line)
    return "\n".join(cleaned)

# NLP 文本预处理函数
def preprocess_text_for_nlp(text):
    """为 NLP 处理预处理文本"""
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    
    # 移除特殊字符但保留中文标点
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？；（）：\-\s]', '', text)
    
    # 限制文本长度（避免模型处理过长文本）
    if len(text) > 10000:
        text = text[:10000]
    
    return text.strip()

# 提取第一个匹配项
def find_first(text, pattern, group=1):
    """使用正则表达式提取第一个匹配项"""
    match = re.search(pattern, text)
    return match.group(group) if match else None

# 提取所有匹配项（列表）
def find_all(text, pattern, group=1):
    """使用正则表达式提取所有匹配项"""
    return [m.group(group) for m in re.finditer(pattern, text)]

# 文本清理和格式化函数
def normalize_text(text):
    """标准化文本格式"""
    if not text:
        return ""
    
    # 统一换行符
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # 去除多余空格
    text = re.sub(r'[ \t]+', ' ', text)
    
    # 去除多余换行
    text = re.sub(r'\n\s*\n', '\n', text)
    
    # 去除行首行尾空格
    lines = [line.strip() for line in text.split('\n')]
    
    return '\n'.join(line for line in lines if line)

def extract_date(text):
    match = re.search(r"(\d{4}[\-/年]\d{1,2}[\-/月]\d{1,2})", text)
    if match:
        try:
            return datetime.strptime(match.group(1).replace("年", "-").replace("月", "-").replace("日", ""), "%Y-%m-%d")
        except ValueError:
            pass
    return None

# 转换金额信息为阿拉伯数字
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

