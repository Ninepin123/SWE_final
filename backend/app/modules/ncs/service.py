from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.email import send_email
from app.modules.aas.models import User
from app.modules.ncs.models import (
    Announcement,
    ApplicationMessage,
    EmailLog,
    IssueReply,
    IssueReport,
    Notification,
    SystemAlert,
)
from app.modules.ncs.schemas import (
    AnnouncementCreate,
    AnnouncementUpdate,
    IssueReportCreate,
    IssueReportUpdate,
    IssueReplyCreate,
    MessageCreate,
    SystemAlertCreate,
    SystemAlertUpdate,
)

def create_notification(
    db: Session,
    user_id: int,
    title: str,
    body: str | None = None,
    category: str | None = None,
    related_type: str | None = None,
    related_id: int | None = None,
    commit: bool = True,
) -> Notification:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="找不到使用者")

    payload: dict = {
        "user_id": user_id,
        "title": title,
        "body": body,
        "is_read": False,
    }
    if hasattr(Notification, "category"):
        payload["category"] = category
    if hasattr(Notification, "related_type"):
        payload["related_type"] = related_type
    if hasattr(Notification, "related_id"):
        payload["related_id"] = related_id

    n = Notification(**payload)
    db.add(n)
    if commit:
        db.commit()
        db.refresh(n)

    # 站內通知建立後，best-effort 寄一封 email 給使用者。
    # EMAIL_ENABLED=false（預設）時 send_email 直接回傳 DISABLED，零開銷。
    _send_notification_email(db, user, title, body, commit=commit)

    return n


def _send_notification_email(
    db: Session,
    user: User,
    subject: str,
    body: str | None,
    commit: bool,
) -> None:
    """寄送通知 email 並寫入 email_logs（best-effort，不影響站內通知）。

    寄信本身永遠不會 raise；這裡再包一層 try 確保連寫 log 失敗也不會
    讓 create_notification 崩潰。commit=False 時不自行 commit，交給外層
    批次流程一起送出，避免提前 commit 其他 pending 的通知。
    """
    if not settings.email_enabled:
        return

    to_email = getattr(user, "email", None)
    try:
        status_value, error = send_email(to_email or "", subject, body)
        log = EmailLog(
            user_id=user.user_id,
            to_email=to_email,
            subject=subject,
            body=body,
            status=status_value,
            error_message=error,
        )
        db.add(log)
        if commit:
            db.commit()
    except Exception:  # noqa: BLE001 - email log 失敗也不能拖垮通知
        db.rollback() if commit else None


def notification_exists(db: Session, user_id: int, title: str, body: str | None = None) -> bool:
    stmt = select(Notification.notification_id).where(
        Notification.user_id == user_id,
        Notification.title == title,
        Notification.body == body,
    )
    return db.scalar(stmt) is not None


def create_notification_if_absent(
    db: Session,
    user_id: int,
    title: str,
    body: str | None = None,
    commit: bool = True,
) -> Notification | None:
    if notification_exists(db, user_id, title, body):
        return None
    return create_notification(db, user_id=user_id, title=title, body=body, commit=commit)


def list_user_notifications(
    db: Session,
    user_id: int,
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[Notification]:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.is_read == False)  # noqa: E712
    stmt = stmt.order_by(Notification.created_at.desc(), Notification.notification_id.desc())
    stmt = stmt.offset(max(offset, 0)).limit(max(limit, 1))
    return list(db.scalars(stmt))


def get_unread_count(db: Session, user_id: int) -> int:
    return int(
        db.scalar(
            select(func.count(Notification.notification_id)).where(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
        )
        or 0
    )


def mark_notification_read(db: Session, notification_id: int, user_id: int) -> Notification:
    n = db.get(Notification, notification_id)
    if n is None:
        raise HTTPException(status_code=404, detail="找不到通知")
    if n.user_id != user_id:
        raise HTTPException(status_code=403, detail="權限不足")

    if not n.is_read:
        n.is_read = True
        if hasattr(n, "read_at"):
            n.read_at = datetime.now()
        db.commit()
        db.refresh(n)
    return n


def mark_all_notifications_read(db: Session, user_id: int) -> int:
    notifications = list(
        db.scalars(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
        )
    )
    if not notifications:
        return 0

    now = datetime.now()
    for n in notifications:
        n.is_read = True
        if hasattr(n, "read_at"):
            n.read_at = now
    db.commit()
    return len(notifications)


def list_my(db: Session, user: User) -> list[Notification]:
    return list_user_notifications(db, user.user_id)


def unread_count(db: Session, user: User) -> int:
    return get_unread_count(db, user.user_id)


def mark_read(db: Session, user: User, notification_id: int) -> Notification:
    return mark_notification_read(db, notification_id, user.user_id)


VALID_TARGET_ROLES = {"STUDENT", "TEACHER", "SPONSOR", "REVIEWER", "ADMIN"}
VALID_ANNOUNCEMENT_STATUS = {"DRAFT", "PUBLISHED", "ARCHIVED"}


def _normalize_target_role(target_role: str | None) -> str | None:
    if target_role is None or target_role == "":
        return None

    role = target_role.upper()
    if role not in VALID_TARGET_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid target_role",
        )
    return role


