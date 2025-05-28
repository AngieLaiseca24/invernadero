import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = None

def init_db():
    global client
    MONGO_URI = os.getenv("MONGO_URI")
    client = MongoClient(MONGO_URI)

def get_db():
    global client

    if client is None:
        MONGO_URI = os.getenv("MONGO_URI")
        if not MONGO_URI:
            raise RuntimeError("❌ MONGO_URI no está definido en el archivo .env")
        client = MongoClient(MONGO_URI)

    return client["invernadero_db"]