from pymongo import MongoClient
from config import MONGO_URI, DB_NAME, COLLECTION_NAME
import pandas as pd

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def insert_bid_data(data):
    """插入招标数据到 MongoDB"""
    collection.insert_one(data)

def bid_exists(file_name):
    """检查招标数据是否已存在"""
    return collection.find_one({"file_name": file_name}) is not None

def get_all_data():
    """获取所有数据"""
    return list(collection.find())

def get_unique_data():
    """获取文件名不重复的数据"""
    pipeline = [
        {
            "$group": {
                "_id": "$文件名",  # 按文件名分组
                "doc": {"$first": "$$ROOT"}  # 取每组的第一个文档
            }
        },
        {
            "$replaceRoot": {"newRoot": "$doc"}  
        }
    ]
    return list(collection.aggregate(pipeline))

def get_data_by_file_type(file_type):
    """根据文件类型获取数据"""
    return list(collection.find({"文件类型": file_type}))

def get_data_by_file_name(file_name):
    """根据文件名获取单个文档数据"""
    return collection.find_one({"文件名": file_name})

def get_bidding_files():
    """获取所有招标文件"""
    return list(collection.find({"文件类型": "招标文件"}))

def get_tender_files():
    """获取所有投标文件"""
    return list(collection.find({"文件类型": "投标文件"}))

def export_to_pandas():
    """导出所有数据为 pandas DataFrame"""
    data = get_all_data()
    if data:
        # 移除 MongoDB 的 _id 字段
        for item in data:
            if '_id' in item:
                del item['_id']
        return pd.DataFrame(data)
    return pd.DataFrame()
    
def export_to_pandas_by_type(file_type):
    """根据文件类型导出数据为 pandas DataFrame"""
    data = get_data_by_file_type(file_type)
    if data:
        # 移除 MongoDB 的 _id 字段
        for item in data:
            if '_id' in item:
                del item['_id']
        return pd.DataFrame(data)
    return pd.DataFrame()

      
def export_to_csv(file_type=None, output_dir="./"):
    """分类导出 CSV 文件"""
    import os
    
    if file_type:
        # 导出指定类型
        df = export_to_pandas_by_type(file_type)
        if not df.empty:
            filename = os.path.join(output_dir, f"{file_type}_data.csv")
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"{file_type}数据已导出到: {filename}")
            return True
        else:
            print(f"没有{file_type}数据可导出")
            return False
    else:
        # 分别导出招标文件和投标文件
        results = {}
        
        # 导出招标文件
        bidding_df = export_to_pandas_by_type("招标文件")
        if not bidding_df.empty:
            bidding_filename = os.path.join(output_dir, "招标文件_data.csv")
            bidding_df.to_csv(bidding_filename, index=False, encoding='utf-8-sig')
            print(f"招标文件数据已导出到: {bidding_filename}")
            results["招标文件"] = bidding_filename
        else:
            print("没有招标文件数据可导出")
        
        # 导出投标文件
        tender_df = export_to_pandas_by_type("投标文件")
        if not tender_df.empty:
            tender_filename = os.path.join(output_dir, "投标文件_data.csv")
            tender_df.to_csv(tender_filename, index=False, encoding='utf-8-sig')
            print(f"投标文件数据已导出到: {tender_filename}")
            results["投标文件"] = tender_filename
        else:
            print("没有投标文件数据可导出")
        
        return results

def export_to_excel(filename="all_data.xlsx"):
    """导出到 Excel 文件，分工作表保存"""
    try:
        # 获取招标文件和投标文件数据
        bidding_df = export_to_pandas_by_type("招标文件")
        tender_df = export_to_pandas_by_type("投标文件")
        
        # 创建 Excel 写入器
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            if not bidding_df.empty:
                bidding_df.to_excel(writer, sheet_name='招标文件', index=False)
                print(f"招标文件数据已写入工作表: 招标文件")
            
            if not tender_df.empty:
                tender_df.to_excel(writer, sheet_name='投标文件', index=False)
                print(f"投标文件数据已写入工作表: 投标文件")
            
            # 如果两个都为空，创建一个空的汇总表
            if bidding_df.empty and tender_df.empty:
                empty_df = pd.DataFrame({"提示": ["没有数据可导出"]})
                empty_df.to_excel(writer, sheet_name='汇总', index=False)
        
        print(f"Excel 文件已导出到: {filename}")
        return True
        
    except Exception as e:
        print(f"导出 Excel 文件失败: {e}")
        return False

def get_data_by_company(company_name):
    """根据公司名称获取相关数据"""
    query = {
        "$or": [
            {"采购人名称": {"$regex": company_name, "$options": "i"}},
            {"投标单位": {"$regex": company_name, "$options": "i"}},
            {"招标单位名称": {"$regex": company_name, "$options": "i"}}
        ]
    }
    return list(collection.find(query))      