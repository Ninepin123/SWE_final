# API 介面契約（前後端共同維護）

> 這份文件是**前後端的約定**：後端改了 request/response 格式，必須同步更新這裡，
> 並通知對應的前端負責人。每個子系統只編輯自己的章節，避免衝突。
>
> 後端啟動後也可直接看自動文件：<http://localhost:8000/docs>（Swagger UI）。

## 共用約定

- 路徑前綴：`/api/<子系統代號>/...`，例如 `/api/aas/login`
- 認證：除登入外的端點都需要 `Authorization: Bearer <JWT>`（AAS 完成後生效）
- 時間格式：ISO 8601（`2026-06-12T10:00:00+08:00`）
- 錯誤回應格式（FastAPI 預設）：`{ "detail": "錯誤訊息" }`
- 分頁參數：`?page=1&page_size=20`，回應 `{ "items": [...], "total": n }`

## AAS 帳號與權限管理

（負責人填寫，範例格式如下）

<!--
### POST /api/aas/login
Request:  { "account": "A1125511", "password": "..." }
Response: { "access_token": "...", "token_type": "bearer", "user": { "id": 1, "name": "...", "role": "STUDENT" } }
-->

## SMS 獎助學金資料管理

（負責人填寫）

## SAS 學生申請

（負責人填寫）

## TRS 教師推薦

（負責人填寫）

## RAS 審查與核發

（負責人填寫）

## NCS 通知與溝通

（負責人填寫）
