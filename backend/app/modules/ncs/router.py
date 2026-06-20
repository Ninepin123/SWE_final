from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.aas.models import User
from app.modules.aas.security import get_current_user, require_roles
from app.modules.ncs import service
from app.modules.ncs.schemas import (
    AnnouncementCreate,
    AnnouncementOut,
    AnnouncementUpdate,
    DeadlineReminderResultOut,
    EmailLogOut,
    IssueReplyCreate,
    IssueReplyOut,
    IssueReportCreate,
    IssueReportOut,
    IssueReportUpdate,
    MarkAllReadOut,
    MarkReadOut,
    MessageCreate,
    MessageOut,
    NotificationCreate,
    NotificationOut,
    SystemAlertOut,
    SystemAlertUpdate,
    UnreadCountOut,
)

router = APIRouter(prefix="/api/ncs", tags=["NCS 通知與溝通"])


@router.post("/notifications", response_model=NotificationOut, status_code=status.HTTP_201_CREATED)
def create_notification(
    body: NotificationCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("ADMIN")),
):
    return service.create_notification(
        db,
        user_id=body.user_id,
        title=body.title,
        body=body.body,
        category=body.category,
        related_type=body.related_type,
        related_id=body.related_id,
    )


@router.get("/notifications", response_model=list[NotificationOut])
def my_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    return service.list_user_notifications(
        db,
        user_id=current.user_id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )


@router.get("/notifications/unread-count", response_model=UnreadCountOut)
@router.get("/notifications/unread_count", response_model=UnreadCountOut, include_in_schema=False)
def unread_count(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return {"unread_count": service.get_unread_count(db, current.user_id)}


@router.patch("/notifications/read-all", response_model=MarkAllReadOut)
def mark_all_read(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return {"updated_count": service.mark_all_notifications_read(db, current.user_id)}


@router.patch("/notifications/{notification_id}/read", response_model=MarkReadOut)
@router.post("/notifications/{notification_id}/read", response_model=MarkReadOut, include_in_schema=False)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    notification = service.mark_notification_read(db, notification_id, current.user_id)
    return {
        "notification_id": notification.notification_id,
        "is_read": notification.is_read,
        "read_at": notification.read_at,
    }


@router.get("/announcements", response_model=list[AnnouncementOut])
def my_announcements(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    return service.list_announcements(db, current)


@router.get("/announcements/admin", response_model=list[AnnouncementOut])
def admin_announcements(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("ADMIN")),
):
    return service.list_all_announcements(db)


@router.post("/announcements", response_model=AnnouncementOut, status_code=status.HTTP_201_CREATED)
def create_announcement(
    body: AnnouncementCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_roles("ADMIN")),
):
    return service.create_announcement(db, body, current)


@router.put("/announcements/{announcement_id}", response_model=AnnouncementOut)
def update_announcement(
    announcement_id: int,
    body: AnnouncementUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("ADMIN")),
):
    return service.update_announcement(db, announcement_id, body)


@router.delete("/announcements/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("ADMIN")),
):
    service.delete_announcement(db, announcement_id)
    return None


@router.post("/deadline-reminders/run", response_model=DeadlineReminderResultOut)
def run_deadline_reminders(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("ADMIN")),
):
    return service.run_deadline_reminders(db)


@router.get("/applications/{application_id}/messages", response_model=list[MessageOut])
def list_messages(
    application_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    return service.list_application_messages(db, application_id, current)


@router.post("/applications/{application_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def create_message(
    application_id: int,
    body: MessageCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    return service.create_application_message(db, application_id, body, current)


@router.post("/issues", response_model=IssueReportOut, status_code=status.HTTP_201_CREATED)
def create_issue(
    body: IssueReportCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    return service.create_issue_report(db, body, current)


@router.get("/issues/me", response_model=list[IssueReportOut])
def my_issues(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    return service.list_my_issues(db, current)


@router.get("/issues", response_model=list[IssueReportOut])
def all_issues(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("ADMIN")),
):
    return service.list_all_issues(db)


@router.patch("/issues/{issue_id}", response_model=IssueReportOut)
def update_issue(
    issue_id: int,
    body: IssueReportUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("ADMIN")),
):
    return service.update_issue_report(db, issue_id, body)


@router.post("/issues/{issue_id}/replies", response_model=IssueReplyOut, status_code=status.HTTP_201_CREATED)
def create_issue_reply(
    issue_id: int,
    body: IssueReplyCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    return service.create_issue_reply(db, issue_id, body, current)


@router.get("/issues/{issue_id}/replies", response_model=list[IssueReplyOut])
def list_issue_replies(
    issue_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    return service.list_issue_replies(db, issue_id, current)


@router.get("/system-alerts", response_model=list[SystemAlertOut])
def list_system_alerts(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("ADMIN")),
):
    return service.list_system_alerts(db)


@router.patch("/system-alerts/{alert_id}", response_model=SystemAlertOut)
def update_system_alert(
    alert_id: int,
    body: SystemAlertUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("ADMIN")),
):
    return service.update_system_alert(db, alert_id, body)


@router.get("/email-logs", response_model=list[EmailLogOut])
def list_email_logs(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("ADMIN")),
):
    return service.list_email_logs(db)
