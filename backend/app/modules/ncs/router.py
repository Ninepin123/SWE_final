"""NCS 通知與溝通 — API 路由
需求書：Chapter 9。v1 範圍：站內通知（列表/未讀數/標記已讀）與公告（列表 + 管理員發布）。
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.aas.models import User
from app.modules.aas.security import get_current_user, require_roles
from app.modules.ncs import service
from app.modules.ncs.schemas import AnnouncementCreate, AnnouncementOut, NotificationOut

router = APIRouter(prefix="/api/ncs", tags=["NCS 通知與溝通"])


@router.get("/notifications", response_model=list[NotificationOut])
def my_notifications(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return service.list_my(db, current)


@router.get("/notifications/unread_count")
def unread_count(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return {"count": service.unread_count(db, current)}


@router.post("/notifications/{notification_id}/read")
def mark_read(notification_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    service.mark_read(db, current, notification_id)
    return {"detail": "已標記為已讀"}


@router.get("/announcements", response_model=list[AnnouncementOut])
def announcements(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return service.list_announcements(db)


@router.post("/announcements", response_model=AnnouncementOut, status_code=status.HTTP_201_CREATED)
def create_announcement(
    body: AnnouncementCreate, db: Session = Depends(get_db), current: User = Depends(require_roles("ADMIN"))
):
    return service.create_announcement(db, body, current)
