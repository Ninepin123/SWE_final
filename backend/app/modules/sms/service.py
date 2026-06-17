"""SMS — 商業邏輯層（獎學金資料管理，需求書 5.2）。"""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.aas.models import Unit, User
from app.modules.sms.models import Scholarship
from app.modules.sms.schemas import ScholarshipCreate, ScholarshipUpdate

VALID_CATEGORIES = {"SCHOOL", "GOVERNMENT", "PRIVATE", "LOW_INCOME", "MERIT", "OTHER"}
VALID_STATUS = {"OPEN", "CLOSED"}


def _naive(dt: datetime | None) -> datetime | None:
    if dt is not None and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


def _to_out(s: Scholarship, unit_name: str | None) -> dict:
    return {
        "scholarship_id": s.scholarship_id,
        "name": s.name,
        "year": s.year,
        "amount": s.amount,
        "quota": s.quota,
        "min_gpa": float(s.min_gpa) if s.min_gpa is not None else None,
        "department_limit": s.department_limit,
        "category": s.category,
        "description": s.description,
        "deadline": s.deadline,
        "status": s.status,
        "unit_id": s.unit_id,
        "unit_name": unit_name,
    }


def _unit_name(db: Session, unit_id: int) -> str | None:
    unit = db.get(Unit, unit_id)
    return unit.name if unit else None


def _ensure_owner(s: Scholarship, current: User) -> None:
    """獎助單位只能改自己單位的獎學金；管理員不限。"""
    if current.role != "ADMIN" and s.unit_id != current.unit_id:
        raise HTTPException(status_code=403, detail="只能管理自己單位張貼的獎學金")


def list_scholarships(db: Session, only_open: bool = False) -> list[dict]:
    rows = db.execute(
        select(Scholarship, Unit.name)
        .join(Unit, Scholarship.unit_id == Unit.unit_id)
        .order_by(Scholarship.created_at.desc())
    ).all()
    now = datetime.now()
    out: list[dict] = []
    for s, unit_name in rows:
        if only_open:
            if s.status != "OPEN":
                continue
            dl = _naive(s.deadline)
            if dl is not None and dl < now:
                continue
        out.append(_to_out(s, unit_name))
    return out


def get_scholarship(db: Session, scholarship_id: int) -> dict:
    row = db.execute(
        select(Scholarship, Unit.name)
        .join(Unit, Scholarship.unit_id == Unit.unit_id)
        .where(Scholarship.scholarship_id == scholarship_id)
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="找不到獎學金")
    s, unit_name = row
    return _to_out(s, unit_name)


def create_scholarship(db: Session, data: ScholarshipCreate, current: User) -> dict:
    if data.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail="分類不存在")
    if current.unit_id is None:
        raise HTTPException(status_code=400, detail="此帳號未綁定單位，無法建立獎學金")
    s = Scholarship(
        unit_id=current.unit_id,
        name=data.name,
        year=data.year,
        amount=data.amount,
        quota=data.quota,
        min_gpa=data.min_gpa,
        department_limit=data.department_limit,
        category=data.category,
        description=data.description,
        deadline=_naive(data.deadline),
        status="OPEN",
        created_by=current.user_id,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return _to_out(s, _unit_name(db, s.unit_id))


def _get_owned(db: Session, scholarship_id: int, current: User) -> Scholarship:
    s = db.get(Scholarship, scholarship_id)
    if s is None:
        raise HTTPException(status_code=404, detail="找不到獎學金")
    _ensure_owner(s, current)
    return s


def update_scholarship(db: Session, scholarship_id: int, data: ScholarshipUpdate, current: User) -> dict:
    s = _get_owned(db, scholarship_id, current)
    payload = data.model_dump(exclude_unset=True)
    if "category" in payload and payload["category"] not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail="分類不存在")
    if "status" in payload and payload["status"] not in VALID_STATUS:
        raise HTTPException(status_code=400, detail="狀態不存在")
    if "deadline" in payload:
        payload["deadline"] = _naive(payload["deadline"])
    for key, value in payload.items():
        setattr(s, key, value)
    db.commit()
    db.refresh(s)
    return _to_out(s, _unit_name(db, s.unit_id))


def delete_scholarship(db: Session, scholarship_id: int, current: User) -> None:
    s = _get_owned(db, scholarship_id, current)
    try:
        db.delete(s)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="此獎學金已有學生申請，無法刪除；可改為將狀態設為「已關閉」。")
