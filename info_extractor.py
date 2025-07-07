import re
from utils import extract_date, extract_amount


def extract_info(text):
    info = {}

    project_match = re.search(r"项目名称[:：]?\s*(.+?)\s", text)
    company_match = re.search(r"投标人[:：]?\s*(.+?)\s", text)
    contact_match = re.search(r"联系人[:：]?\s*(.+?)\s", text)
    phone_match = re.search(r"(1[3-9]\d{9})", text)

    info["project_name"] = project_match.group(1) if project_match else None
    info["bidding_company"] = company_match.group(1) if company_match else None
    info["contact_person"] = contact_match.group(1) if contact_match else None
    info["contact_phone"] = phone_match.group(1) if phone_match else None
    info["bid_deadline"] = extract_date(text)
    info["bid_amount"] = extract_amount(text)

    return info