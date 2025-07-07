import re
from utils import extract_date, extract_amount


def extract_info(text, file_type):
    info = {}

    if file_type == "投标文件":
        # 基本信息
        info["项目名称"] = find_first(text, r"项目名称[:：]?\s*(.+?)\s")
        info["投标单位"] = find_first(text, r"(投标人|投标单位|响应单位)[:：]?\s*(.+?)\s", group=2)
        info["法定代表人"] = find_first(text, r"(法定代表人|法人代表)[:：]?\s*(.+?)\s", group=2)

        # 投标者联系方式
        info["联系人"] = find_first(text, r"(联系人|项目负责人)[:：]?\s*(.+?)\s", group=2)
        info["联系电话"] = find_first(text, r"(1[3-9]\d{9})")
        info["联系邮箱"] = find_first(text, r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

        # 金额与时间
        #这个要改
        info["投标报价"] = extract_amount(text)

        info["投标截止时间"] = extract_date(text)
        info["投标时间"] = find_first(text, r"(投标时间|提交时间)[:：]?\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)", group=2)
        info["报价时间"] = find_first(text, r"(报价时间)[:：]?\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)", group=2)

        #字体？
        info["字体"] = None

    elif file_type == "招标文件":
        # 招标文件字段提取
        info["项目名称"] = find_first(text, r"项目名称[:：]?\s*(.+?)\s")
        info["采购人名称"] = find_first(text, r"(采购人|招标人|买方)[:：]?\s*(.+?)\s", group=2)
        info["采购人地址"] = find_first(text, r"(采购人地址|联系地址)[:：]?\s*(.+?)\s", group=2)
        info["代理机构"] = find_first(text, r"(代理机构|招标代理)[:：]?\s*(.+?)\s", group=2)
        info["评分办法"] = find_first(text, r"(评分办法|评标方法|评分标准)[:：]?\s*(.+?)\s", group=2)

        #这个要改
        amount_list = extract_amount(text)
        info["最高限价"] = amount_list[0] if amount_list else None
        info["开标时间"] = extract_date(text)

    return info

# 工具函数：提取第一个匹配项
def find_first(text, pattern, group=1):
    match = re.search(pattern, text)
    return match.group(group) if match else None

# 工具函数：提取所有匹配项（列表）
def find_all(text, pattern, group=1):
    return [m.group(group) for m in re.finditer(pattern, text)]
