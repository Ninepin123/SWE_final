"""End-to-end smoke test against the running dev server.

Run with: python tests/e2e_smoke.py

Simulates a real user walking through every subsystem's primary flows.
Not part of the pytest suite; talks to http://localhost:8000 like a browser.
"""
from __future__ import annotations

import datetime as dt
import os
import sys
import time
import uuid

import requests

BASE = os.environ.get("E2E_BASE", "http://localhost:8000")
ADMIN_ACCOUNT = os.environ.get("E2E_ADMIN_ACCOUNT", "admin")
ADMIN_PASSWORD = os.environ.get("E2E_ADMIN_PASSWORD", "ChangeMe!12345")

passed: list[str] = []
failed: list[tuple[str, str]] = []


def log_ok(label: str) -> None:
    passed.append(label)
    print(f"  [OK] {label}")


def log_fail(label: str, err: str) -> None:
    failed.append((label, err))
    print(f"  [FAIL] {label}: {err}")


def expect(cond: bool, label: str, detail: str = "") -> None:
    if cond:
        log_ok(label)
    else:
        log_fail(label, detail or "condition false")


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


class Session:
    def __init__(self) -> None:
        self.s = requests.Session()
        self.token: str | None = None
        self.user: dict | None = None

    def headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def login(self, account: str, password: str) -> dict:
        r = self.s.post(f"{BASE}/api/aas/login",
                        json={"account": account, "password": password}, timeout=15)
        r.raise_for_status()
        body = r.json()
        self.token = body["access_token"]
        self.user = body["user"]
        return body

    def get(self, path, **kw):
        return self.s.get(f"{BASE}{path}", headers=self.headers(), timeout=30, **kw)

    def post(self, path, **kw):
        return self.s.post(f"{BASE}{path}", headers=self.headers(), timeout=30, **kw)

    def put(self, path, **kw):
        return self.s.put(f"{BASE}{path}", headers=self.headers(), timeout=30, **kw)

    def patch(self, path, **kw):
        return self.s.patch(f"{BASE}{path}", headers=self.headers(), timeout=30, **kw)

    def delete(self, path, **kw):
        return self.s.delete(f"{BASE}{path}", headers=self.headers(), timeout=30, **kw)


def uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def test_aas_me(admin: Session) -> None:
    print("\n=== AAS: me ===")
    r = admin.get("/api/aas/me")
    expect(r.status_code == 200, "GET /api/aas/me", f"{r.status_code} {r.text[:200]}")


def test_aas_account_crud(admin: Session) -> dict:
    print("\n=== AAS: account CRUD ===")
    admin.login(ADMIN_ACCOUNT, ADMIN_PASSWORD)  # AAS003: refresh admin session
    unit_resp = admin.post("/api/aas/units", json={"name": "E2E-" + uid("u"), "description": "e2e"})
    unit = unit_resp.json() if unit_resp.status_code in (200, 201) else None
    expect(unit_resp.status_code in (200, 201), "POST /api/aas/units", f"{unit_resp.status_code} {unit_resp.text[:200]}")

    dept_resp = admin.post("/api/aas/departments", json={"name": "E2E-" + uid("d"), "code": uid("C")[:8]})
    dept = dept_resp.json() if dept_resp.status_code in (200, 201) else None
    expect(dept_resp.status_code in (200, 201), "POST /api/aas/departments", f"{dept_resp.status_code} {dept_resp.text[:200]}")

    created: dict = {}
    specs = [
        ("student", "s" + uid("stu")[:10], "STUDENT", {"gpa": 3.8, "department": dept["name"] if dept else None}),
        ("teacher", "t" + uid("tea")[:10], "TEACHER", {}),
        ("sponsor", "u" + uid("spo")[:10], "SPONSOR", {"unit_id": unit["unit_id"] if unit else None}),
        ("reviewer", "r" + uid("rev")[:10], "REVIEWER", {"unit_id": unit["unit_id"] if unit else None}),
    ]
    for label, acct, role, extra in specs:
        body = {"account": acct, "password": "Test!2345", "name": f"E2E {label}",
                "role": role, "email": f"{acct}@e2e.test", **extra}
        r = admin.post("/api/aas/users", json=body)
        if r.status_code in (200, 201):
            created[label] = r.json()
            log_ok(f"POST /api/aas/users ({role})")
        else:
            log_fail(f"POST /api/aas/users ({role})", f"{r.status_code} {r.text[:300]}")

    expect(admin.get("/api/aas/users").status_code == 200, "GET /api/aas/users")
    stu = created.get("student")
    if stu:
        r = admin.put(f"/api/aas/users/{stu['user_id']}", json={"email": "updated@e2e.test"})
        expect(r.status_code == 200, "PUT /api/aas/users/{id}", f"{r.status_code} {r.text[:200]}")

    expect(admin.get("/api/aas/audit-logs").status_code == 200, "GET /api/aas/audit-logs")
    expect(admin.get("/api/aas/monitoring/metrics").status_code == 200, "GET /api/aas/monitoring/metrics")
    expect(admin.get("/api/aas/teachers").status_code == 200, "GET /api/aas/teachers")
    return {"created": created, "password": "Test!2345"}