def _normalize_announcement_status(value: str | None, default: str = "PUBLISHED") -> str:
    normalized = (value or default).upper()
    if normalized not in VALID_ANNOUNCEMENT_STATUS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid announcement status",
        )
    return normalized


def _get_announcement_or_404(db: Session, announcement_id: int) -> Announcement:
    announcement = (
        db.query(Announcement)
        .filter(Announcement.announcement_id == announcement_id)
        .first()
    )
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found",
        )
    return announcement


def list_announcements(db: Session, current_user: User | None = None) -> list[Announcement]:
    """
    一般使用者公告列表：
    - 只顯示 PUBLISHED
    - 未過期
    - 全域公告，或 target_role 符合目前使用者角色
    """
    now = datetime.utcnow()

    query = db.query(Announcement).filter(Announcement.status == "PUBLISHED")

    query = query.filter(
        or_(
            Announcement.expires_at.is_(None),
            Announcement.expires_at >= now,
        )
    )

    if current_user is not None:
        query = query.filter(
            or_(
                Announcement.is_global.is_(True),
                Announcement.target_role.is_(None),
                Announcement.target_role == current_user.role,
            )
        )

    return query.order_by(Announcement.created_at.desc()).all()


def list_all_announcements(db: Session) -> list[Announcement]:
    """
    Admin 管理公告用：可查看全部公告。
    """
    return (
        db.query(Announcement)
        .order_by(Announcement.created_at.desc())
        .all()
    )


def create_announcement(
    db: Session,
    body: AnnouncementCreate,
    current_user: User,
) -> Announcement:
    target_role = _normalize_target_role(body.target_role)
    announcement_status = _normalize_announcement_status(body.status)

    is_global = bool(body.is_global)
    if is_global:
        target_role = None

    now = datetime.utcnow()

    announcement = Announcement(
        title=body.title,
        body=body.body,
        created_by=current_user.user_id,
        target_role=target_role,
        is_global=is_global,
        status=announcement_status,
        published_at=now if announcement_status == "PUBLISHED" else None,
        expires_at=body.expires_at,
        created_at=now,
        updated_at=now,
    )

    db.add(announcement)
    db.commit()
    db.refresh(announcement)

    if body.notify_users and announcement.status == "PUBLISHED":
        create_announcement_notifications(db, announcement)

    return announcement


def update_announcement(
    db: Session,
    announcement_id: int,
    body: AnnouncementUpdate,
) -> Announcement:
    announcement = _get_announcement_or_404(db, announcement_id)

    if body.title is not None:
        announcement.title = body.title

    if body.body is not None:
        announcement.body = body.body

    if body.is_global is not None:
        announcement.is_global = body.is_global
        if body.is_global:
            announcement.target_role = None

    if body.target_role is not None:
        announcement.target_role = _normalize_target_role(body.target_role)
        announcement.is_global = False

    if body.status is not None:
        new_status = _normalize_announcement_status(body.status)
        announcement.status = new_status
        if new_status == "PUBLISHED" and announcement.published_at is None:
            announcement.published_at = datetime.utcnow()

    if body.expires_at is not None:
        announcement.expires_at = body.expires_at

    announcement.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(announcement)
    return announcement


def delete_announcement(db: Session, announcement_id: int) -> None:
    announcement = _get_announcement_or_404(db, announcement_id)
    db.delete(announcement)
    db.commit()


def create_announcement_notifications(
    db: Session,
    announcement: Announcement,
) -> int:
    """
    公告發布後建立站內通知。
    - 全域公告：通知所有 active users
    - 指定角色公告：通知該 role 的 active users
    """
    user_query = db.query(User)

    if hasattr(User, "status"):
        user_query = user_query.filter(User.status == "ACTIVE")

    if not announcement.is_global and announcement.target_role:
        user_query = user_query.filter(User.role == announcement.target_role)

    users = user_query.all()
    created_count = 0

    for user in users:
        notification = Notification(
            user_id=user.user_id,
            title=f"公告：{announcement.title}",
            body=announcement.body,
            is_read=False,
        )

        if hasattr(notification, "category"):
            notification.category = "ANNOUNCEMENT"
        if hasattr(notification, "related_type"):
            notification.related_type = "ANNOUNCEMENT"
        if hasattr(notification, "related_id"):
            notification.related_id = announcement.announcement_id

        db.add(notification)
        created_count += 1

    db.commit()
    return created_count

