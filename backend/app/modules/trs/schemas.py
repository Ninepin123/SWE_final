"""TRS — Pydantic schema。介面契約同步在 docs/API.md。"""
from datetime import datetime

from pydantic import BaseModel


class RecommendationRequestCreate(BaseModel):
    application_id: int
    teacher_id: int


class RecommendationLetterUpdate(BaseModel):
    content: str | None = None
    submit: bool = False  # True = 送出（SUBMITTED），False = 存草稿（DRAFT）


# 給老師看：含推薦信內容
class RecommendationTeacherOut(BaseModel):
    rec_id: int
    application_id: int
    student_id: int | None = None
    teacher_id: int | None = None
    student_name: str | None = None
    student_account: str | None = None
    scholarship_name: str | None = None
    deadline: datetime | None = None
    content: str | None = None
    status: str
    submitted_at: datetime | None = None
    updated_at: datetime


# 給學生看：只有狀態，看不到內容（隱私 7.2.5）
class RecommendationStudentOut(BaseModel):
    rec_id: int
    application_id: int
    teacher_id: int | None = None
    scholarship_name: str | None = None
    teacher_name: str | None = None
    status: str
    deadline: datetime | None = None
    submitted_at: datetime | None = None
    updated_at: datetime


class RecommendationStudentProfileStudentOut(BaseModel):
    user_id: int
    name: str
    account: str
    email: str | None = None


class RecommendationStudentProfileProfileOut(BaseModel):
    grade: str | None = None
    identity_type: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None


class RecommendationStudentProfileApplicationOut(BaseModel):
    application_id: int
    status: str
    submitted_at: datetime | None = None


class RecommendationStudentProfileScholarshipOut(BaseModel):
    scholarship_id: int
    name: str
    deadline: datetime | None = None


class RecommendationStudentProfileDocumentOut(BaseModel):
    document_id: int
    document_type: str
    title: str
    content_text: str


class RecommendationStudentProfileOut(BaseModel):
    rec_id: int
    application_id: int
    status: str
    student: RecommendationStudentProfileStudentOut
    profile: RecommendationStudentProfileProfileOut | None = None
    application: RecommendationStudentProfileApplicationOut
    scholarship: RecommendationStudentProfileScholarshipOut
    documents: list[RecommendationStudentProfileDocumentOut]


class TeacherRecommendationDashboardOut(BaseModel):
    total_count: int
    pending_count: int
    draft_count: int
    submitted_count: int
    due_soon_count: int
    overdue_count: int


class DueSoonNotificationRunOut(BaseModel):
    checked_count: int
    created_count: int
