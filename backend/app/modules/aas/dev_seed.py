"""AAS — 開發用種子資料（一次性、可重複執行）。

建立示範單位、各角色帳號與兩筆示範獎學金，方便團隊立刻試跑 v1 流程。
（為了讓密碼用與登入相同的 bcrypt 雜湊，種子改用 Python 撰寫而非 SQL。）

用法（先啟動過一次 start.bat 讓資料表建好，再於 backend 目錄、venv 啟用後執行）：
    Windows:  .venv\\Scripts\\python -m app.modules.aas.dev_seed
    macOS/Linux: python -m app.modules.aas.dev_seed

所有帳號的密碼皆為： password123
"""
from sqlalchemy import select

from app.core.database import SessionLocal
from app.modules.aas.models import Unit, User
from app.modules.aas.security import hash_password
from app.modules.sms.models import Scholarship

DEMO_PASSWORD = "password123"


def _get_or_create_unit(db, name, type_, email):
    unit = db.scalar(select(Unit).where(Unit.name == name))
    if unit:
        return unit
    unit = Unit(name=name, type=type_, contact_email=email)
    db.add(unit)
    db.flush()
    return unit


def _get_or_create_user(db, account, name, role, **extra):
    user = db.scalar(select(User).where(User.account == account))
    if user:
        return user
    user = User(
        account=account,
        password=hash_password(DEMO_PASSWORD),
        name=name,
        role=role,
        status="ACTIVE",
        **extra,
    )
    db.add(user)
    db.flush()
    return user


def _ensure_scholarship(db, name, **fields):
    if db.scalar(select(Scholarship).where(Scholarship.name == name)):
        return
    db.add(Scholarship(name=name, **fields))


def main():
    db = SessionLocal()
    try:
        osa = _get_or_create_unit(db, "學生事務處生活輔導組", "SCHOOL", "osa@nuk.edu.tw")
        moe = _get_or_create_unit(db, "教育部", "GOVERNMENT", "moe@example.gov.tw")

        _get_or_create_user(db, "admin", "系統管理員", "ADMIN", email="admin@nuk.edu.tw")
        sponsor = _get_or_create_user(db, "sponsor", "生輔組承辦人", "SPONSOR", email="sponsor@nuk.edu.tw", unit_id=osa.unit_id)
        _get_or_create_user(db, "reviewer", "審查委員", "REVIEWER", email="reviewer@nuk.edu.tw", unit_id=osa.unit_id)
        _get_or_create_user(db, "teacher", "陳老師", "TEACHER", email="teacher@nuk.edu.tw")
        _get_or_create_user(db, "A1125529", "黃文傑", "STUDENT", email="student1@nuk.edu.tw", gpa=3.85, department="資訊工程學系")
        _get_or_create_user(db, "A1125599", "王小明", "STUDENT", email="student2@nuk.edu.tw", gpa=3.20, department="電機工程學系")
        db.flush()

        _ensure_scholarship(
            db, "清寒優秀學生獎學金",
            unit_id=osa.unit_id, year=2026, amount=20000, quota=5, min_gpa=3.50,
            category="LOW_INCOME", description="提供家境清寒且學業成績優良之在學學生申請。",
            status="OPEN", created_by=sponsor.user_id,
        )
        _ensure_scholarship(
            db, "教育部學產基金助學金",
            unit_id=moe.unit_id, year=2026, amount=15000, quota=10, min_gpa=None,
            category="GOVERNMENT", description="教育部提供之助學金，不限 GPA。",
            status="OPEN", created_by=sponsor.user_id,
        )
        db.commit()
        print("✅ 示範資料建立完成。")
        print("   可用帳號（密碼皆為 password123）：")
        print("   - admin     系統管理員")
        print("   - sponsor   獎助單位（可新增獎學金）")
        print("   - reviewer  審查人員（可審查申請）")
        print("   - teacher   老師")
        print("   - A1125529  學生（GPA 3.85）")
        print("   - A1125599  學生（GPA 3.20）")
    finally:
        db.close()


if __name__ == "__main__":
    main()
