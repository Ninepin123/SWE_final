"""RAS — SQLAlchemy 資料模型（對應 database/schema/05_ras_tables.sql）。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Review(Base):
    __tablename__ = "reviews"

    review_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.application_id"), nullable=False)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    # 審查結果：通過 / 不通過 / 要求補件（8.2.4 / 8.2.5）
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
