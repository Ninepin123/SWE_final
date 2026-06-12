"""SAS 學生申請 — API 路由
負責人：（填上負責組員姓名）
需求書：Chapter 6，功能需求 6.2.1–6.2.7
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/sas", tags=["SAS 學生申請"])

# TODO(SAS):
#   GET    /api/sas/profile                         查看個人資料（6.2.1）
#   PUT    /api/sas/profile                         修改個人資料（學號等核心欄位不可改）
#   GET    /api/sas/scholarships/available          可申請獎學金查詢與篩選（NUKSAMS013，向 SMS 取資料）
#   POST   /api/sas/applications                    線上申請（NUKSAMS011）
#   GET    /api/sas/applications                    我的申請進度列表（NUKSAMS014）
#   POST   /api/sas/applications/{app_id}/documents 上傳文件（限制格式與大小, 6.2.4）
#   POST   /api/sas/applications/{app_id}/supplements 補件上傳（6.2.6）
#
# 注意：申請截止後鎖定（NUKSAMS008）—— 在 service 層檢查獎學金截止時間，
#       截止後一律拒絕修改與上傳。


@router.get("/ping")
def ping():
    """骨架測試用端點，開發開始後可移除。"""
    return {"module": "sas", "status": "ok"}
