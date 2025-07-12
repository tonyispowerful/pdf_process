"""
测试 PaddleNLP 实体识别功能(提取schema)
"""
# 忽略 FutureWarning 警告
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from info_extractor import extract_entities_with_nlp, extract_info_enhanced

# 测试文本
test_text = """
项目名称：某办公设备采购项目
公告类别：中标公告
开标日期：2025年7月8日
招标单位名称：某市政府采购中心
招标单位地址：某市建设路123号
招标单位联系人：张先生
招标单位联系电话：010-12345678
项目编号：2025-001
第一中标供应商单位名称：XX科技有限公司
投标报价：150万元
采购人名称：某市教育局
"""

def test_nlp_extraction():
    print("=== 测试 PaddleNLP 实体识别 ===")
    
    # 测试原始 NLP 提取
    nlp_result = extract_entities_with_nlp(test_text)
    if nlp_result:
        print("NLP 识别结果：")
        for key, value in nlp_result["records"].items():
            if value:
                print(f"  {key}: {value}")
    else:
        print("NLP 识别失败或不可用")
    
    print("\n=== 测试增强版信息提取 ===")
    
    # 测试增强版提取（NLP + 正则表达式）
    enhanced_result = extract_info_enhanced(test_text, "招标文件")
    print("增强版提取结果：")
    for key, value in enhanced_result.items():
        if value:
            print(f"  {key}: {value}")

if __name__ == "__main__":
    test_nlp_extraction()
