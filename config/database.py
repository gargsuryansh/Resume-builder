import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# === Load .env file ===
load_dotenv()

# === Get DATABASE_URL from .env ===
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file! Please check your .env file.")

print("DATABASE_URL loaded successfully from .env")   # Debugging line

# === Create Engine (Neon Postgres optimized) ===
engine = create_engine(
    DATABASE_URL,
    echo=False,           # Development mein True kar sakte ho
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()