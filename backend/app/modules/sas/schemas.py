"""SAS — Pydantic schema。介面契約同步在 docs/API.md。"""
from datetime import datetime

from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    scholarship_id: int
    statement: str | None = None          # 申請理由
    contact_phone: str | None = None
    address: str | None = None
    household_status: str | None = None
    academic_note: str | None = None


class ApplicationOut(BaseModel):
    application_id: int
    scholarship_id: int
    scholarship_name: str | None = None
    status: str
    statement: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    household_status: str | None = None
    academic_note: str | None = None
    created_at: datetime


class ProfileOut(BaseModel):
    # 唯讀身分資料（來自 users）
    user_id: int
    account: str
    name: str
    email: str | None = None
    department: str | None = None
    gpa: float | None = None
    # 可編輯欄位（來自 student_profiles）
    contact_phone: str | None = None
    address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None


class ProfileUpdate(BaseModel):
    contact_phone: str | None = None
    address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
