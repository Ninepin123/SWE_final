"""NCS — Pydantic schema。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    notification_id: int
    user_id: int
    title: str
    body: str | None = None
    category: str | None = None
    related_type: str | None = None
    related_id: int | None = None
    is_read: bool
    created_at: datetime
    read_at: datetime | None = None


class NotificationCreate(BaseModel):
    user_id: int
    title: str
    body: str | None = None
    category: str | None = None
    related_type: str | None = None
    related_id: int | None = None


class UnreadCountOut(BaseModel):
    unread_count: int


class MarkReadOut(BaseModel):
    notification_id: int
    is_read: bool
    read_at: datetime | None = None


class MarkAllReadOut(BaseModel):
    updated_count: int


class AnnouncementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    announcement_id: int
    title: str
    body: str | None = None
    created_by: int | None = None
    target_role: str | None = None
    is_global: bool = True
    status: str = "PUBLISHED"
    published_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None


class AnnouncementCreate(BaseModel):
    title: str
    body: str | None = None
    target_role: str | None = None
    is_global: bool = True
    status: str = "PUBLISHED"
    expires_at: datetime | None = None
    notify_users: bool = True


class AnnouncementUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    target_role: str | None = None
    is_global: bool | None = None
    status: str | None = None
    expires_at: datetime | None = None


class DeadlineReminderResultOut(BaseModel):
    checked_count: int
    created_count: int
    skipped_duplicate_count: int = 0


class MessageCreate(BaseModel):
    body: str


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: int
    application_id: int
    sender_id: int
    body: str
    created_at: datetime


class IssueReportCreate(BaseModel):
    issue_type: str
    title: str
    description: str
    attachment_name: str | None = None
    attachment_url: str | None = None


class IssueReportUpdate(BaseModel):
    status: str | None = None


class IssueReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    issue_id: int
    reporter_id: int
    issue_type: str
    title: str
    description: str
    attachment_name: str | None = None
    attachment_url: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime | None = None


class IssueReplyCreate(BaseModel):
    body: str


class IssueReplyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reply_id: int
    issue_id: int
    replier_id: int
    body: str
    created_at: datetime


class SystemAlertCreate(BaseModel):
    severity: str = "INFO"
    title: str
    body: str | None = None
    source: str | None = None


class SystemAlertUpdate(BaseModel):
    status: str | None = None


class SystemAlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    alert_id: int
    severity: str
    title: str
    body: str | None = None
    source: str | None = None
    status: str
    created_at: datetime
    resolved_at: datetime | None = None


class EmailLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email_log_id: int
    user_id: int | None = None
    to_email: str | None = None
    subject: str
    body: str | None = None
    status: str
    error_message: str | None = None
    created_at: datetime
