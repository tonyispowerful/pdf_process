import os
from datetime import datetime
from config import PDF_FOLDER
from pdf_reader import extract_pdf_text
from info_extractor import extract_info_enhanced
from db_manager import insert_bid_data, bid_exists

# 判断文件类型
def determine_file_type(file_name, text_preview=""):
    file_name_lower = file_name.lower()
    
    # 基于文件名判断
    if any(keyword in file_name_lower for keyword in ["招标", "采购", "公告"]):
        return "招标文件"
    elif any(keyword in file_name_lower for keyword in ["投标", "响应", "报价"]):
        return "投标文件"

    
    # 基于内容判断（如果文件名不明确）
    if text_preview:
        if any(keyword in text_preview[:1000] for keyword in ["招标公告", "采购公告", "最高限价"]):
            return "招标文件"
        elif any(keyword in text_preview[:1000] for keyword in ["投标人", "投标报价", "响应文件"]):
            return "投标文件"
    
    # 默认返回类型为通用
    return "通用"

# 判断提取信息的完整性
def validate_extracted_info(info, file_type):
    required_fields = {
        "招标文件": ["项目名称", "采购人名称"],
        "投标文件": ["项目名称", "投标单位"],
    }
    
    required = required_fields.get(file_type, ["项目名称"])
    missing_fields = [field for field in required if not info.get(field)]
    
    return len(missing_fields) == 0, missing_fields


def process_pdfs():
    """处理 PDF 文件的主函数"""
    # 统计信息
    stats = {
        "总文件数": 0,
        "处理成功": 0,
        "跳过文件": 0,
        "处理失败": 0,
        "字段缺失": 0
    }
    
    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith(".pdf")]
    stats["总文件数"] = len(pdf_files)
    
    print(f"开始处理 {stats['总文件数']} 个 PDF 文件...")
    
    for i, file_name in enumerate(pdf_files, 1):
        print(f"\n[{i}/{stats['总文件数']}] 处理中: {file_name}")
        
        # 检查是否已存在
        if bid_exists(file_name):
            print(f"[跳过] {file_name} 已存在于数据库中")
            stats["跳过文件"] += 1
            continue

        file_path = os.path.join(PDF_FOLDER, file_name)

        try:
            # 提取文本
            print("  - 提取PDF文本...")
            text = extract_pdf_text(file_path)
            
            if not text or len(text.strip()) < 50:
                print(f"[警告] {file_name} 提取的文本内容过少，可能是扫描质量问题")
                stats["处理失败"] += 1
                continue
            
            # 智能判断文件类型
            file_type = determine_file_type(file_name, text)
            print(f"  - 文件类型: {file_type}")

            # 进行信息提取
            print("  - 提取结构化信息...")
            info = extract_info_enhanced(text, file_type)
            
            if not info:
                print(f"[错误] {file_name} 信息提取失败")
                stats["处理失败"] += 1
                continue

            # 验证关键字段
            is_valid, missing_fields = validate_extracted_info(info, file_type)
            if not is_valid:
                print(f"[警告] {file_name} 缺少必要字段: {missing_fields}")
                stats["字段缺失"] += 1
                # 继续处理，但标记为不完整
                info["数据完整性"] = "不完整"
                info["缺失字段"] = missing_fields
            else:
                info["数据完整性"] = "完整"

            # 补充元数据
            info.update({
                "文件名": file_name,
                "原始文本": text,
                "文件类型": file_type,
                "提取时间": datetime.now(),
                "文本长度": len(text),
            })

            # 写入数据库
            print("  - 写入数据库...")
            insert_bid_data(info)
            print(f"[完成] 成功处理: {file_name}")
            stats["处理成功"] += 1

        except Exception as e:
            print(f"[错误] 处理 {file_name} 时出错: {str(e)}")
            stats["处理失败"] += 1
            
    # 打印统计结果
    print("\n" + "="*50)
    print("处理完成! 统计结果:")
    print(f"总文件数: {stats['总文件数']}")
    print(f"处理成功: {stats['处理成功']}")
    print(f"跳过文件: {stats['跳过文件']}")
    print(f"字段缺失: {stats['字段缺失']}")
    print(f"处理失败: {stats['处理失败']}")
    print(f"成功率: {stats['处理成功']/max(stats['总文件数']-stats['跳过文件'], 1)*100:.1f}%")


if __name__ == "__main__":
    process_pdfs()
    # 处理完成后，可以在数据库中查看提取结果, 也可以导出为 Excel 文件
    from db_manager import export_to_csv
    export_to_csv()

