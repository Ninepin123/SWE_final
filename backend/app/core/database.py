"""資料庫連線（組長維護）。

所有子系統一律透過這裡的 get_db 取得 Session，
不要自己建立 engine 或連線字串。

用法（FastAPI dependency injection）：

    from fastapi import Depends
    from sqlalchemy.orm import Session
    from app.core.database import get_db

    @router.get("/items")
    def list_items(db: Session = Depends(get_db)):
        ...
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """所有 SQLAlchemy model 的共同基底，各模組的 models.py 請繼承這個。"""


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
