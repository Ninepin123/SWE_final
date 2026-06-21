"""RAS — Pydantic schema。介面契約同步在 docs/API.md。"""
from datetime import datetime

from pydantic import BaseModel


class ReviewDecision(BaseModel):
    result: str  # APPROVED / REJECTED / NEED_SUPPLEMENT
    comment: str | None = None
    supplement_deadline: datetime | None = None


class ReviewRecommendation(BaseModel):
    rec_id: int | None = None
    teacher_name: str | None = None
    status: str | None = None
    content: str | None = None
    content_available: bool = False


class ReviewDocument(BaseModel):
    title: str
    document_type: str | None = None
    content_text: str | None = None


class ReviewApplicationOut(BaseModel):
    application_id: int
    student_id: int
    student_name: str | None = None
    scholarship_id: int
    scholarship_name: str | None = None
    gpa: float | None = None
    status: str
    supplement_deadline: datetime | None = None
    # 申請表內容（審查人員可見全部）
    statement: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    household_status: str | None = None
    academic_note: str | None = None
    documents: list[ReviewDocument] = []
    created_at: datetime
    # 最近一次審查紀錄（item 6：審查人員/結果/時間/意見）
    reviewer_name: str | None = None
    review_result: str | None = None
    review_comment: str | None = None
    reviewed_at: datetime | None = None
    # 已送出的推薦信（僅審查人員可見內容）
    recommendations: list[ReviewRecommendation] = []


class AwardListItem(BaseModel):
    application_id: int
    student_id: int
    student_name: str | None = None
    student_account: str | None = None
    department: str | None = None
    scholarship_id: int
    scholarship_name: str | None = None
    year: int
    amount: int
    status: str
    reviewed_at: datetime | None = None


class UnitStatistics(BaseModel):
    unit_name: str
    total_applications: int
    approved_count: int
    pass_rate: float


class AnnualStatisticsOut(BaseModel):
    year: int | None = None
    total_winners: int
    total_amount: int
    unit_stats: list[UnitStatistics]
