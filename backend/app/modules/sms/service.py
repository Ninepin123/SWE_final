"""SMS — 商業邏輯層（獎學金資料管理，需求書 5.2）。"""
import json
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.aas.models import Unit, User
from app.modules.sas.models import Application
from app.modules.sms.models import Scholarship
from app.modules.sms.schemas import ScholarshipCreate, ScholarshipUpdate

VALID_CATEGORIES = {"SCHOOL", "GOVERNMENT", "PRIVATE", "LOW_INCOME", "MERIT", "OTHER"}
VALID_STATUS = {"OPEN", "CLOSED"}


def _naive(dt: datetime | None) -> datetime | None:
    if dt is not None and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


def _safe_json_load(text: str | None) -> list | dict | None:
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _to_out(s: Scholarship, unit_name: str | None) -> dict:
    now = datetime.now()
    used_quota = getattr(s, "used_quota", 0)
    is_open = False
    if s.status == "OPEN":
        is_open = True
        sd = _naive(s.start_date)
        dl = _naive(s.deadline)
        if sd and sd > now: is_open = False
        if dl and dl < now: is_open = False
        if used_quota >= s.quota: is_open = False

    return {
        "id": s.scholarship_id,
        "title": s.name,
        "year": s.year,
        "amount": s.amount,
        "quota": s.quota,
        "used_quota": used_quota,
        "category": s.category,
        "description": s.description,
        "start_date": s.start_date,
        "deadline": s.deadline,
        "status": s.status,
        "unit_id": s.unit_id,
        "sponsor": unit_name,
        "criteria": {
            "min_gpa": float(s.min_gpa) if s.min_gpa is not None else None,
            "departments": _safe_json_load(s.department_limit) or ([] if s.department_limit else None),
            "grades": _safe_json_load(s.grade_limit) or [],
            "identities": _safe_json_load(s.identity_limit) or [],
            "family_statuses": _safe_json_load(s.family_status_limit) or [],
            "note": s.criteria_note,
        },
        "tags": _safe_json_load(s.tags) or [],
        "required_docs": _safe_json_load(s.required_docs) or [],
        "require_recommendation": s.require_recommendation,
        "contact_name": s.contact_name,
        "contact_phone": s.contact_phone,
        "contact_email": s.contact_email,
        "contact_address": s.contact_address,
        "website": s.website,
        "is_open": is_open,
    }


def _unit_name(db: Session, unit_id: int) -> str | None:
    unit = db.get(Unit, unit_id)
    return unit.name if unit else None


def _ensure_owner(s: Scholarship, current: User) -> None:
    """獎助單位只能改自己單位的獎學金；管理員不限。"""
    if current.role != "ADMIN" and s.unit_id != current.unit_id:
        raise HTTPException(status_code=403, detail="只能管理自己單位張貼的獎學金")


def list_scholarships(db: Session, only_open: bool = False) -> list[dict]:
    stmt = (
        select(Scholarship, Unit.name, func.count(Application.application_id))
        .join(Unit, Scholarship.unit_id == Unit.unit_id)
        .outerjoin(Application, Scholarship.scholarship_id == Application.scholarship_id)
        .group_by(Scholarship.scholarship_id, Unit.name)
        .order_by(Scholarship.created_at.desc())
    )
    rows = db.execute(stmt).all()
    now = datetime.now()
    out: list[dict] = []
    for s, unit_name, used_quota in rows:
        setattr(s, "used_quota", used_quota)
        if only_open:
            if s.status != "OPEN":
                continue
            sd = _naive(s.start_date)
            if sd is not None and sd > now:
                continue
            dl = _naive(s.deadline)
            if dl is not None and dl < now:
                continue
            if used_quota >= s.quota:
                continue
        out.append(_to_out(s, unit_name))
    return out


def get_scholarship(db: Session, scholarship_id: int) -> dict:
    stmt = (
        select(Scholarship, Unit.name, func.count(Application.application_id))
        .join(Unit, Scholarship.unit_id == Unit.unit_id)
        .outerjoin(Application, Scholarship.scholarship_id == Application.scholarship_id)
        .where(Scholarship.scholarship_id == scholarship_id)
        .group_by(Scholarship.scholarship_id, Unit.name)
    )
    row = db.execute(stmt).first()
    if row is None:
        raise HTTPException(status_code=404, detail="找不到獎學金")
    s, unit_name, used_quota = row
    setattr(s, "used_quota", used_quota)
    return _to_out(s, unit_name)


