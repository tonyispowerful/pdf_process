# 测试能否正确提取中文大写金额

from utils import extract_amount

test_text = """
我公司投标报价为壹佰贰拾万元整，项目预算为95万元，履约保证金为5000元，
也有写成中文大写金额：伍仟圆，或人民币陆拾万元正。还可能出现多个金额：350000元、2.8万元。
"""

amounts = extract_amount(test_text)

print("提取到的金额如下（单位：元）：")
for amt in amounts:
    print(f"  - {amt:.2f}")

print(f"共提取 {len(amounts)} 个金额")
