"""AAS — SQLAlchemy 資料模型（對應 database/schema/01_aas_tables.sql）。

規則：欄位必須與 SQL 一致，改資料表時兩邊一起改、同一個 PR 提交。
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Unit(Base):
    __tablename__ = "units"

    unit_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="OTHER")
    contact_email: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)  # bcrypt 雜湊
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # STUDENT/TEACHER/SPONSOR/REVIEWER/ADMIN
    unit_id: Mapped[int | None] = mapped_column(ForeignKey("units.unit_id"))
    gpa: Mapped[float | None] = mapped_column(Numeric(3, 2))        # v1 簡化：學生 GPA 暫存於此（SAS 個人資料後續再拆出）
    department: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
