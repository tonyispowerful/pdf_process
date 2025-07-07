from pymongo import MongoClient
from config import MONGO_URI, DB_NAME, COLLECTION_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def insert_bid_data(data):
    collection.insert_one(data)

def bid_exists(file_name):
    return collection.find_one({"file_name": file_name}) is not None

