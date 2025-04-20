import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()
db_mode = os.getenv("DB_MODE")
db_username = os.getenv("DB_USERNAME")
db_password = os.getenv("DB_PASSWORD")
db_database = os.getenv("DB_DATABASE")
rds_endpoint = os.getenv("RDS_ENDPOINT")
rds_port = os.getenv("RDS_PORT")

if db_mode == "prd":
    DATABASE_URL = f"postgresql://{db_username}:{db_password}@{rds_endpoint}:{rds_port}/{db_database}"
else:
    DATABASE_URL = "postgresql://myuser:mypassword@localhost:5432/mydb"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