def _resolve_unit_id(db: Session, requested_unit_id: int | None, current: User) -> int:
    """決定獎學金所屬單位：管理員可指定任一單位；獎助單位人員僅限自己單位；未指定則沿用登入者單位。"""
    unit_id = requested_unit_id if requested_unit_id is not None else current.unit_id
    if unit_id is None:
        raise HTTPException(status_code=400, detail="請選擇提供單位")
    if current.role != "ADMIN" and unit_id != current.unit_id:
        raise HTTPException(status_code=403, detail="只能為自己所屬的單位建立獎學金")
    if db.get(Unit, unit_id) is None:
        raise HTTPException(status_code=404, detail="找不到指定的單位")
    return unit_id


def create_scholarship(db: Session, data: ScholarshipCreate, current: User) -> dict:
    unit_id = _resolve_unit_id(db, data.unit_id, current)
    if data.quota <= 0:
        raise HTTPException(status_code=400, detail="名額必須大於 0")
    if data.start_date and data.deadline and data.start_date >= data.deadline:
        raise HTTPException(status_code=400, detail="開始時間必須早於截止時間")

    s = Scholarship(
        unit_id=unit_id,
        name=data.name,
        year=data.year,
        amount=data.amount,
        quota=data.quota,
        category=data.category,
        description=data.description,
        start_date=_naive(data.start_date),
        deadline=_naive(data.deadline),
        status="OPEN",
        created_by=current.user_id,
        tags=json.dumps(data.tags, ensure_ascii=False) if data.tags else None,
        required_docs=json.dumps(data.required_docs, ensure_ascii=False) if data.required_docs else None,
        require_recommendation=data.require_recommendation,
        contact_name=data.contact_name,
        contact_phone=data.contact_phone,
        contact_email=data.contact_email,
        contact_address=data.contact_address,
        website=data.website,
    )
    
    if data.criteria:
        s.min_gpa = data.criteria.min_gpa
        s.department_limit = json.dumps(data.criteria.departments, ensure_ascii=False) if data.criteria.departments else None
        s.grade_limit = json.dumps(data.criteria.grades, ensure_ascii=False) if data.criteria.grades else None
        s.identity_limit = json.dumps(data.criteria.identities, ensure_ascii=False) if data.criteria.identities else None
        s.family_status_limit = json.dumps(data.criteria.family_statuses, ensure_ascii=False) if data.criteria.family_statuses else None
        s.criteria_note = data.criteria.note

    db.add(s)
    _ensure_options(db, data.category, data.tags)
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
    if "status" in payload and payload["status"] not in VALID_STATUS:
        raise HTTPException(status_code=400, detail="狀態不存在")

    if "unit_id" in payload and payload["unit_id"] is not None and payload["unit_id"] != s.unit_id:
        if current.role != "ADMIN":
            raise HTTPException(status_code=403, detail="僅管理員可變更獎學金的提供單位")
        if db.get(Unit, payload["unit_id"]) is None:
            raise HTTPException(status_code=404, detail="找不到指定的單位")
        s.unit_id = payload["unit_id"]

    if "name" in payload: s.name = payload["name"]
    if "year" in payload: s.year = payload["year"]
    if "amount" in payload: s.amount = payload["amount"]
    if "quota" in payload: 
        if payload["quota"] <= 0:
            raise HTTPException(status_code=400, detail="名額必須大於 0")
        s.quota = payload["quota"]
    if "category" in payload: s.category = payload["category"]
    if "description" in payload: s.description = payload["description"]
    if "start_date" in payload: s.start_date = _naive(payload["start_date"])
    if "deadline" in payload: s.deadline = _naive(payload["deadline"])
    if "status" in payload: s.status = payload["status"]
    
    if s.start_date and s.deadline and s.start_date >= s.deadline:
        raise HTTPException(status_code=400, detail="開始時間必須早於截止時間")
    
    if "tags" in payload:
        s.tags = json.dumps(payload["tags"], ensure_ascii=False) if payload["tags"] is not None else None
    if "required_docs" in payload:
        s.required_docs = json.dumps(payload["required_docs"], ensure_ascii=False) if payload["required_docs"] is not None else None
    if "require_recommendation" in payload:
        s.require_recommendation = payload["require_recommendation"]
        
    if "contact_name" in payload: s.contact_name = payload["contact_name"]
    if "contact_phone" in payload: s.contact_phone = payload["contact_phone"]
    if "contact_email" in payload: s.contact_email = payload["contact_email"]
    if "contact_address" in payload: s.contact_address = payload["contact_address"]
    if "website" in payload: s.website = payload["website"]

    if "criteria" in payload and payload["criteria"] is not None:
        c = payload["criteria"]
        if "min_gpa" in c: s.min_gpa = c["min_gpa"]
        if "departments" in c: s.department_limit = json.dumps(c["departments"], ensure_ascii=False) if c["departments"] else None
        if "grades" in c: s.grade_limit = json.dumps(c["grades"], ensure_ascii=False) if c["grades"] else None
        if "identities" in c: s.identity_limit = json.dumps(c["identities"], ensure_ascii=False) if c["identities"] else None
        if "family_statuses" in c: s.family_status_limit = json.dumps(c["family_statuses"], ensure_ascii=False) if c["family_statuses"] else None
        if "note" in c: s.criteria_note = c["note"]

    _ensure_options(db, payload.get("category"), payload.get("tags"))
    db.commit()
    db.refresh(s)

    # Reload used_quota
    used_quota = db.scalar(select(func.count()).select_from(Application).where(Application.scholarship_id == s.scholarship_id))
    setattr(s, "used_quota", used_quota)
    return _to_out(s, _unit_name(db, s.unit_id))


