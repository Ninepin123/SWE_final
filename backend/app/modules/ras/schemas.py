"""RAS — Pydantic schema。介面契約同步在 docs/API.md。"""
from datetime import datetime

from pydantic import BaseModel


class ReviewDecision(BaseModel):
    result: str  # APPROVED / REJECTED / NEED_SUPPLEMENT
    comment: str | None = None


class ReviewApplicationOut(BaseModel):
    application_id: int
    student_id: int
    student_name: str | None = None
    scholarship_id: int
    scholarship_name: str | None = None
    gpa: float | None = None
    status: str
    statement: str | None = None
    created_at: datetime