def test_sms(sponsor: Session) -> dict:
    print("\n=== SMS: scholarship CRUD + options ===")
    expect(sponsor.get("/api/sms/options").status_code == 200, "GET /api/sms/options")
    r = sponsor.post("/api/sms/options", json={"name": "E2E-" + uid("cat")[:6], "type": "CATEGORY"})
    option = r.json() if r.status_code in (200, 201) else None
    # SMS010: 系統管理員或獎助單位人員皆可管理分類/標籤
    expect(r.status_code in (200, 201), "POST /api/sms/options (sponsor)", f"{r.status_code} {r.text[:200]}")

    now = now_utc()
    sc_id = None
    body = {
        "title": "E2E-" + uid("sc")[:6], "year": 2026, "amount": 10000,
        "description": "e2e", "contactName": "聯絡人",
        "contactEmail": "scholar@e2e.test", "contactPhone": "02-1234-5678",
        "startDate": (now - dt.timedelta(days=1)).isoformat(),
        "deadline": (now + dt.timedelta(days=30)).isoformat(),
        "quota": 5, "category": option["name"] if option else "MERIT",
        "criteria": {"minGpa": 3.0}, "requiredDocs": ["成績單", "自傳"],
    }
    r = sponsor.post("/api/sms/scholarships", json=body)
    sc = r.json() if r.status_code in (200, 201) else None
    expect(r.status_code in (200, 201), "POST /api/sms/scholarships", f"{r.status_code} {r.text[:300]}")
    if sc:
        sc_id = sc.get("id") or sc.get("scholarship_id")
        expect(sponsor.get("/api/sms/scholarships").status_code == 200, "GET /api/sms/scholarships")
        expect(sponsor.get(f"/api/sms/scholarships/{sc_id}").status_code == 200, "GET /api/sms/scholarships/{id}")
        r = sponsor.put(f"/api/sms/scholarships/{sc_id}", json={"description": "updated"})
        expect(r.status_code == 200, "PUT /api/sms/scholarships/{id}", f"{r.status_code} {r.text[:200]}")
    return {"scholarship": sc, "scholarship_id": sc_id}


