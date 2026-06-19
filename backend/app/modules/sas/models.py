"""SAS — SQLAlchemy 資料模型（對應 database/schema/03_sas_tables.sql）。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("student_id", "scholarship_id", name="uq_student_scholarship"),)

    application_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    scholarship_id: Mapped[int] = mapped_column(ForeignKey("scholarships.scholarship_id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT")
    # 申請表欄位
    statement: Mapped[str | None] = mapped_column(Text)            # 申請理由 / 自述
    contact_phone: Mapped[str | None] = mapped_column(String(30))  # 聯絡電話
    address: Mapped[str | None] = mapped_column(String(255))       # 通訊地址
    household_status: Mapped[str | None] = mapped_column(Text)     # 家庭狀況
    academic_note: Mapped[str | None] = mapped_column(Text)        # 在學成績 / 排名說明
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), primary_key=True)
    grade: Mapped[str | None] = mapped_column(String(20))
    identity_type: Mapped[str | None] = mapped_column(String(50))
    contact_email: Mapped[str | None] = mapped_column(String(100))
    contact_phone: Mapped[str | None] = mapped_column(String(30))
    address: Mapped[str | None] = mapped_column(String(255))
    emergency_contact_name: Mapped[str | None] = mapped_column(String(100))
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(30))
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
