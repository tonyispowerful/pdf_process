import os
from datetime import datetime
from config import PDF_FOLDER
from pdf_reader import extract_pdf_text
from db_manager import insert_bid_data, bid_exists
import re

from utils import (
    extract_amount, preprocess_text_for_nlp, 
)

# 忽略 FutureWarning 警告
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# PaddleNLP 实体识别相关
try:
    from paddlenlp import Taskflow
    PADDLENLP_AVAILABLE = True
except ImportError:
    print("[警告] PaddleNLP 未安装，请确保已安装 PaddleNLP 库")
    raise ImportError("PaddleNLP 库未安装，请先安装 PaddleNLP")


# 为招标文件和投标文件分别定义 schema
BIDDING_SCHEMA = [
    # 招标文件专用字段
    "项目名称","招标编号",  "招标单位名称", "招标单位地址", "代理机构", 
    "评分办法", "最高限价", "开标时间", "投标截止时间",
    "项目编号", "招标单位联系人姓名", "招标单位联系电话", "公告发布时间"
]

TENDER_SCHEMA = [
    # 投标文件专用字段 - 简单实体
    "项目名称", "投标单位名称", "采购代理机构", "法定代表人", "投标单位联系人姓名", 
    "投标单位联系电话", "投标单位联系邮箱", "投标报价", "投标截止时间",
    "投标时间", "报价时间", "项目编号", "企业资质", "项目开始时间",
    "项目工期", "项目人数", "负责人职务", "负责人资质", "高级职称人员数量", "中级职称人员数量", "低级职称人员数量",
    "投入设备", "投入资金"
]

# 定义需要提取详细内容的复杂字段
COMPLEX_CONTENT_SCHEMA = [
    "进度管理方案", "巡查考核方案", "质量保证方案", "施工标准",
    "安全保障", "应急预案", "服务承诺", "沟通配合措施", 
    "安全文明建设", "制度建设", "资料整编方案"
]


# 全量字段（合并所有 schema, 通用）
ALL_SCHEMA = list(set(BIDDING_SCHEMA + TENDER_SCHEMA + COMPLEX_CONTENT_SCHEMA))

ie_models = {}

# 初始化 PaddleNLP 实体识别器
if PADDLENLP_AVAILABLE:
    try:
        # 为不同文件类型初始化不同的模型
        ie_models["招标文件"] = Taskflow("information_extraction", 
                                       schema=BIDDING_SCHEMA, 
                                       model='uie-medium', 
                                       schema_lang='zh')
        
        tender_full_schema = TENDER_SCHEMA + COMPLEX_CONTENT_SCHEMA
        ie_models["投标文件"] = Taskflow("information_extraction", 
                                       schema=tender_full_schema, 
                                       model='uie-medium', 
                                       schema_lang='zh')
        ie_models["通用"] = Taskflow("information_extraction", 
                                       schema=ALL_SCHEMA, 
                                       model='uie-medium', 
                                       schema_lang='zh')
        
        print("PaddleNLP 实体识别器初始化成功")
    except Exception as e:
        print(f"[警告] PaddleNLP 初始化失败: {e}")
        PADDLENLP_AVAILABLE = False

# 根据文件类型获取对应的 schema
def get_schema_by_file_type(file_type):
    schema_mapping = {
        "招标文件": BIDDING_SCHEMA,
        "投标文件": TENDER_SCHEMA + COMPLEX_CONTENT_SCHEMA,
    }
    return schema_mapping.get(file_type, ALL_SCHEMA)
  
# 使用 PaddleNLP 进行实体识别
def extract_entities_with_nlp(text, file_type="通用"):
    if not PADDLENLP_AVAILABLE:
        return None
    
    try:
        # 选择对应的模型
        ie_model = ie_models.get(file_type, ie_models.get("通用"))
        if not ie_model:
            print(f"[警告] 未找到 {file_type} 对应的模型，使用通用模型")
            ie_model = ie_models.get("通用")
        
        # 预处理文本
        processed_text = preprocess_text_for_nlp(text)
        
        # 获取对应的 schema
        current_schema = get_schema_by_file_type(file_type)
        
        # 执行实体识别
        result = ie_model(processed_text)
        
        if isinstance(result, list):
            # 如果返回列表，取第一个元素
            result = result[0] if result else {}
        elif not isinstance(result, dict):
            # 如果既不是字典也不是列表，返回空字典
            result = {}
        
        record_dict = {}
        
        # 格式化结果
        for key in current_schema:
            spans = result.get(key, [])
            if key in COMPLEX_CONTENT_SCHEMA:
                # 对于复杂内容字段，提取所有相关文本并合并
                if spans:
                    # 合并所有提取的文本片段
                    all_text = []
                    for item in spans:
                        text_content = item.get("text", "")
                        if text_content and len(text_content.strip()) > 10:  # 过滤过短的文本
                            all_text.append(text_content.strip())
                    
                    # 如果没有足够的内容，尝试基于关键词搜索
                    if not all_text:
                        extracted_content = extract_content_by_keyword(processed_text, key)
                        if extracted_content:
                            all_text = [extracted_content]
                    
                    record_dict[key] = [{"span": "\n".join(all_text)}] if all_text else []
                else:
                    # 如果NLP没有识别出来，尝试基于关键词提取
                    extracted_content = extract_content_by_keyword(processed_text, key)
                    record_dict[key] = [{"span": extracted_content}] if extracted_content else []
            else:
                # 简单字段保持原有逻辑
                record_dict[key] = [{"span": item["text"]} for item in spans] if spans else []
        
        return {"records": record_dict, "file_type": file_type}
    except Exception as e:
        print(f"[错误] NLP 实体识别失败: {e}")
        return None

