"""RAS — 商業邏輯層（審查與核發，需求書 8.2）。

審查時：寫入 reviews 紀錄（審查人員/結果/時間/意見，item 6），
透過 SAS 介面更新申請狀態，並透過 NCS 通知學生審查結果。
審查清單會帶出最近一次審查紀錄與已送出的推薦信內容。
"""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.aas.models import User
from app.modules.ncs import service as ncs_service
from app.modules.ras.models import Review
from app.modules.ras.schemas import ReviewDecision
from app.modules.sas import service as sas_service
from app.modules.sas.models import Application, ApplicationDocument
from app.modules.sas.schemas import SupplementRequestCreate
from app.modules.sms.models import Scholarship
from app.modules.trs import service as trs_service

DECISION_TO_STATUS = {"APPROVED": "APPROVED", "REJECTED": "REJECTED", "NEED_SUPPLEMENT": "NEED_SUPPLEMENT"}
RESULT_LABEL = {"APPROVED": "已通過", "REJECTED": "未通過", "NEED_SUPPLEMENT": "需補件"}


def _latest_review(db: Session, application_id: int):
    return db.execute(
        select(Review, User.name)
        .join(User, Review.reviewer_id == User.user_id)
        .where(Review.application_id == application_id)
        .order_by(Review.reviewed_at.desc(), Review.review_id.desc())
        .limit(1)
    ).first()


def list_applications_for_review(db: Session, reviewer: User, scholarship_id: int | None = None, sort_by: str = "gpa_desc") -> list[dict]:
    stmt = (
        select(Application, User.name, User.gpa, Scholarship.name)
        .join(User, Application.student_id == User.user_id)
        .join(Scholarship, Application.scholarship_id == Scholarship.scholarship_id)
    )
    # Unit isolation: Reviewers can only see applications for their unit
    if reviewer.role == "REVIEWER" and reviewer.unit_id:
        stmt = stmt.where(Scholarship.unit_id == reviewer.unit_id)
        
    if scholarship_id is not None:
        stmt = stmt.where(Application.scholarship_id == scholarship_id)
        
    if sort_by == "gpa_desc":
        stmt = stmt.order_by(User.gpa.desc(), Application.created_at.asc())
    elif sort_by == "gpa_asc":
        stmt = stmt.order_by(User.gpa.asc(), Application.created_at.asc())
    elif sort_by == "time_desc":
        stmt = stmt.order_by(Application.created_at.desc())
    elif sort_by == "time_asc":
        stmt = stmt.order_by(Application.created_at.asc())
    else:
        stmt = stmt.order_by(User.gpa.desc(), Application.created_at.asc())
        
    rows = db.execute(stmt).all()

    out: list[dict] = []
    for app, student_name, gpa, scholarship_name in rows:
        review_row = _latest_review(db, app.application_id)
        recs = trs_service.get_recommendations_for_reviewer(db, app.application_id, reviewer)

        # 申請附件存於 application_documents（線上申請以文字內容代替實體附件）；
        # 審查人員需看到完整文件內容（需求書 8.2.2）。
        doc_rows = db.execute(
            select(ApplicationDocument)
            .where(ApplicationDocument.application_id == app.application_id)
            .order_by(ApplicationDocument.document_id)
        ).scalars().all()
        docs = [
            {"title": d.title, "document_type": d.document_type, "content_text": d.content_text}
            for d in doc_rows
        ]

        out.append({
            "application_id": app.application_id,
            "student_id": app.student_id,
            "student_name": student_name,
            "scholarship_id": app.scholarship_id,
            "scholarship_name": scholarship_name,
            "gpa": float(gpa) if gpa is not None else None,
            "status": app.status,
            "supplement_deadline": app.supplement_deadline,
            "statement": app.statement,
            "contact_phone": app.contact_phone,
            "address": app.address,
            "household_status": app.household_status,
            "academic_note": app.academic_note,
            "documents": docs,
            "created_at": app.created_at,
            "reviewer_name": review_row[1] if review_row else None,
            "review_result": review_row[0].result if review_row else None,
            "review_comment": review_row[0].comment if review_row else None,
            "reviewed_at": review_row[0].reviewed_at if review_row else None,
            "recommendations": recs,
        })
    return out