def notification_exists(
    db: Session,
    user_id: int,
    title: str,
    body: str | None = None,
    category: str | None = None,
    related_type: str | None = None,
    related_id: int | None = None,
) -> bool:
    stmt = select(Notification.notification_id).where(
        Notification.user_id == user_id,
        Notification.title == title,
        Notification.body == body,
    )

    if category is not None:
        stmt = stmt.where(Notification.category == category)
    if related_type is not None:
        stmt = stmt.where(Notification.related_type == related_type)
    if related_id is not None:
        stmt = stmt.where(Notification.related_id == related_id)

    return db.scalar(stmt) is not None


def create_notification_if_absent(
    db: Session,
    user_id: int,
    title: str,
    body: str | None = None,
    category: str | None = None,
    related_type: str | None = None,
    related_id: int | None = None,
    commit: bool = True,
) -> Notification | None:
    if notification_exists(
        db,
        user_id=user_id,
        title=title,
        body=body,
        category=category,
        related_type=related_type,
        related_id=related_id,
    ):
        return None

    return create_notification(
        db,
        user_id=user_id,
        title=title,
        body=body,
        category=category,
        related_type=related_type,
        related_id=related_id,
        commit=commit,
    )

def run_deadline_reminders(db: Session) -> dict:
    """
    手動執行 48 小時截止提醒。
    目前處理：
    1. TRS 推薦信 48 小時內截止且未提交，提醒教師。
    2. SAS 補件期限 48 小時內截止且未完成，提醒學生。

    注意：
    此函式使用既有資料表名稱：
    recommendations, applications, scholarships, supplement_requests。
    若你的 03_sas_tables.sql 欄位名稱不同，需對 SQL 欄位微調。
    """
    checked_count = 0
    created_count = 0
    skipped_duplicate_count = 0

    now = datetime.utcnow()
    until = now + timedelta(hours=48)

    rec_sql = text(
        """
        SELECT
            r.rec_id AS rec_id,
            r.teacher_id AS teacher_id,
            r.student_id AS student_id,
            a.application_id AS application_id,
            s.name AS scholarship_name,
            s.deadline AS deadline
        FROM recommendations r
        JOIN applications a ON a.application_id = r.application_id
        JOIN scholarships s ON s.scholarship_id = a.scholarship_id
        WHERE r.status <> 'SUBMITTED'
          AND s.deadline >= :now
          AND s.deadline <= :until
        """
    )

    for row in db.execute(rec_sql, {"now": now, "until": until}).mappings():
        checked_count += 1
        title = "推薦信即將截止"
        body = f"「{row['scholarship_name']}」推薦信將於 {row['deadline']} 截止，請盡快完成。"

        created = create_notification_if_absent(
            db,
            user_id=row["teacher_id"],
            title=title,
            body=body,
            category="DEADLINE_REMINDER",
            related_type="RECOMMENDATION",
            related_id=row["rec_id"],
            commit=False,
        )

        if created:
            created_count += 1
        else:
            skipped_duplicate_count += 1

    try:
        supplement_sql = text(
            """
            SELECT
                sr.supplement_id AS supplement_id,
                sr.application_id AS application_id,
                a.student_id AS student_id,
                s.name AS scholarship_name,
                sr.deadline AS deadline
            FROM supplement_requests sr
            JOIN applications a ON a.application_id = sr.application_id
            JOIN scholarships s ON s.scholarship_id = a.scholarship_id
            WHERE sr.status NOT IN ('SUBMITTED', 'COMPLETED', 'RESOLVED')
              AND sr.deadline >= :now
              AND sr.deadline <= :until
            """
        )

        for row in db.execute(supplement_sql, {"now": now, "until": until}).mappings():
            checked_count += 1
            title = "補件期限提醒"
            body = f"「{row['scholarship_name']}」補件期限將於 {row['deadline']} 截止，請盡快完成補件。"

            created = create_notification_if_absent(
                db,
                user_id=row["student_id"],
                title=title,
                body=body,
                category="DEADLINE_REMINDER",
                related_type="SUPPLEMENT",
                related_id=row["supplement_id"],
                commit=False,
            )

            if created:
                created_count += 1
            else:
                skipped_duplicate_count += 1

    except Exception:
        pass

    db.commit()

    return {
        "checked_count": checked_count,
        "created_count": created_count,
        "skipped_duplicate_count": skipped_duplicate_count,
    }

