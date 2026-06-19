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
    documents: Mapped[str | None] = mapped_column(Text)            # 上傳之附件(JSON 字串)
    supplement_deadline: Mapped[datetime | None] = mapped_column(DateTime) # 補件期限
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


class ApplicationDocument(Base):
    __tablename__ = "application_documents"
    __table_args__ = (
        UniqueConstraint("application_id", "document_type", name="uq_application_document_type"),
    )

    document_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.application_id"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    # 預留未來實體檔案整合欄位；目前文字文件不使用。
    storage_path: Mapped[str | None] = mapped_column(String(500))
    mime_type: Mapped[str | None] = mapped_column(String(100))
    file_size: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class SupplementRequest(Base):
    __tablename__ = "supplement_requests"

    supplement_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.application_id"), nullable=False
    )
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    required_items: Mapped[str] = mapped_column(Text, nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="REQUESTED")
    response_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)


class ApplicationEvent(Base):
    __tablename__ = "application_events"

    event_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.application_id"), nullable=False
    )
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"))
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(20))
    to_status: Mapped[str | None] = mapped_column(String(20))
    detail: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
