import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings

is_serverless = os.getenv("VERCEL") == "1" or os.getenv("SERVERLESS") == "1"

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    poolclass=NullPool if is_serverless else None,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
