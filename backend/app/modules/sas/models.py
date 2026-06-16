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
    # 狀態：審核中 / 需補件 / 已通過 / 未通過（NUKSAMS014）
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="UNDER_REVIEW")
    statement: Mapped[str | None] = mapped_column(Text)  # 申請理由/自述（v1 以文字代替文件上傳）
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