def _get_application_student_id(db: Session, application_id: int) -> int:
    row = db.execute(
        text("SELECT student_id FROM applications WHERE application_id = :application_id"),
        {"application_id": application_id},
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="找不到申請案")

    return int(row["student_id"])


def _ensure_message_access(db: Session, application_id: int, current_user: User) -> int:
    student_id = _get_application_student_id(db, application_id)

    if current_user.user_id == student_id:
        return student_id

    if current_user.role in {"REVIEWER", "SPONSOR", "ADMIN"}:
        return student_id

    raise HTTPException(status_code=403, detail="沒有案件留言權限")


def list_application_messages(
    db: Session,
    application_id: int,
    current_user: User,
) -> list[ApplicationMessage]:
    _ensure_message_access(db, application_id, current_user)

    return list(
        db.scalars(
            select(ApplicationMessage)
            .where(ApplicationMessage.application_id == application_id)
            .order_by(ApplicationMessage.created_at.asc(), ApplicationMessage.message_id.asc())
        )
    )


def create_application_message(
    db: Session,
    application_id: int,
    body: MessageCreate,
    current_user: User,
) -> ApplicationMessage:
    student_id = _ensure_message_access(db, application_id, current_user)

    message = ApplicationMessage(
        application_id=application_id,
        sender_id=current_user.user_id,
        body=body.body,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    if current_user.user_id == student_id:
        reviewers = db.query(User).filter(User.role == "REVIEWER").all()
        for reviewer in reviewers:
            create_notification_if_absent(
                db,
                user_id=reviewer.user_id,
                title="案件有新留言",
                body=f"申請案 #{application_id} 有學生新增留言。",
                category="MESSAGE",
                related_type="APPLICATION",
                related_id=application_id,
                commit=False,
            )
    else:
        create_notification_if_absent(
            db,
            user_id=student_id,
            title="案件有新留言",
            body=f"申請案 #{application_id} 有新的回覆。",
            category="MESSAGE",
            related_type="APPLICATION",
            related_id=application_id,
            commit=False,
        )

    db.commit()
    return message

VALID_ISSUE_STATUS = {"OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"}
VALID_ATTACHMENT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf", ".txt"}


def _validate_attachment_name(name: str | None) -> None:
    if not name:
        return

    lowered = name.lower()
    if not any(lowered.endswith(ext) for ext in VALID_ATTACHMENT_EXTENSIONS):
        raise HTTPException(status_code=400, detail="附件格式不允許")


def create_issue_report(
    db: Session,
    body: IssueReportCreate,
    current_user: User,
) -> IssueReport:
    _validate_attachment_name(body.attachment_name)

    issue = IssueReport(
        reporter_id=current_user.user_id,
        issue_type=body.issue_type,
        title=body.title,
        description=body.description,
        attachment_name=body.attachment_name,
        attachment_url=body.attachment_url,
        status="OPEN",
        created_at=datetime.utcnow(),
    )

    db.add(issue)
    db.commit()
    db.refresh(issue)

    admins = db.query(User).filter(User.role == "ADMIN").all()
    for admin in admins:
        create_notification_if_absent(
            db,
            user_id=admin.user_id,
            title="新的問題回報",
            body=f"{current_user.name if hasattr(current_user, 'name') else '使用者'} 回報問題：{issue.title}",
            category="ISSUE",
            related_type="ISSUE",
            related_id=issue.issue_id,
            commit=False,
        )

    db.commit()
    return issue


def list_my_issues(db: Session, current_user: User) -> list[IssueReport]:
    return list(
        db.scalars(
            select(IssueReport)
            .where(IssueReport.reporter_id == current_user.user_id)
            .order_by(IssueReport.created_at.desc(), IssueReport.issue_id.desc())
        )
    )


def list_all_issues(db: Session) -> list[IssueReport]:
    return list(
        db.scalars(
            select(IssueReport)
            .order_by(IssueReport.created_at.desc(), IssueReport.issue_id.desc())
        )
    )


def update_issue_report(
    db: Session,
    issue_id: int,
    body: IssueReportUpdate,
) -> IssueReport:
    issue = db.get(IssueReport, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="找不到問題回報")

    if body.status is not None:
        status_value = body.status.upper()
        if status_value not in VALID_ISSUE_STATUS:
            raise HTTPException(status_code=400, detail="問題狀態不正確")
        issue.status = status_value

    issue.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(issue)
    return issue


def create_issue_reply(
    db: Session,
    issue_id: int,
    body: IssueReplyCreate,
    current_user: User,
) -> IssueReply:
    issue = db.get(IssueReport, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="找不到問題回報")

    if current_user.role != "ADMIN" and issue.reporter_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="沒有權限回覆此問題回報")

    reply_body = body.body.strip()
    if not reply_body:
        raise HTTPException(status_code=400, detail="請輸入回覆內容")

    reply = IssueReply(
        issue_id=issue_id,
        replier_id=current_user.user_id,
        body=reply_body,
    )

    issue.updated_at = datetime.utcnow()
    db.add(reply)
    db.commit()
    db.refresh(reply)

    if current_user.user_id == issue.reporter_id:
        admins = (
            db.query(User)
            .filter(User.role == "ADMIN", User.user_id != current_user.user_id)
            .all()
        )
        reporter_name = current_user.name if hasattr(current_user, "name") else "使用者"
        for admin in admins:
            create_notification(
                db,
                user_id=admin.user_id,
                title="問題回報有新留言",
                body=f"{reporter_name} 在問題「{issue.title}」新增回覆。",
                category="ISSUE",
                related_type="ISSUE",
                related_id=issue.issue_id,
                commit=False,
            )
        db.commit()
    elif issue.reporter_id != current_user.user_id:
        create_notification(
            db,
            user_id=issue.reporter_id,
            title="問題回報有新回覆",
            body=f"你的問題「{issue.title}」已有管理員回覆。",
            category="ISSUE",
            related_type="ISSUE",
            related_id=issue.issue_id,
            commit=True,
        )

    return reply


