"""AAS 帳號與權限管理 — API 路由
負責人：（填上負責組員姓名）
需求書：Chapter 4，功能需求 4.2.1–4.2.6
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/aas", tags=["AAS 帳號與權限管理"])

# TODO(AAS):
#   POST   /api/aas/login            使用者登入（UC001），回傳 JWT
#   POST   /api/aas/logout           登出（UC002）
#   GET    /api/aas/users            查詢帳號（UC004，僅管理員）
#   POST   /api/aas/users            新增帳號（UC003，僅管理員）
#   PUT    /api/aas/users/{user_id}  修改帳號（UC005，僅管理員）
#   DELETE /api/aas/users/{user_id}  刪除帳號（僅管理員）
#   GET    /api/aas/audit-logs       操作紀錄查詢（4.2.5）
#
# 另外：AAS 需提供「目前登入者」的共用 dependency（get_current_user），
# 完成後放在本模組並在 docs/DEVELOPMENT.md 公告，供其他子系統 import 使用。


@router.get("/ping")
def ping():
    """骨架測試用端點，開發開始後可移除。"""
    return {"module": "aas", "status": "ok"}
