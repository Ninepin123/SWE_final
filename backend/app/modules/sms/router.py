"""SMS 獎助學金資料管理 — API 路由
負責人：（填上負責組員姓名）
需求書：Chapter 5，功能需求 5.2.1–5.2.5
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/sms", tags=["SMS 獎助學金資料管理"])

# TODO(SMS):
#   GET    /api/sms/scholarships                    獎學金列表（含分類/標籤篩選, NUKSAMS022/023）
#   POST   /api/sms/scholarships                    新增獎學金（NUKSAMS005，獎助單位）
#   GET    /api/sms/scholarships/{scholarship_id}   獎學金詳細資料
#   PUT    /api/sms/scholarships/{scholarship_id}   修改獎學金（含條件/名額/截止日, NUKSAMS006/007）
#   DELETE /api/sms/scholarships/{scholarship_id}   刪除獎學金
#   GET    /api/sms/categories                      分類列表
#
# 注意：截止時間到達或名額額滿時自動關閉申請（NUKSAMS007）——
#       建議以查詢時判斷（status 計算欄位），不要依賴排程。


@router.get("/ping")
def ping():
    """骨架測試用端點，開發開始後可移除。"""
    return {"module": "sms", "status": "ok"}