# 基于字段名称从文本中提取相关段落内容
def extract_content_by_keyword(text, field_name):
    """
    基于字段名称从文本中提取相关段落内容
    """
    # 定义关键词映射
    keyword_mapping = {
        "质量保证方案": ["质量保证", "质量管理", "质量控制", "质量方案", "质量措施"],
        "安全保障": ["安全保障", "安全措施", "安全管理", "安全防护", "安全方案"],
        "进度管理方案": ["进度管理", "进度控制", "进度安排", "时间安排", "工期管理"],
        "应急预案": ["应急预案", "应急处理", "应急措施", "突发事件", "应急响应"],
        "服务承诺": ["服务承诺", "服务保证", "服务质量", "服务标准"],
        "施工标准": ["施工标准", "施工规范", "施工要求", "技术标准", "作业标准"],
        "巡查考核方案": ["巡查", "考核", "检查", "监督", "评估"],
        "沟通配合措施": ["沟通配合", "协调", "配合", "沟通机制"],
        "安全文明建设": ["安全文明", "文明施工", "现场管理"],
        "制度建设": ["制度建设", "管理制度", "规章制度", "制度完善"],
        "资料整编方案": ["资料整编", "资料管理", "档案管理", "文档整理"]
    }
    
    keywords = keyword_mapping.get(field_name, [field_name])
    
    # 按段落分割文本
    paragraphs = re.split(r'\n\s*\n', text)
    
    relevant_content = []
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if len(paragraph) < 20:  # 跳过过短的段落
            continue
            
        # 检查段落是否包含相关关键词
        for keyword in keywords:
            if keyword in paragraph:
                relevant_content.append(paragraph)
                break
    
    # 如果找到相关内容，返回合并后的文本
    if relevant_content:
        return "\n\n".join(relevant_content[:3])  # 最多返回3个相关段落
    
    return None


# 创建一个和 schema 顺序一致的有序结果
def create_ordered_result(data, schema):
    ordered_result = {}
    
    # 按照 schema 顺序添加字段，包括 None 值
    for field in schema:
        ordered_result[field] = data.get(field, None)
    
    return ordered_result

# nlp 信息提取
def extract_info(text, file_type):
    # 使用 NLP 方法
    nlp_result = extract_entities_with_nlp(text, file_type)
    
    # 获取当前文件类型对应的 schema
    current_schema = get_schema_by_file_type(file_type)
    
    enhanced_info = {}
    
    # 初始化所有schema字段为空值
    for field in current_schema:
        enhanced_info[field] = None
    
    if nlp_result and nlp_result["records"]:
        records = nlp_result["records"]
        
        # 从 NLP 结果中提取第一个匹配项，覆盖对应字段
        for field in current_schema:
            if field in records and records[field]:
                enhanced_info[field] = records[field][0]["span"]
    
    enhanced_info = standardize_amounts_in_result(enhanced_info)
    
    enhanced_info = create_ordered_result(enhanced_info, current_schema)
    
    return enhanced_info
      
# 标准化结果中的金额字段为阿拉伯数字
def standardize_amounts_in_result(info):
    # 需要标准化的金额字段
    amount_fields = ["投标报价", "最高限价"]
    
    for field in amount_fields:
        if field in info and info[field]:
            # 如果已经是数字，跳过
            if isinstance(info[field], (int, float)):
                continue
            
            # 提取并转换金额
            amount_text = str(info[field])
            converted_amounts = extract_amount(amount_text)
            
            if converted_amounts and len(converted_amounts) > 0:
                # 取第一个有效金额
                info[field] = converted_amounts[0]
    
    return info

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
        if any(keyword in text_preview[:10000] for keyword in ["招标文件", "招标公告", "采购公告", "最高限价"]):
            return "招标文件"
        elif any(keyword in text_preview[:10000] for keyword in ["投标单位", "投标文件", "投标书", "投标人", "投标报价", "响应文件"]):
            return "投标文件"
    
    # 默认返回类型为通用
    return "通用"
  
# 判断提取信息的完整性
def validate_extracted_info(info, file_type):
    required_fields = {
        "招标文件": ["项目名称", "招标单位名称"],
        "投标文件": ["项目名称", "投标单位名称"],
    }
    
    required = required_fields.get(file_type, ["项目名称"])
    missing_fields = [field for field in required if not info.get(field)]
    
    return len(missing_fields) == 0, missing_fields
  
# pdf的主处理函数：遍历 PDF 文件夹，提取信息并存入数据库
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
            print("  - 提取结构化信息... 提取时间可能较长")
            info = extract_info(text, file_type)
            
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

