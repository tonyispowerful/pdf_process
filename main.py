import os
from datetime import datetime
from config import PDF_FOLDER
from pdf_reader import extract_pdf_text
from info_extractor import extract_info
from db_manager import insert_bid_data, bid_exists


def process_pdfs():
    for file_name in os.listdir(PDF_FOLDER):
        if not file_name.lower().endswith(".pdf"):
            continue

        if bid_exists(file_name):
            print(f"[跳过] {file_name} 已存在")
            continue

        file_path = os.path.join(PDF_FOLDER, file_name)
        try:
            print(f"[处理中] {file_name}")
            text = extract_pdf_text(file_path)
            info = extract_info(text)

            if not info["project_name"] or not info["bidding_company"]:
                print(f"[警告] 未提取到必要字段: {file_name}")
                continue

            info.update({
                "file_name": file_name,
                "raw_text": text,
                "extracted_at": datetime.now()
            })

            insert_bid_data(info)
            print(f"[完成] 成功写入数据库: {file_name}")

        except Exception as e:
            print(f"[错误] 处理 {file_name} 时出错: {str(e)}")


if __name__ == "__main__":
    process_pdfs()
