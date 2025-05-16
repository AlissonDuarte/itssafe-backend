import os
from dotenv import load_dotenv
from services.rabbit.producer import Producer
load_dotenv()

db_mode = os.getenv("DB_MODE")
if db_mode=="prd":
    producer = Producer('alerts')
else:
    producer = None