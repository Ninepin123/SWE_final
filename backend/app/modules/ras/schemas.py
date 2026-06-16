"""RAS — Pydantic schema。介面契約同步在 docs/API.md。"""
from datetime import datetime

from pydantic import BaseModel


class ReviewDecision(BaseModel):
    result: str  # APPROVED / REJECTED / NEED_SUPPLEMENT
    comment: str | None = None


class ReviewRecommendation(BaseModel):
    teacher_name: str | None = None
    content: str | None = None


class ReviewApplicationOut(BaseModel):
    application_id: int
    student_id: int
    student_name: str | None = None
    scholarship_id: int
    scholarship_name: str | None = None
    gpa: float | None = None
    status: str
    # 申請表內容（審查人員可見全部）
    statement: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    household_status: str | None = None
    academic_note: str | None = None
    created_at: datetime
    # 最近一次審查紀錄（item 6：審查人員/結果/時間/意見）
    reviewer_name: str | None = None
    review_result: str | None = None
    review_comment: str | None = None
    reviewed_at: datetime | None = None
    # 已送出的推薦信（僅審查人員可見內容）
    recommendations: list[ReviewRecommendation] = []
