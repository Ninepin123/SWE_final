"""SAS — Pydantic schema。介面契約同步在 docs/API.md。"""
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ApplicationCreate(BaseModel):
    scholarship_id: int
    statement: str | None = None          # 申請理由
    contact_phone: str | None = None
    address: str | None = None
    household_status: str | None = None
    academic_note: str | None = None


class ApplicationUpdate(BaseModel):
    statement: str | None = None
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
    updated_at: datetime
    submitted_at: datetime | None = None
    can_edit: bool


class ApplicationDocumentWrite(BaseModel):
    document_type: str
    title: str = Field(min_length=1, max_length=100)
    content_text: str = Field(min_length=1, max_length=20000)


class ApplicationDocumentOut(BaseModel):
    document_id: int
    application_id: int
    document_type: str
    title: str
    content_text: str
    created_at: datetime
    updated_at: datetime


class SupplementRequestCreate(BaseModel):
    required_items: str = Field(min_length=1, max_length=2000)
    deadline: datetime


class SupplementSubmit(BaseModel):
    response_text: str = Field(min_length=1, max_length=20000)


class SupplementRequestOut(BaseModel):
    supplement_id: int
    application_id: int
    reviewer_id: int
    required_items: str
    deadline: datetime
    status: str
    response_text: str | None = None
    created_at: datetime
    submitted_at: datetime | None = None
    can_submit: bool


class ApplicationEventOut(BaseModel):
    event_id: int
    application_id: int
    actor_id: int | None = None
    actor_name: str | None = None
    actor_role: str | None = None
    event_type: str
    from_status: str | None = None
    to_status: str | None = None
    detail: str | None = None
    created_at: datetime


class ProfileOut(BaseModel):
    # 唯讀身分資料（來自 users）
    user_id: int
    account: str
    name: str
    department: str | None = None
    grade: str | None = None
    gpa: float | None = None
    identity_type: str | None = None
    # 可編輯欄位（來自 student_profiles）
    email: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None


class ProfileUpdate(BaseModel):
    email: str | None = Field(default=None, max_length=100)
    contact_phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=255)
    emergency_contact_name: str | None = Field(default=None, max_length=100)
    emergency_contact_phone: str | None = Field(default=None, max_length=30)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return value
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("Email 格式不正確")
        return value


class ScholarshipEligibilityOut(BaseModel):
    scholarship_id: int
    name: str
    year: int
    amount: int
    quota: int
    remaining_quota: int
    min_gpa: float | None = None
    department_limit: str | None = None
    category: str
    description: str | None = None
    deadline: datetime | None = None
    status: str
    unit_id: int
    unit_name: str | None = None
    contact_email: str | None = None
    required_documents: list[str] = Field(default_factory=list)
    already_applied: bool
    can_apply: bool
    ineligibility_reasons: list[str]
