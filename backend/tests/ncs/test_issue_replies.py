import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.modules.aas.models import Unit, User
from app.modules.aas.security import create_access_token
from app.modules.ncs.models import IssueReply, IssueReport, Notification
from app.modules.ncs.router import router


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(
        engine,
        tables=[
            Unit.__table__,
            User.__table__,
            Notification.__table__,
            IssueReport.__table__,
            IssueReply.__table__,
        ],
    )
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session):
    app = FastAPI()
    app.include_router(router)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def create_user(db_session, account, *, role="STUDENT"):
    user = User(
        account=account,
        password="test-password",
        name=account,
        role=role,
        status="ACTIVE",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_issue(db_session, reporter, *, title="無法上傳附件"):
    issue = IssueReport(
        reporter_id=reporter.user_id,
        issue_type="BUG",
        title=title,
        description="附件送出後沒有反應",
        status="OPEN",
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)
    return issue


def auth(user):
    token = create_access_token(user.user_id, user.role)
    return {"Authorization": f"Bearer {token}"}


def test_reporter_can_continue_discussion_and_admin_is_notified(client, db_session):
    reporter = create_user(db_session, "student-issue")
    admin = create_user(db_session, "admin-issue", role="ADMIN")
    issue = create_issue(db_session, reporter)

    response = client.post(
        f"/api/ncs/issues/{issue.issue_id}/replies",
        json={"body": "我補充一下，PDF 也會失敗。"},
        headers=auth(reporter),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["issue_id"] == issue.issue_id
    assert payload["replier_id"] == reporter.user_id
    assert payload["body"] == "我補充一下，PDF 也會失敗。"

    notifications = list(
        db_session.scalars(select(Notification).where(Notification.user_id == admin.user_id))
    )
    assert len(notifications) == 1
    assert notifications[0].title == "問題回報有新留言"
    assert notifications[0].related_id == issue.issue_id


def test_admin_reply_notifies_reporter_every_time(client, db_session):
    reporter = create_user(db_session, "student-notify")
    admin = create_user(db_session, "admin-notify", role="ADMIN")
    issue = create_issue(db_session, reporter)

    first = client.post(
        f"/api/ncs/issues/{issue.issue_id}/replies",
        json={"body": "我們正在確認附件限制。"},
        headers=auth(admin),
    )
    second = client.post(
        f"/api/ncs/issues/{issue.issue_id}/replies",
        json={"body": "已定位到檔案類型判斷，稍後更新。"},
        headers=auth(admin),
    )

    assert first.status_code == 201
    assert second.status_code == 201

    notifications = list(
        db_session.scalars(select(Notification).where(Notification.user_id == reporter.user_id))
    )
    assert len(notifications) == 2
    assert all(note.title == "問題回報有新回覆" for note in notifications)


def test_other_user_cannot_read_or_reply_to_issue(client, db_session):
    reporter = create_user(db_session, "student-owner")
    other = create_user(db_session, "student-other")
    issue = create_issue(db_session, reporter)

    read_response = client.get(
        f"/api/ncs/issues/{issue.issue_id}/replies",
        headers=auth(other),
    )
    reply_response = client.post(
        f"/api/ncs/issues/{issue.issue_id}/replies",
        json={"body": "我不應該可以留言"},
        headers=auth(other),
    )

    assert read_response.status_code == 403
    assert reply_response.status_code == 403
    assert db_session.scalar(select(IssueReply)) is None
