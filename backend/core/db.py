# app/db.py
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load .env file into process env (looks in current working dir by default)
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    pool_recycle=300,
    connect_args={"sslmode": "require"},
)