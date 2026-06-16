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
    student_name: str | None = None
    scholarship_name: str | None = None
    content: str | None = None
    status: str
    updated_at: datetime


# 給學生看：只有狀態，看不到內容（隱私 7.2.5）
class RecommendationStudentOut(BaseModel):
    rec_id: int
    application_id: int
    scholarship_name: str | None = None
    teacher_name: str | None = None
    status: str
    updated_at: datetime