def test_sas(student: Session, scholarship: dict, teacher_user: dict | None = None) -> dict:
    print("\n=== SAS: profile / available / apply / document / submit / track ===")
    expect(student.get("/api/sas/profile").status_code == 200, "GET /api/sas/profile")
    r = student.put("/api/sas/profile",
                    json={"contact_phone": "0911-000-000", "address": "e2e addr", "email": "student@e2e.test"})
    expect(r.status_code == 200, "PUT /api/sas/profile", f"{r.status_code} {r.text[:200]}")
    expect(student.get("/api/sas/scholarships/available").status_code == 200, "GET available scholarships")

    if not scholarship:
        log_fail("SAS apply flow", "no scholarship created")
        return {}
    sc_id = scholarship.get("id") or scholarship.get("scholarship_id")

    r = student.post("/api/sas/applications",
                     json={"scholarship_id": sc_id, "statement": "我想申請",
                           "contact_phone": "0911-000-000", "address": "e2e addr",
                           "household_status": "一般", "academic_note": "GPA 3.8"})
    if r.status_code in (200, 201):
        app = r.json()
        log_ok("POST /api/sas/applications")
    else:
        log_fail("POST /api/sas/applications", f"{r.status_code} {r.text[:300]}")
        return {}

    aid = app["application_id"]
    for doc_type, title in [("TRANSCRIPT", "成績單"), ("AUTOBIOGRAPHY", "自傳")]:
        r = student.post(f"/api/sas/applications/{aid}/documents",
                         json={"document_type": doc_type, "title": title, "content_text": f"E2E {title}"})
        expect(r.status_code in (200, 201), f"POST documents ({doc_type})", f"{r.status_code} {r.text[:200]}")

    expect(student.get(f"/api/sas/applications/{aid}/documents").status_code == 200, "GET documents")
    trs_res = test_trs_invite(student, teacher_user, app) if teacher_user else {}
    r = student.post(f"/api/sas/applications/{aid}/submit")
    if r.status_code == 200:
        app = r.json()
    expect(r.status_code == 200, "POST submit", f"{r.status_code} {r.text[:200]}")
    expect(student.get("/api/sas/applications/me").status_code == 200, "GET /api/sas/applications/me")
    expect(student.get(f"/api/sas/applications/{aid}/events").status_code == 200, "GET events")
    return {"application": app, **trs_res}


def test_trs_invite(student: Session, teacher_user: dict, application: dict) -> dict:
    print("\n=== TRS: student invites teacher ===")
    if not application or not teacher_user:
        log_fail("TRS invite", "missing application or teacher")
        return {}
    r = student.post("/api/trs/recommendations",
                     json={"application_id": application["application_id"],
                           "teacher_id": teacher_user["user_id"]})
    if r.status_code in (200, 201):
        rec = r.json()
        log_ok("POST /api/trs/recommendations")
        rid = rec.get("rec_id") or rec.get("recommendation_id") or rec.get("id")
        if rid is None:
            print("    (debug) TRS invite response keys:", list(rec.keys()), "body:", str(rec)[:300])
        return {"recommendation_id": rid}
    log_fail("POST /api/trs/recommendations", f"{r.status_code} {r.text[:300]}")
    return {}


def test_trs_teacher(teacher: Session, student: Session, rec_id) -> None:
    print("\n=== TRS: teacher dashboard / list / draft / submit / profile ===")
    expect(teacher.get("/api/trs/recommendations/teacher/dashboard").status_code == 200, "GET teacher dashboard")
    expect(teacher.get("/api/trs/recommendations/teacher").status_code == 200, "GET teacher list")
    expect(student.get("/api/trs/recommendations/student").status_code == 200,
           "GET recommendations/student (student status only)")
    if rec_id is None:
        log_fail("TRS teacher flow", "no recommendation")
        return
    r = teacher.get(f"/api/trs/recommendations/{rec_id}/student-profile")
    expect(r.status_code == 200, "GET recommendation student-profile", f"{r.status_code} {r.text[:200]}")
    r = teacher.put(f"/api/trs/recommendations/{rec_id}",
                    json={"content": "草稿內容。", "submit": False})
    expect(r.status_code == 200, "PUT recommendation (DRAFT)", f"{r.status_code} {r.text[:200]}")
    r = teacher.put(f"/api/trs/recommendations/{rec_id}",
                    json={"content": "完整推薦信。", "submit": True})
    expect(r.status_code == 200, "PUT recommendation (SUBMITTED)", f"{r.status_code} {r.text[:200]}")
    r = teacher.put(f"/api/trs/recommendations/{rec_id}",
                    json={"content": "不應覆寫", "submit": False})
    expect(r.status_code == 409, "submitted recommendation locked", f"{r.status_code} {r.text[:200]}")