def list_issue_replies(db: Session, issue_id: int, current_user: User) -> list[IssueReply]:
    issue = db.get(IssueReport, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="找不到問題回報")

    if current_user.role != "ADMIN" and issue.reporter_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="沒有權限查看此問題回報")

    return list(
        db.scalars(
            select(IssueReply)
            .where(IssueReply.issue_id == issue_id)
            .order_by(IssueReply.created_at.asc(), IssueReply.reply_id.asc())
        )
    )

VALID_ALERT_SEVERITY = {"INFO", "WARNING", "ERROR", "CRITICAL"}
VALID_ALERT_STATUS = {"OPEN", "RESOLVED"}


def create_system_alert(
    db: Session,
    body: SystemAlertCreate,
) -> SystemAlert:
    severity = body.severity.upper()
    if severity not in VALID_ALERT_SEVERITY:
        raise HTTPException(status_code=400, detail="系統警示等級不正確")

    alert = SystemAlert(
        severity=severity,
        title=body.title,
        body=body.body,
        source=body.source,
        status="OPEN",
        created_at=datetime.utcnow(),
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    admins = db.query(User).filter(User.role == "ADMIN").all()
    for admin in admins:
        create_notification_if_absent(
            db,
            user_id=admin.user_id,
            title=f"系統警示：{alert.title}",
            body=alert.body,
            category="SYSTEM_ALERT",
            related_type="SYSTEM_ALERT",
            related_id=alert.alert_id,
            commit=False,
        )

    db.commit()
    return alert


def list_system_alerts(db: Session) -> list[SystemAlert]:
    return list(
        db.scalars(
            select(SystemAlert)
            .order_by(SystemAlert.created_at.desc(), SystemAlert.alert_id.desc())
        )
    )


def update_system_alert(
    db: Session,
    alert_id: int,
    body: SystemAlertUpdate,
) -> SystemAlert:
    alert = db.get(SystemAlert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="找不到系統警示")

    if body.status is not None:
        next_status = body.status.upper()
        if next_status not in VALID_ALERT_STATUS:
            raise HTTPException(status_code=400, detail="系統警示狀態不正確")

        alert.status = next_status
        if next_status == "RESOLVED":
            alert.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(alert)
    return alert

def create_email_log(
    db: Session,
    subject: str,
    body: str | None = None,
    user_id: int | None = None,
    to_email: str | None = None,
    status_value: str = "DISABLED",
    error_message: str | None = None,
) -> EmailLog:
    log = EmailLog(
        user_id=user_id,
        to_email=to_email,
        subject=subject,
        body=body,
        status=status_value,
        error_message=error_message,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def list_email_logs(db: Session) -> list[EmailLog]:
    return list(
        db.scalars(
            select(EmailLog)
            .order_by(EmailLog.created_at.desc(), EmailLog.email_log_id.desc())
        )
    )
