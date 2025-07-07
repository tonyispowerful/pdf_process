import pdfplumber
from pdf2image import convert_from_path
from pytesseract import image_to_string
import pytesseract
from utils import clean_text, clean_ocr_text

# 设置Tesseract路径，后面还要改
pytesseract.pytesseract.tesseract_cmd = r"D:\tesseract\tesseract.exe"


def extract_pdf_text(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text and len(page_text.strip()) > 10:
                # 直接提取文本型页面内容
                print(f"第{i+1}页：使用文本提取")
                text += page_text + "\n"
            else:
                # 使用 OCR 提取扫描页内容
                print(f"第{i+1}页：使用OCR识别")
                # 这个poppler 路径也要改
                images = convert_from_path(file_path, dpi=300, first_page=i+1, last_page=i+1, poppler_path=r"D:\poppler\Library\bin")
                if images:
                    ocr_text = image_to_string(images[0], lang="chi_sim")
                    cleand_ocr = clean_ocr_text(ocr_text)
                    text += cleand_ocr + "\n"
    return clean_text(text)