"""SMS 獎助學金資料管理 — API 路由
需求書：Chapter 5。範圍：列表/查詢（所有登入者）；單位/管理員的新增/修改/刪除。
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.aas import service as aas_service
from app.modules.aas.models import User
from app.modules.aas.security import get_current_user, require_roles
from app.modules.sms import service
from app.modules.sms.schemas import ScholarshipCreate, ScholarshipOut, ScholarshipUpdate

router = APIRouter(prefix="/api/sms", tags=["SMS 獎助學金資料管理"])


@router.get("/scholarships", response_model=list[ScholarshipOut])
def list_scholarships(only_open: bool = False, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return service.list_scholarships(db, only_open=only_open)


@router.get("/scholarships/{scholarship_id}", response_model=ScholarshipOut)
def get_scholarship(scholarship_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return service.get_scholarship(db, scholarship_id)


@router.post("/scholarships", response_model=ScholarshipOut, status_code=status.HTTP_201_CREATED)
def create_scholarship(
    body: ScholarshipCreate, db: Session = Depends(get_db), current: User = Depends(require_roles("SPONSOR", "ADMIN"))
):
    result = service.create_scholarship(db, body, current)
    aas_service.write_audit(db, current.user_id, "CREATE_SCHOLARSHIP", "scholarship", result["scholarship_id"], f"新增獎學金「{result['name']}」")
    return result


@router.put("/scholarships/{scholarship_id}", response_model=ScholarshipOut)
def update_scholarship(
    scholarship_id: int,
    body: ScholarshipUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_roles("SPONSOR", "ADMIN")),
):
    result = service.update_scholarship(db, scholarship_id, body, current)
    aas_service.write_audit(db, current.user_id, "UPDATE_SCHOLARSHIP", "scholarship", scholarship_id, f"修改獎學金「{result['name']}」")
    return result


@router.delete("/scholarships/{scholarship_id}")
def delete_scholarship(
    scholarship_id: int, db: Session = Depends(get_db), current: User = Depends(require_roles("SPONSOR", "ADMIN"))
):
    service.delete_scholarship(db, scholarship_id, current)
    aas_service.write_audit(db, current.user_id, "DELETE_SCHOLARSHIP", "scholarship", scholarship_id, f"刪除獎學金 #{scholarship_id}")
    return {"detail": "已刪除獎學金"}


# --- Options (Category & Tag) ---
from app.modules.sms.schemas import OptionCreate, OptionOut

@router.get("/options", response_model=list[OptionOut])
def list_options(type: str | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return service.list_options(db, type_=type)

@router.post("/options", response_model=OptionOut, status_code=status.HTTP_201_CREATED)
def create_option(
    body: OptionCreate, db: Session = Depends(get_db), current: User = Depends(require_roles("ADMIN"))
):
    result = service.create_option(db, body)
    aas_service.write_audit(db, current.user_id, "CREATE_OPTION", "scholarship_option", result["id"], f"新增選項「{result['name']}」")
    return result

@router.put("/options/{option_id}", response_model=OptionOut)
def update_option(
    option_id: int, body: OptionCreate, db: Session = Depends(get_db), current: User = Depends(require_roles("ADMIN"))
):
    result = service.update_option(db, option_id, body)
    aas_service.write_audit(db, current.user_id, "UPDATE_OPTION", "scholarship_option", option_id, f"修改選項 #{option_id}")
    return result

@router.delete("/options/{option_id}")
def delete_option(
    option_id: int, db: Session = Depends(get_db), current: User = Depends(require_roles("ADMIN"))
):
    service.delete_option(db, option_id)
    aas_service.write_audit(db, current.user_id, "DELETE_OPTION", "scholarship_option", option_id, f"刪除選項 #{option_id}")
    return {"detail": "已刪除選項"}
