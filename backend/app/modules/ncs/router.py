"""NCS 通知與溝通 — API 路由
負責人：（填上負責組員姓名）
需求書：Chapter 9，功能需求 9.2.1–9.2.6
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/ncs", tags=["NCS 通知與溝通"])

# TODO(NCS):
#   GET    /api/ncs/notifications                   我的站內通知列表
#   PUT    /api/ncs/notifications/{notif_id}/read   標記已讀
#   GET    /api/ncs/announcements                   公告列表（NUKSAMS020）
#   POST   /api/ncs/announcements                   發布公告（僅管理員）
#   GET    /api/ncs/messages                        留言板（NUKSAMS018）
#   POST   /api/ncs/messages                        發送留言
#   POST   /api/ncs/issues                          問題回報（NUKSAMS021）
#
# 另外：NCS 需提供「發送通知」的共用 service 函式（例如 notify(user_id, ...)），
# 供 SAS/RAS/TRS 在狀態異動時呼叫；Email 失敗需記錄並重送（NUKSAMS036）。
# 截止提醒（NUKSAMS003）建議以排程實作，可後期再加。


@router.get("/ping")
def ping():
    """骨架測試用端點，開發開始後可移除。"""
    return {"module": "ncs", "status": "ok"}