def decide(db: Session, reviewer: User, application_id: int, data: ReviewDecision) -> dict:
    if data.result not in DECISION_TO_STATUS:
        raise HTTPException(status_code=400, detail="審查結果不正確")
    app = db.get(Application, application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="找不到申請案")
    review = Review(
        application_id=application_id, reviewer_id=reviewer.user_id, result=data.result, comment=data.comment
    )
    db.add(review)
    if data.result == "NEED_SUPPLEMENT":
        if data.supplement_deadline is None:
            raise HTTPException(status_code=400, detail="請設定補件期限")
        app.supplement_deadline = data.supplement_deadline
        sas_service.create_supplement_request(
            db,
            reviewer,
            application_id,
            SupplementRequestCreate(
                required_items=(data.comment or "請補件"),
                deadline=data.supplement_deadline,
            ),
        )
    else:
        sas_service.set_application_status(db, application_id, DECISION_TO_STATUS[data.result], commit=False)
        db.commit()
    # 通知學生審查結果
    sch = db.get(Scholarship, app.scholarship_id)
    sch_name = sch.name if sch else "獎學金"
    ncs_service.create_notification(
        db, app.student_id, "審查結果通知",
        f"你的「{sch_name}」申請審查結果：{RESULT_LABEL[data.result]}。", commit=True,
    )
    return {"detail": "審查完成", "application_id": application_id, "result": data.result}


def log_application_view(db: Session, reviewer: User, application_id: int) -> dict:
    from app.modules.aas.models import AuditLog
    log = AuditLog(
        actor_id=reviewer.user_id,
        action="VIEW_APPLICATION",
        target_type="Application",
        target_id=application_id,
        detail=f"審查人員 {reviewer.name} 查看申請案件 {application_id}"
    )
    db.add(log)
    db.commit()
    return {"detail": "已記錄查看操作"}


def get_award_list(db: Session, reviewer: User, year: int | None = None, scholarship_id: int | None = None) -> list[dict]:
    stmt = (
        select(
            Application.application_id, Application.student_id, Application.status,
            User.name.label("student_name"), User.account.label("student_account"), User.department,
            Scholarship.scholarship_id, Scholarship.name.label("scholarship_name"), Scholarship.year, Scholarship.amount
        )
        .join(User, Application.student_id == User.user_id)
        .join(Scholarship, Application.scholarship_id == Scholarship.scholarship_id)
        .where(Application.status == "APPROVED")
    )
    # 單位隔離
    if reviewer.role == "REVIEWER" and reviewer.unit_id:
        stmt = stmt.where(Scholarship.unit_id == reviewer.unit_id)
        
    if year is not None:
        stmt = stmt.where(Scholarship.year == year)
    if scholarship_id is not None:
        stmt = stmt.where(Application.scholarship_id == scholarship_id)
        
    stmt = stmt.order_by(Scholarship.year.desc(), Scholarship.scholarship_id, User.department, User.name)
    rows = db.execute(stmt).all()

    out = []
    for row in rows:
        review_row = _latest_review(db, row.application_id)
        out.append({
            "application_id": row.application_id,
            "student_id": row.student_id,
            "student_name": row.student_name,
            "student_account": row.student_account,
            "department": row.department,
            "scholarship_id": row.scholarship_id,
            "scholarship_name": row.scholarship_name,
            "year": row.year,
            "amount": row.amount,
            "status": row.status,
            "reviewed_at": review_row[0].reviewed_at if review_row else None
        })
    return out


def get_annual_statistics(db: Session, reviewer: User, year: int | None = None) -> dict:
    from sqlalchemy import func
    from sqlalchemy.types import Integer
    from app.modules.aas.models import Unit

    stmt = (
        select(
            Unit.name.label("unit_name"),
            func.count(Application.application_id).label("total_applications"),
            func.sum(
                func.cast(Application.status == "APPROVED", Integer)
            ).label("approved_count"),
            func.sum(
                func.cast(Application.status == "APPROVED", Integer) * Scholarship.amount
            ).label("total_amount")
        )
        .select_from(Application)
        .join(Scholarship, Application.scholarship_id == Scholarship.scholarship_id)
        .join(Unit, Scholarship.unit_id == Unit.unit_id)
    )

    if reviewer.role == "REVIEWER" and reviewer.unit_id:
        stmt = stmt.where(Scholarship.unit_id == reviewer.unit_id)
    if year is not None:
        stmt = stmt.where(Scholarship.year == year)

    stmt = stmt.group_by(Unit.name)
    rows = db.execute(stmt).all()

    total_winners = 0
    total_amount = 0
    unit_stats = []

    for row in rows:
        approved = int(row.approved_count or 0)
        total_app = int(row.total_applications or 0)
        amount = int(row.total_amount or 0)
        
        total_winners += approved
        total_amount += amount
        pass_rate = round((approved / total_app) * 100, 2) if total_app > 0 else 0.0
        
        unit_stats.append({
            "unit_name": row.unit_name,
            "total_applications": total_app,
            "approved_count": approved,
            "pass_rate": pass_rate
        })

    return {
        "year": year,
        "total_winners": total_winners,
        "total_amount": total_amount,
        "unit_stats": unit_stats
    }


