from utils import (
    extract_date, extract_amount, preprocess_text_for_nlp, 
    find_first
)

# 忽略 FutureWarning 警告
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# PaddleNLP 实体识别相关
try:
    from paddlenlp import Taskflow
    PADDLENLP_AVAILABLE = True
except ImportError:
    print("[警告] PaddleNLP 未安装，将使用传统正则表达式方法")
    PADDLENLP_AVAILABLE = False


# 为招标文件和投标文件分别定义 schema
BIDDING_SCHEMA = [
    # 招标文件专用字段
    "项目名称", "招标单位名称", "招标单位地址", "代理机构", 
    "评分办法", "最高限价", "开标时间", "投标截止时间",
    "项目编号", "招标单位联系人姓名", "招标单位联系电话", "公告发布时间"
]

TENDER_SCHEMA = [
    # 投标文件专用字段
    "项目名称", "投标单位名称", "采购代理机构", "法定代表人", "投标单位联系人姓名", 
    "投标单位联系电话", "投标单位联系邮箱", "投标报价", "投标截止时间",
    "投标时间", "报价时间", "项目编号", "企业资质", "项目开始时间",
    "项目工期", "项目人数", "负责人职务", "负责人资质", "高级职称人员数量", "中级职称人员数量", "低级职称人员数量",
    "投入设备", "投入资金", "进度管理方案", "巡查考核方案", "质量保证方案", "施工标准",
    "安全保障", "应急预案", "服务承诺", "沟通配合措施", "安全文明建设", "制度建设", "资料整编方案"
]


# 全量字段（合并所有 schema, 通用）
ALL_SCHEMA = list(set(BIDDING_SCHEMA + TENDER_SCHEMA))

ie_models = {}

# 初始化 PaddleNLP 实体识别器
if PADDLENLP_AVAILABLE:
    try:
        # 为不同文件类型初始化不同的模型
        ie_models["招标文件"] = Taskflow("information_extraction", 
                                       schema=BIDDING_SCHEMA, 
                                       model='uie-medium', 
                                       schema_lang='zh')
        
        ie_models["投标文件"] = Taskflow("information_extraction", 
                                       schema=TENDER_SCHEMA, 
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
        "投标文件": TENDER_SCHEMA,
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
            record_dict[key] = [{"span": item["text"]} for item in spans] if spans else []
        
        return {"records": record_dict, "file_type": file_type}
    except Exception as e:
        print(f"[错误] NLP 实体识别失败: {e}")
        return None

# 增强版信息提取：优先使用 NLP, 正则表达式作为补充
def extract_info_enhanced(text, file_type):
    # 使用 NLP 方法
    nlp_result = extract_entities_with_nlp(text, file_type)
    
    # 正则表达式方法作为备选
    regex_result = extract_info(text, file_type)
    
    # 合并结果
    if nlp_result and nlp_result["records"]:
        enhanced_info = {}
        records = nlp_result["records"]
        
        # 获取当前文件类型对应的 schema
        current_schema = get_schema_by_file_type(file_type)
        
        # 从 NLP 结果中提取第一个匹配项
        for field in current_schema:
            if field in records and records[field]:
                enhanced_info[field] = records[field][0]["span"]
        
        # 用正则表达式结果补充缺失的字段
        for key, value in regex_result.items():
            if key not in enhanced_info or not enhanced_info[key]:
                enhanced_info[key] = value
        
        enhanced_info = standardize_amounts_in_result(enhanced_info)
        
        return enhanced_info
    else:
        # 如果 NLP 不可用，返回正则表达式结果
        result = regex_result
        result = standardize_amounts_in_result(result)
        return result
      
# 传统正则表达式信息提取
def extract_info(text, file_type):
    info = {}

    if file_type == "投标文件":
        # 基本信息
        info["项目名称"] = find_first(text, r"项目名称[:：]?\s*(.+?)\s")
        info["投标单位"] = find_first(text, r"(投标人|投标单位|响应单位)[:：]?\s*(.+?)\s", group=2)
        info["法定代表人"] = find_first(text, r"(法定代表人|法人代表)[:：]?\s*(.+?)\s", group=2)

        # 投标者联系方式
        info["投标单位联系人"] = find_first(text, r"(联系人|项目负责人)[:：]?\s*(.+?)\s", group=2)
        info["投标单位联系电话"] = find_first(text, r"(1[3-9]\d{9})")
        info["投标单位联系邮箱"] = find_first(text, r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

        # 金额与时间
        amount_list = extract_amount(text)
        info["投标报价"] = amount_list[0] if amount_list else None
        info["投标截止时间"] = extract_date(text)
        info["投标时间"] = find_first(text, r"(投标时间|提交时间)[:：]?\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)", group=2)
        info["报价时间"] = find_first(text, r"(报价时间)[:：]?\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)", group=2)

    elif file_type == "招标文件":
        # 招标文件字段提取
        info["项目名称"] = find_first(text, r"项目名称[:：]?\s*(.+?)\s")
        info["采购人名称"] = find_first(text, r"(采购人|招标人|买方)[:：]?\s*(.+?)\s", group=2)
        info["采购人地址"] = find_first(text, r"(采购人地址|联系地址)[:：]?\s*(.+?)\s", group=2)
        info["代理机构"] = find_first(text, r"(代理机构|招标代理)[:：]?\s*(.+?)\s", group=2)
        info["评分办法"] = find_first(text, r"(评分办法|评标方法|评分标准)[:：]?\s*(.+?)\s", group=2)

        # 金额与时间
        amount_list = extract_amount(text)
        info["最高限价"] = amount_list[0] if amount_list else None
        info["开标时间"] = find_first(text, r"(开标时间)[:：]?\s*(.+?)\s", group=2)
        info["投标截止时间"] = find_first(text, r"(投标截止时间)[:：]?\s*(.+?)\s", group=2)
        
        # 招标单位信息
        info["招标单位名称"] = find_first(text, r"(招标单位|招标人)[:：]?\s*(.+?)\s", group=2)
        info["招标单位地址"] = find_first(text, r"(招标单位地址|招标人地址)[:：]?\s*(.+?)\s", group=2)
        info["招标单位联系人"] = find_first(text, r"(招标单位联系人|联系人)[:：]?\s*(.+?)\s", group=2)
        info["招标单位联系电话"] = find_first(text, r"(招标单位联系电话|联系电话)[:：]?\s*(1[3-9]\d{9})", group=2)

    return info

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
            else:
                # 如果 extract_amount 失败，尝试简单的数字提取
                import re
                numbers = re.findall(r'(\d+(?:\.\d+)?)', amount_text)
                if numbers:
                    try:
                        base_amount = float(numbers[0])
                        # 检查是否包含"万"
                        if '万' in amount_text:
                            info[field] = base_amount * 10000
                        else:
                            info[field] = base_amount
                    except ValueError:
                        # 转换失败，保持原值
                        pass
    
    return info
