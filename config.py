import os
import pytesseract

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "bidding_db"
COLLECTION_NAME = "bids"
PDF_FOLDER = "./pdfs"

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Poppler 配置
POPPLER_PATHS = [
    os.path.join(PROJECT_ROOT, "poppler", "bin"),  # 项目内 poppler
    os.path.join(PROJECT_ROOT, "poppler", "Library", "bin"),  # conda 风格
]

def get_poppler_path():
    """获取可用的 poppler 路径"""
    for path in POPPLER_PATHS:
        if os.path.exists(path):
            # 检查关键文件是否存在
            pdftoppm = os.path.join(path, "pdftoppm.exe" if os.name == 'nt' else "pdftoppm")
            if os.path.exists(pdftoppm):
                print(f"[√] poppler路径配置成功: {path}")
                return path
    print("[!] 未找到可用的 poppler")
    return None
  
def get_tesseract_path():
    """获取可用的 Tesseract 路径并检查中文语言支持"""
    import subprocess
    
    possible_paths = [
        r"D:\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"E:\Tesseract-OCR\tesseract.exe",
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
    ]
    
    # 先检查系统 PATH 中是否有 tesseract
    import shutil
    system_tesseract = shutil.which("tesseract")
    if system_tesseract:
        possible_paths.insert(0, system_tesseract)
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                # 设置 tesseract 路径
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"[√] Tesseract 路径已设置为: {path}")
                
                # 检查中文语言支持
                result = subprocess.run([path, '--list-langs'], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    languages = result.stdout.strip().split('\n')[1:]  # 跳过第一行
                    chinese_langs = [lang for lang in languages if 'chi' in lang.lower()]
                    
                    if chinese_langs:
                        print(f"[√] 检测到中文语言包: {', '.join(chinese_langs)}")
                        return path
                    else:
                        print(f"[!] {path} 缺少中文语言包")
                        continue
                else:
                    print(f"[!] {path} 无法获取语言列表")
                    continue
                    
            except Exception as e:
                print(f"[!] {path} 测试失败: {e}")
                continue
    
    # 如果没有找到支持中文的 tesseract
    raise FileNotFoundError(
        "未找到支持中文的 Tesseract！\n"
        "请确保:\n"
        "1. 已安装 Tesseract-OCR\n"
        "2. 已安装中文语言包 (chi_sim.traineddata)\n"
        "3. 或在 config.py 中手动指定路径"
    )

POPPLER_PATH = get_poppler_path()
TESSERACT_PATH = get_tesseract_path()
