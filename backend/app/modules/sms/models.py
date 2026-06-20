"""SMS — SQLAlchemy 資料模型（對應 database/schema/02_sms_tables.sql）。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Scholarship(Base):
    __tablename__ = "scholarships"

    scholarship_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.unit_id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quota: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    min_gpa: Mapped[float | None] = mapped_column(Numeric(3, 2))
    department_limit: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(20), nullable=False, default="OTHER")
    description: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[datetime | None] = mapped_column(DateTime)
    deadline: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="OPEN")  # OPEN/CLOSED
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    grade_limit: Mapped[str | None] = mapped_column(Text)
    identity_limit: Mapped[str | None] = mapped_column(Text)
    family_status_limit: Mapped[str | None] = mapped_column(Text)
    require_recommendation: Mapped[bool] = mapped_column(default=False)
    required_docs: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[str | None] = mapped_column(Text)
    criteria_note: Mapped[str | None] = mapped_column(Text)
    
    # 聯絡資訊
    contact_name: Mapped[str | None] = mapped_column(String(100))
    contact_phone: Mapped[str | None] = mapped_column(String(50))
    contact_email: Mapped[str | None] = mapped_column(String(100))
    contact_address: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(255))


class ScholarshipOption(Base):
    __tablename__ = "scholarship_options"

    option_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # CATEGORY or TAG
    name: Mapped[str] = mapped_column(String(50), nullable=False)

