"""TRS — SQLAlchemy 資料模型（對應 database/schema/04_trs_tables.sql）。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = (UniqueConstraint("application_id", "teacher_id", name="uq_app_teacher"),)

    rec_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.application_id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="REQUESTED")  # REQUESTED/DRAFT/SUBMITTED
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
