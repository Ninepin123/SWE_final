"""TRS 教師推薦 — API 路由
負責人：（填上負責組員姓名）
需求書：Chapter 7，功能需求 7.2.1–7.2.6
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/trs", tags=["TRS 教師推薦"])

# TODO(TRS):
#   GET    /api/trs/requests                        推薦案件列表（僅自己負責的, NUKSAMS004）
#   GET    /api/trs/requests/{request_id}/student   學生完整資料檢視（NUKSAMS001, 7.2.2）
#   PUT    /api/trs/requests/{request_id}/letter    撰寫/暫存推薦信（草稿, 7.2.4）
#   POST   /api/trs/requests/{request_id}/letter/submit  提交推薦信
#   GET    /api/trs/requests/{request_id}/progress  案件進度查詢（7.2.6）
#
# 注意：推薦信內容僅撰寫老師與審查人員可見，學生只能看到是否已提交（7.2.5）。


@router.get("/ping")
def ping():
    """骨架測試用端點，開發開始後可移除。"""
    return {"module": "trs", "status": "ok"}
