"""NCS — 商業邏輯層（站內通知與公告，需求書 9.2）。

create_notification() 是提供給其他子系統的共用介面：
SAS / RAS / TRS 在關鍵事件發生時呼叫它寫入通知，不直接操作 notifications 表以外的事。
"""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.aas.models import User
from app.modules.ncs.models import Announcement, Notification
from app.modules.ncs.schemas import AnnouncementCreate


def create_notification(db: Session, user_id: int, title: str, body: str | None = None, commit: bool = True) -> Notification:
    n = Notification(user_id=user_id, title=title, body=body, is_read=False)
    db.add(n)
    if commit:
        db.commit()
    return n


def list_my(db: Session, user: User) -> list[Notification]:
    return list(
        db.scalars(
            select(Notification).where(Notification.user_id == user.user_id).order_by(Notification.created_at.desc())
        )
    )


def unread_count(db: Session, user: User) -> int:
    return len(
        list(
            db.scalars(
                select(Notification).where(Notification.user_id == user.user_id, Notification.is_read == False)  # noqa: E712
            )
        )
    )


def mark_read(db: Session, user: User, notification_id: int) -> Notification:
    n = db.get(Notification, notification_id)
    if n is None or n.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="找不到通知")
    n.is_read = True
    db.commit()
    return n


def list_announcements(db: Session) -> list[Announcement]:
    return list(db.scalars(select(Announcement).order_by(Announcement.created_at.desc())))


def create_announcement(db: Session, data: AnnouncementCreate, current: User) -> Announcement:
    a = Announcement(title=data.title, body=data.body, created_by=current.user_id)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a
