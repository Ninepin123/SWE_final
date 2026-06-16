"""NCS — Pydantic schema。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    notification_id: int
    title: str
    body: str | None = None
    is_read: bool
    created_at: datetime


class AnnouncementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    announcement_id: int
    title: str
    body: str | None = None
    created_by: int | None = None
    created_at: datetime


class AnnouncementCreate(BaseModel):
    title: str
    body: str | None = None
