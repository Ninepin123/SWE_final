"""RAS 審查與核發 — API 路由
需求書：Chapter 8。範圍：審查人員查看申請案（GPA 排序、含推薦信與審查紀錄）、做出審查決定。
注意：依需求僅「審查單位 / 審查人員(REVIEWER)」可審查（管理員不參與審查）。
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.aas.models import User
from app.modules.aas.security import require_roles
from app.modules.ras import service
from app.modules.ras.schemas import ReviewApplicationOut, ReviewDecision

router = APIRouter(prefix="/api/ras", tags=["RAS 審查與核發"])


@router.get("/applications", response_model=list[ReviewApplicationOut])
def list_applications(
    scholarship_id: int | None = None,
    sort_by: str = "gpa_desc",
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_roles("REVIEWER")),
):
    return service.list_applications_for_review(db, reviewer, scholarship_id, sort_by)


@router.post("/applications/{application_id}/decision")
def decide(
    application_id: int,
    body: ReviewDecision,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_roles("REVIEWER")),
):
    return service.decide(db, reviewer, application_id, body)


@router.post("/applications/{application_id}/view")
def log_view(
    application_id: int,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_roles("REVIEWER")),
):
    return service.log_application_view(db, reviewer, application_id)


from app.modules.ras.schemas import AwardListItem, AnnualStatisticsOut

@router.get("/award-list", response_model=list[AwardListItem])
def get_award_list(
    year: int | None = None,
    scholarship_id: int | None = None,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_roles("REVIEWER", "ADMIN")),
):
    return service.get_award_list(db, reviewer, year, scholarship_id)


@router.get("/statistics", response_model=AnnualStatisticsOut)
def get_statistics(
    year: int | None = None,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_roles("REVIEWER", "ADMIN")),
):
    return service.get_annual_statistics(db, reviewer, year)


from fastapi.responses import Response

@router.get("/statistics/export")
def export_statistics(
    year: int | None = None,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_roles("REVIEWER", "ADMIN")),
):
    csv_content = service.export_statistics_csv(db, reviewer, year)
    
    # 避免中文檔名問題，使用 url 標籤或簡單英文檔名
    filename = f"statistics_{year}.csv" if year else "statistics_all.csv"
    headers = {
        "Content-Disposition": f"attachment; filename={filename}"
    }
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers=headers
    )