def export_statistics_csv(db: Session, reviewer: User, year: int | None = None) -> str:
    import csv
    import io
    
    stmt = (
        select(
            Application.status,
            User.name.label("student_name"), User.account.label("student_account"), User.department,
            Scholarship.name.label("scholarship_name"), Scholarship.amount
        )
        .join(User, Application.student_id == User.user_id)
        .join(Scholarship, Application.scholarship_id == Scholarship.scholarship_id)
    )
    if reviewer.role == "REVIEWER" and reviewer.unit_id:
        stmt = stmt.where(Scholarship.unit_id == reviewer.unit_id)
    if year is not None:
        stmt = stmt.where(Scholarship.year == year)
        
    stmt = stmt.order_by(Scholarship.year.desc(), Scholarship.scholarship_id, User.department, User.name)
    rows = db.execute(stmt).all()

    output = io.StringIO()
    # Add BOM for excel to open correctly
    output.write('\ufeff')
    writer = csv.writer(output)
    
    writer.writerow(["學號", "姓名", "系所", "申請獎學金名稱", "預定核發金額", "審核狀態"])
    
    total_winners = 0
    total_amount = 0
    
    status_map = {
        "SUBMITTED": "已送出",
        "UNDER_REVIEW": "審查中",
        "NEEDS_SUPPLEMENT": "需補件",
        "APPROVED": "已通過",
        "REJECTED": "未通過"
    }
    
    for row in rows:
        is_approved = row.status == "APPROVED"
        amount = int(row.amount) if is_approved else 0
        status_label = status_map.get(row.status, row.status)

        if is_approved:
            total_winners += 1
            total_amount += amount

        writer.writerow([
            row.student_account,
            row.student_name,
            row.department,
            row.scholarship_name,
            amount,
            status_label
        ])

    total_apps = len(rows)
    pass_rate = round((total_winners / total_apps) * 100, 2) if total_apps > 0 else 0.0
            
    writer.writerow([])
    writer.writerow(["【總體統計】"])
    writer.writerow(["申請總數", total_apps])
    writer.writerow(["總計核發人數", total_winners])
    writer.writerow(["通過比例", f"{pass_rate}%"])
    writer.writerow(["總計核發金額", total_amount])
    
    # 取得各單位統計 (使用既有的 get_annual_statistics 邏輯)
    writer.writerow([])
    writer.writerow(["【各單位統計】"])
    writer.writerow(["提供單位", "申請總數", "通過人數", "通過比例"])
    
    stats = get_annual_statistics(db, reviewer, year)
    for unit in stats["unit_stats"]:
        writer.writerow([
            unit["unit_name"],
            unit["total_applications"],
            unit["approved_count"],
            f"{unit['pass_rate']}%"
        ])

    return output.getvalue()


def export_statistics_pdf(db: Session, reviewer: User, year: int | None = None) -> bytes:
    """RAS016-017：年度統計報表 PDF 匯出（支援中文，使用 reportlab 內建 CID 字型）。"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        )
    except ImportError:  # pragma: no cover - 僅在未安裝 reportlab 時觸發
        raise HTTPException(status_code=503, detail="PDF 匯出服務未啟用（缺少 reportlab）")

    import io

    font_name = "STSong-Light"  # reportlab 內建中日韓字型，免外掛字型檔
    pdfmetrics.registerFont(UnicodeCIDFont(font_name))

    stats = get_annual_statistics(db, reviewer, year)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("CJKTitle", parent=styles["Title"], fontName=font_name)
    normal = ParagraphStyle("CJKNormal", parent=styles["Normal"], fontName=font_name, fontSize=11, leading=18)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title="獎助學金統計報表")
    story = []

    year_label = f"{year} 學年度" if year else "全部年度"
    story.append(Paragraph(f"高雄大學獎助學金統計報表（{year_label}）", title_style))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(f"核發總人數：{stats['total_winners']} 人", normal))
    story.append(Paragraph(f"核發總金額：NT$ {stats['total_amount']:,}", normal))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("各單位統計", normal))
    story.append(Spacer(1, 3 * mm))

    table_data = [["提供單位", "申請總數", "核發人數", "通過比例"]]
    for unit in stats["unit_stats"]:
        table_data.append([
            unit["unit_name"],
            str(unit["total_applications"]),
            str(unit["approved_count"]),
            f"{unit['pass_rate']}%",
        ])
    if len(table_data) == 1:
        table_data.append(["（無資料）", "-", "-", "-"])

    table = Table(table_data, colWidths=[70 * mm, 30 * mm, 30 * mm, 30 * mm])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2f6b4f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f6f3")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)

    doc.build(story)
    return buf.getvalue()