def test_ras_queue(reviewer: Session) -> None:
    print("\n=== RAS: query queue ===")
    expect(reviewer.get("/api/ras/applications").status_code == 200, "GET /api/ras/applications")


def test_ras_decision(reviewer: Session, student: Session, application: dict) -> None:
    print("\n=== RAS: view / decision / supplement / award / stats ===")
    if not application:
        log_fail("RAS decision flow", "no application")
        return
    aid = application["application_id"]
    expect(reviewer.post(f"/api/ras/applications/{aid}/view").status_code == 200, "POST view (track)")

    end = (now_utc() + dt.timedelta(days=7)).isoformat()
    r = reviewer.post(f"/api/ras/applications/{aid}/decision",
                      json={"result": "NEED_SUPPLEMENT", "comment": "請補財力證明", "supplement_deadline": end})
    expect(r.status_code == 200, "POST decision NEED_SUPPLEMENT", f"{r.status_code} {r.text[:200]}")

    r = student.get(f"/api/sas/applications/{aid}/supplement-requests")
    expect(r.status_code == 200, "GET supplement-requests (student)", f"{r.status_code} {r.text[:200]}")
    srs = r.json() if r.status_code == 200 else []
    if srs:
        sid = srs[0]["supplement_id"]
        r = student.post(f"/api/sas/applications/{aid}/supplement-requests/{sid}/submit",
                         json={"response_text": "已補上財力證明。"})
        expect(r.status_code == 200, "POST supplement submit", f"{r.status_code} {r.text[:200]}")
    else:
        log_fail("POST supplement submit", "no supplement request created")

    r = reviewer.post(f"/api/ras/applications/{aid}/decision",
                      json={"result": "APPROVED", "comment": "成績優良"})
    expect(r.status_code == 200, "POST decision APPROVED", f"{r.status_code} {r.text[:200]}")

    expect(reviewer.get("/api/ras/statistics").status_code == 200, "GET /api/ras/statistics")
    expect(reviewer.get("/api/ras/award-list").status_code == 200, "GET /api/ras/award-list")
    expect(reviewer.get("/api/ras/statistics/export").status_code == 200, "GET /api/ras/statistics/export (csv)")
    expect(reviewer.get("/api/ras/statistics/export/pdf").status_code == 200, "GET /api/ras/statistics/export/pdf")


def test_ncs(student: Session, admin: Session) -> None:
    print("\n=== NCS: notifications / announcements / issues / alerts ===")
    admin.login(ADMIN_ACCOUNT, ADMIN_PASSWORD)  # AAS003 single-session rotates prior tokens
    expect(student.get("/api/ncs/notifications").status_code == 200, "GET notifications")
    expect(student.get("/api/ncs/notifications/unread-count").status_code == 200, "GET unread-count")
    expect(student.patch("/api/ncs/notifications/read-all").status_code in (200, 204), "PATCH read-all")

    r = admin.post("/api/ncs/announcements",
                   json={"title": "E2E-" + uid("a")[:6], "body": "e2e", "is_global": True})
    expect(r.status_code in (200, 201), "POST announcements", f"{r.status_code} {r.text[:200]}")
    expect(student.get("/api/ncs/announcements").status_code == 200, "GET announcements")
    expect(admin.get("/api/ncs/announcements/admin").status_code == 200, "GET announcements/admin")

    r = student.post("/api/ncs/issues",
                     json={"title": "E2E問題", "description": "有問題", "issue_type": "BUG"})
    issue = r.json() if r.status_code in (200, 201) else None
    expect(r.status_code in (200, 201), "POST issues", f"{r.status_code} {r.text[:200]}")
    expect(student.get("/api/ncs/issues/me").status_code == 200, "GET issues/me")
    expect(admin.get("/api/ncs/issues").status_code == 200, "GET issues (admin)")
    if issue:
        iid = issue["issue_id"]
        r = admin.post(f"/api/ncs/issues/{iid}/replies", json={"body": "已收到"})
        expect(r.status_code in (200, 201), "POST issue replies", f"{r.status_code} {r.text[:200]}")
        r = admin.patch(f"/api/ncs/issues/{iid}", json={"status": "IN_PROGRESS"})
        expect(r.status_code in (200, 400), "PATCH issue status", f"{r.status_code} {r.text[:200]}")

    expect(admin.get("/api/ncs/system-alerts").status_code == 200, "GET system-alerts")
    expect(admin.get("/api/ncs/email-logs").status_code == 200, "GET email-logs")
    expect(admin.post("/api/ncs/deadline-reminders/run").status_code in (200, 204),
           "POST deadline-reminders/run")


