from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# 기본값: 로컬 MySQL (사용자가 환경에 맞게 수정 필요)
# 포맷: mysql+pymysql://<username>:<password>@<host>:<port>/<dbname>
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+pymysql://community_user:secure_password_123!@localhost:3306/community_db"
)

# pool_recycle: MySQL 연결 끊김 방지
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
