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
  
def export_to_csv(filename="bidding_data.csv"):
    """导出数据为 CSV 文件"""
    df = export_to_pandas()
    if not df.empty:
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"数据已导出到: {filename}")
        return True
    else:
        print("没有数据可导出")
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