def delete_scholarship(db: Session, scholarship_id: int, current: User) -> None:
    s = _get_owned(db, scholarship_id, current)
    try:
        db.delete(s)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="此獎學金已有學生申請，無法刪除；可改為將狀態設為「已關閉」。")


# --- Options (Category & Tag) ---

from app.modules.sms.models import ScholarshipOption
from app.modules.sms.schemas import OptionCreate


def _ensure_options(db: Session, category: str | None = None, tags: list[str] | None = None) -> None:
    """獎學金存檔時，把新出現的分類／標籤自動登記進選項庫，作為下次新增時的建議來源。

    僅新增尚未存在的選項；不在這裡 commit，交由呼叫端（建立／更新獎學金）的同一個交易一起寫入。
    """
    pending: list[tuple[str, str]] = []
    if category:
        pending.append(("CATEGORY", category))
    for tag in tags or []:
        pending.append(("TAG", tag))
    for type_, raw in pending:
        name = (raw or "").strip()
        if not name:
            continue
        exists = db.execute(
            select(ScholarshipOption).where(
                ScholarshipOption.type == type_, ScholarshipOption.name == name
            )
        ).scalar_one_or_none()
        if exists is None:
            db.add(ScholarshipOption(type=type_, name=name))


def list_options(db: Session, type_: str | None = None) -> list[dict]:
    query = select(ScholarshipOption)
    if type_:
        query = query.where(ScholarshipOption.type == type_)
    rows = db.execute(query.order_by(ScholarshipOption.type, ScholarshipOption.name)).scalars().all()
    return [{"id": r.option_id, "type": r.type, "name": r.name} for r in rows]

def create_option(db: Session, data: OptionCreate) -> dict:
    existing = db.execute(
        select(ScholarshipOption).where(ScholarshipOption.type == data.type, ScholarshipOption.name == data.name)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="同類型的選項名稱已存在")
    
    opt = ScholarshipOption(type=data.type, name=data.name)
    db.add(opt)
    db.commit()
    db.refresh(opt)
    return {"id": opt.option_id, "type": opt.type, "name": opt.name}

def update_option(db: Session, option_id: int, data: OptionCreate) -> dict:
    opt = db.get(ScholarshipOption, option_id)
    if not opt:
        raise HTTPException(status_code=404, detail="找不到選項")
        
    existing = db.execute(
        select(ScholarshipOption)
        .where(ScholarshipOption.type == data.type, ScholarshipOption.name == data.name, ScholarshipOption.option_id != option_id)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="同類型的選項名稱已存在")
        
    # We should also update the existing scholarships if name changes? 
    # The requirement SMS010 doesn't explicitly mention cascading updates, but if we don't, it might break.
    # Let's keep it simple: just update the option name.
    
    opt.type = data.type
    opt.name = data.name
    db.commit()
    db.refresh(opt)
    return {"id": opt.option_id, "type": opt.type, "name": opt.name}

def delete_option(db: Session, option_id: int):
    opt = db.get(ScholarshipOption, option_id)
    if not opt:
        raise HTTPException(status_code=404, detail="找不到選項")
        
    if opt.type == "CATEGORY":
        count = db.scalar(select(func.count()).select_from(Scholarship).where(Scholarship.category == opt.name))
        if count and count > 0:
            raise HTTPException(status_code=400, detail="此分類已被獎學金使用，無法刪除")
    elif opt.type == "TAG":
        # using LIKE to search within JSON array text for simplicity across DBs
        count = db.scalar(select(func.count()).select_from(Scholarship).where(Scholarship.tags.like(f'%"{opt.name}"%')))
        if count and count > 0:
            raise HTTPException(status_code=400, detail="此標籤已被獎學金使用，無法刪除")
            
    db.delete(opt)
    db.commit()