def main() -> int:
    start = time.time()
    print(f"== E2E smoke test against {BASE} ==")
    admin = Session()
    try:
        admin.login(ADMIN_ACCOUNT, ADMIN_PASSWORD)
        log_ok("admin login")
    except Exception as e:
        log_fail("admin login", repr(e))
        return 1

    try:
        test_aas_me(admin)
        cr = test_aas_account_crud(admin)
    except Exception as e:
        log_fail("AAS scenario", repr(e))
        return 1

    created = cr["created"]
    pwd = cr["password"]
    teacher_user = created.get("teacher", {})

    sessions = {"student": Session(), "teacher": Session(),
                "sponsor": Session(), "reviewer": Session()}
    for label, sess in sessions.items():
        acct = created.get(label, {}).get("account")
        if not acct:
            log_fail(f"{label} login", "account not created")
            continue
        try:
            sess.login(acct, pwd)
            log_ok(f"{label} login")
        except Exception as e:
            log_fail(f"{label} login", repr(e))

    student = sessions["student"]
    teacher = sessions["teacher"]
    sponsor = sessions["sponsor"]
    reviewer = sessions["reviewer"]

    try:
        sms_res = test_sms(sponsor)
    except Exception as e:
        log_fail("SMS scenario", repr(e))
        sms_res = {}

    try:
        sas_res = test_sas(student, sms_res.get("scholarship"), teacher_user)
    except Exception as e:
        log_fail("SAS scenario", repr(e))
        sas_res = {}

    try:
        test_ncs(student, admin)
    except Exception as e:
        log_fail("NCS scenario", repr(e))

    try:
        test_ras_queue(reviewer)
    except Exception as e:
        log_fail("RAS queue scenario", repr(e))

    app = sas_res.get("application")
    trs_res = {"recommendation_id": sas_res.get("recommendation_id")}
    if trs_res["recommendation_id"] is None:
        log_fail("TRS invite scenario", "no recommendation created during draft flow")

    try:
        test_trs_teacher(teacher, student, trs_res.get("recommendation_id"))
    except Exception as e:
        log_fail("TRS teacher scenario", repr(e))

    try:
        test_ras_decision(reviewer, student, app)
    except Exception as e:
        log_fail("RAS decision scenario", repr(e))

    sc_id = sms_res.get("scholarship_id")
    if sc_id:
        r = sponsor.delete(f"/api/sms/scholarships/{sc_id}")
        expect(r.status_code in (200, 204, 409), "DELETE scholarship",
               f"{r.status_code} {r.text[:200]}")

    elapsed = time.time() - start
    print("\n" + "=" * 60)
    print(f"Passed: {len(passed)}   Failed: {len(failed)}   ({elapsed:.1f}s)")
    if failed:
        print("\nFailures:")
        for label, err in failed:
            print(f"  - {label}: {err}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
