"""Remove legacy development/mock data from the configured NUKSAMS database.

This script targets data that was previously inserted by development seed
paths, quick-login helpers, or frontend mock flows. It intentionally does not
create replacement records.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import pymysql
except ImportError:
    sys.exit("[X] 找不到 pymysql，請先安裝 backend/requirements.txt。")


ROOT = Path(__file__).resolve().parent.parent

MOCK_ACCOUNTS = (
    "sponsor",
    "reviewer",
    "reviewer2",
    "teacher",
    "teacher2",
    "A1125529",
    "A1125599",
)
MOCK_UNIT_NAMES = (
    "學生事務處生活輔導組",
    "教育部",
    "TRS 開發測試單位",
)
MOCK_SCHOLARSHIP_NAMES = (
    "清寒優秀學生獎學金",
    "教育部學產基金助學金",
    "TRS 逾期測試獎學金",
)
MOCK_OPTION_NAMES = (
    "校內獎學金",
    "政府獎學金",
    "企業贊助",
    "清寒獎助",
    "成績優良",
    "其他",
    "急難救助",
    "限理工學院",
)
MOCK_APPLICATION_STATEMENTS = (
    "開發種子資料建立的示範申請案。",
    "快速登入測試用申請案。",
)


def parse_database_url() -> dict[str, str | int]:
    env_file = ROOT / "backend" / ".env"
    if not env_file.exists():
        env_file = ROOT / "backend" / ".env.example"

    url = None
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("DATABASE_URL="):
            url = line.split("=", 1)[1].strip()
            break

    if not url:
        sys.exit("[X] 找不到 DATABASE_URL")

    match = re.match(
        r"mysql\+pymysql://([^:]+):([^@]*)@([^:/]+)(?::(\d+))?/([^?]+)",
        url,
    )
    if not match:
        sys.exit(f"[X] 無法解析 DATABASE_URL：{url}")

    user, password, host, port, db = match.groups()
    return {
        "user": user,
        "password": password,
        "host": host,
        "port": int(port or 3306),
        "database": db,
    }


def placeholders(values) -> str:
    return ", ".join(["%s"] * len(values))


def table_exists(cursor, table: str) -> bool:
    cursor.execute("SHOW TABLES LIKE %s", (table,))
    return cursor.fetchone() is not None


def execute_delete(cursor, summary: dict[str, int], table: str, sql: str, params=()) -> None:
    if not table_exists(cursor, table):
        return
    if params:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)
    summary[table] = summary.get(table, 0) + cursor.rowcount


def create_temp_tables(cursor) -> None:
    cursor.execute("CREATE TEMPORARY TABLE purge_mock_users (user_id BIGINT PRIMARY KEY)")
    cursor.execute(
        f"""
        INSERT IGNORE INTO purge_mock_users
        SELECT user_id
        FROM users
        WHERE account IN ({placeholders(MOCK_ACCOUNTS)})
           OR account LIKE 'DEVTRS%%'
           OR email LIKE 'devtrs%%@nuk.edu.tw'
        """,
        MOCK_ACCOUNTS,
    )
    cursor.execute("CREATE TEMPORARY TABLE purge_mock_teacher_users AS SELECT * FROM purge_mock_users")

    cursor.execute("CREATE TEMPORARY TABLE purge_mock_units (unit_id BIGINT PRIMARY KEY)")
    cursor.execute(
        f"""
        INSERT IGNORE INTO purge_mock_units
        SELECT unit_id
        FROM units
        WHERE name IN ({placeholders(MOCK_UNIT_NAMES)})
           OR contact_email IN ('trs-dev@nuk.edu.tw', 'moe@example.gov.tw', 'osa@nuk.edu.tw')
        """,
        MOCK_UNIT_NAMES,
    )

    cursor.execute("CREATE TEMPORARY TABLE purge_mock_scholarships (scholarship_id BIGINT PRIMARY KEY)")
    cursor.execute(
        f"""
        INSERT IGNORE INTO purge_mock_scholarships
        SELECT scholarship_id
        FROM scholarships
        WHERE name IN ({placeholders(MOCK_SCHOLARSHIP_NAMES)})
           OR name LIKE 'TRS 快速測試獎學金 %%'
           OR description IN ('開發測試：逾期未提交推薦信案件。', '開發模式快速登入測試資料。')
           OR created_by IN (SELECT user_id FROM purge_mock_users)
        """,
        MOCK_SCHOLARSHIP_NAMES,
    )

    cursor.execute("CREATE TEMPORARY TABLE purge_mock_applications (application_id BIGINT PRIMARY KEY)")
    cursor.execute(
        f"""
        INSERT IGNORE INTO purge_mock_applications
        SELECT application_id
        FROM applications
        WHERE student_id IN (SELECT user_id FROM purge_mock_users)
           OR scholarship_id IN (SELECT scholarship_id FROM purge_mock_scholarships)
           OR statement IN ({placeholders(MOCK_APPLICATION_STATEMENTS)})
        """,
        MOCK_APPLICATION_STATEMENTS,
    )

    cursor.execute("CREATE TEMPORARY TABLE purge_mock_issues (issue_id BIGINT PRIMARY KEY)")
    if table_exists(cursor, "issue_reports"):
        cursor.execute(
            """
            INSERT IGNORE INTO purge_mock_issues
            SELECT issue_id
            FROM issue_reports
            WHERE reporter_id IN (SELECT user_id FROM purge_mock_users)
            """
        )


def purge(conn) -> dict[str, int]:
    summary: dict[str, int] = {}
    with conn.cursor() as cursor:
        create_temp_tables(cursor)

        execute_delete(
            cursor,
            summary,
            "notifications",
            """
            DELETE FROM notifications
            WHERE user_id IN (SELECT user_id FROM purge_mock_users)
               OR body LIKE '%TRS 逾期測試獎學金%'
               OR body LIKE '%TRS 快速測試獎學金%'
               OR body LIKE '%清寒優秀學生獎學金%'
               OR body LIKE '%教育部學產基金助學金%'
            """,
        )
        execute_delete(
            cursor,
            summary,
            "email_logs",
            "DELETE FROM email_logs WHERE user_id IN (SELECT user_id FROM purge_mock_users)",
        )
        execute_delete(
            cursor,
            summary,
            "announcements",
            "DELETE FROM announcements WHERE created_by IN (SELECT user_id FROM purge_mock_users)",
        )
        execute_delete(
            cursor,
            summary,
            "application_messages",
            """
            DELETE FROM application_messages
            WHERE application_id IN (SELECT application_id FROM purge_mock_applications)
               OR sender_id IN (SELECT user_id FROM purge_mock_users)
            """,
        )
        execute_delete(
            cursor,
            summary,
            "issue_replies",
            """
            DELETE FROM issue_replies
            WHERE issue_id IN (SELECT issue_id FROM purge_mock_issues)
               OR replier_id IN (SELECT user_id FROM purge_mock_users)
            """,
        )
        execute_delete(
            cursor,
            summary,
            "issue_reports",
            "DELETE FROM issue_reports WHERE issue_id IN (SELECT issue_id FROM purge_mock_issues)",
        )
        execute_delete(
            cursor,
            summary,
            "reviews",
            """
            DELETE FROM reviews
            WHERE application_id IN (SELECT application_id FROM purge_mock_applications)
               OR reviewer_id IN (SELECT user_id FROM purge_mock_users)
            """,
        )
        execute_delete(
            cursor,
            summary,
            "recommendations",
            """
            DELETE FROM recommendations
            WHERE application_id IN (SELECT application_id FROM purge_mock_applications)
               OR student_id IN (SELECT user_id FROM purge_mock_users)
               OR teacher_id IN (SELECT user_id FROM purge_mock_teacher_users)
            """,
        )
        execute_delete(
            cursor,
            summary,
            "supplement_requests",
            """
            DELETE FROM supplement_requests
            WHERE application_id IN (SELECT application_id FROM purge_mock_applications)
               OR reviewer_id IN (SELECT user_id FROM purge_mock_users)
            """,
        )
        execute_delete(
            cursor,
            summary,
            "application_events",
            """
            DELETE FROM application_events
            WHERE application_id IN (SELECT application_id FROM purge_mock_applications)
               OR actor_id IN (SELECT user_id FROM purge_mock_users)
            """,
        )
        execute_delete(
            cursor,
            summary,
            "application_documents",
            "DELETE FROM application_documents WHERE application_id IN (SELECT application_id FROM purge_mock_applications)",
        )
        execute_delete(
            cursor,
            summary,
            "applications",
            "DELETE FROM applications WHERE application_id IN (SELECT application_id FROM purge_mock_applications)",
        )
        execute_delete(
            cursor,
            summary,
            "student_profiles",
            "DELETE FROM student_profiles WHERE user_id IN (SELECT user_id FROM purge_mock_users)",
        )
        execute_delete(
            cursor,
            summary,
            "scholarships",
            "DELETE FROM scholarships WHERE scholarship_id IN (SELECT scholarship_id FROM purge_mock_scholarships)",
        )
        execute_delete(
            cursor,
            summary,
            "audit_logs",
            """
            DELETE FROM audit_logs
            WHERE actor_id IN (SELECT user_id FROM purge_mock_users)
               OR action = 'DEV_QUICK_LOGIN'
               OR detail LIKE '%開發快速登入%'
               OR detail LIKE '%DEVTRS%'
            """,
        )
        execute_delete(
            cursor,
            summary,
            "users",
            "DELETE FROM users WHERE user_id IN (SELECT user_id FROM purge_mock_users)",
        )
        execute_delete(
            cursor,
            summary,
            "units",
            """
            DELETE FROM units
            WHERE unit_id IN (SELECT unit_id FROM purge_mock_units)
              AND unit_id NOT IN (SELECT DISTINCT unit_id FROM users WHERE unit_id IS NOT NULL)
              AND unit_id NOT IN (SELECT DISTINCT unit_id FROM scholarships WHERE unit_id IS NOT NULL)
            """,
        )
        execute_delete(
            cursor,
            summary,
            "scholarship_options",
            f"DELETE FROM scholarship_options WHERE name IN ({placeholders(MOCK_OPTION_NAMES)})",
            MOCK_OPTION_NAMES,
        )
        execute_delete(
            cursor,
            summary,
            "system_alerts",
            """
            DELETE FROM system_alerts
            WHERE LOWER(source) LIKE '%mock%'
               OR LOWER(source) = 'manual'
               OR title LIKE '%測試%'
               OR body LIKE '%測試%'
            """,
        )

    conn.commit()
    return summary


def main() -> None:
    cfg = parse_database_url()
    try:
        conn = pymysql.connect(charset="utf8mb4", autocommit=False, **cfg)
    except pymysql.err.OperationalError as exc:
        sys.exit(f"[X] 無法連線到資料庫：{exc.args[1]}")

    try:
        summary = purge(conn)
    finally:
        conn.close()

    total = sum(summary.values())
    print(f"已清理 {total} 筆 legacy mock/dev 資料。")
    for table, count in sorted(summary.items()):
        if count:
            print(f"  - {table}: {count}")


if __name__ == "__main__":
    main()
