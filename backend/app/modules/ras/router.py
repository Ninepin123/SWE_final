"""RAS 審查與核發 — API 路由
負責人：（填上負責組員姓名）
需求書：Chapter 8，功能需求 8.2.1–8.2.8
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/ras", tags=["RAS 審查與核發"])

# TODO(RAS):
#   GET    /api/ras/applications                    申請案件查詢與篩選（NUKSAMS002，僅本單位, NUKSAMS010）
#   GET    /api/ras/applications/{app_id}           申請資料檢視（含文件與推薦信, 8.2.2）
#   GET    /api/ras/applications/ranking            自動排序（依 GPA/條件, NUKSAMS015）
#   POST   /api/ras/applications/{app_id}/decision  審查通過/不通過（NUKSAMS016）
#   POST   /api/ras/applications/{app_id}/supplement-request  發送補件要求（NUKSAMS017）
#   GET    /api/ras/awards                          核發名單（8.2.6）
#   GET    /api/ras/statistics                      年度統計（NUKSAMS019，支援匯出 PDF/Excel）
#
# 注意：單位資料隔離（NUKSAMS041）—— 所有查詢必須以登入者的 unit_id 過濾。


@router.get("/ping")
def ping():
    """骨架測試用端點，開發開始後可移除。"""
    return {"module": "ras", "status": "ok"}
