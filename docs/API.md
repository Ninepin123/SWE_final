# API 介面契約（前後端共同維護）

> 這份文件是**前後端的約定**：後端改了 request/response 格式，必須同步更新這裡，
> 並通知對應的前端負責人。每個子系統只編輯自己的章節，避免衝突。
>
> 後端啟動後也可直接看自動文件：<http://localhost:8000/docs>（Swagger UI）。

## 共用約定

- 路徑前綴：`/api/<子系統代號>/...`，例如 `/api/aas/login`
- 認證：除登入外的端點都需要 `Authorization: Bearer <JWT>`
- 時間格式：ISO 8601（`2026-06-12T10:00:00`）
- 錯誤回應格式（FastAPI 預設）：`{ "detail": "錯誤訊息" }`
- 角色：`STUDENT` / `TEACHER` / `SPONSOR` / `REVIEWER` / `ADMIN`

---

## AAS 帳號與權限管理

### POST /api/aas/login
- 公開（不需 token）。
- Request：`{ "account": "A1125529", "password": "password123" }`
- Response：`{ "access_token": "<JWT>", "token_type": "bearer", "user": { "user_id": 5, "account": "A1125529", "name": "黃文傑", "role": "STUDENT", "email": "...", "unit_id": null, "department": "資訊工程學系" } }`

### POST /api/aas/logout
- 需登入。JWT 無狀態，前端清除 token 即登出。Response：`{ "detail": "已登出" }`

### GET /api/aas/me
- 需登入。Response：同上 `user` 物件（`UserOut`）。

### GET /api/aas/users  （僅 ADMIN）
- Response：`UserOut[]`

### POST /api/aas/users  （僅 ADMIN）
- Request：`{ "account", "password", "name", "role", "email?", "unit_id?", "department?", "gpa?" }`
- Response：`UserOut`（201）

---

## SMS 獎助學金資料管理

### GET /api/sms/scholarships?only_open=false  （需登入）
- `only_open=true` 只回傳開放中且未截止者。
- Response：`ScholarshipOut[]`，其中
  `ScholarshipOut = { scholarship_id, name, year, amount, quota, min_gpa, department_limit, category, description, deadline, status, unit_id, unit_name }`
- `category`：`SCHOOL/GOVERNMENT/PRIVATE/LOW_INCOME/MERIT/OTHER`；`status`：`OPEN/CLOSED`

### GET /api/sms/scholarships/{id}  （需登入）
- Response：`ScholarshipOut`

### POST /api/sms/scholarships  （僅 SPONSOR / ADMIN）
- 以登入者的 `unit_id` 作為提供單位。
- Request：`{ "name", "year", "amount", "quota", "min_gpa?", "department_limit?", "category?", "description?", "deadline?" }`
- Response：`ScholarshipOut`（201）

---

## SAS 學生申請

### POST /api/sas/applications  （僅 STUDENT）
- 檢查：獎學金開放中、未截止、GPA 達門檻、未重複申請。
- Request：`{ "scholarship_id": 1, "statement": "..." }`
- Response：`ApplicationOut = { application_id, scholarship_id, scholarship_name, status, statement, created_at }`（201）
- `status` 初始為 `UNDER_REVIEW`。

### GET /api/sas/applications/me  （僅 STUDENT）
- Response：`ApplicationOut[]`
- `status`：`UNDER_REVIEW`(審核中) / `NEED_SUPPLEMENT`(需補件) / `APPROVED`(已通過) / `REJECTED`(未通過)

---

## RAS 審查與核發

### GET /api/ras/applications?scholarship_id=  （僅 REVIEWER / ADMIN）
- 預設依申請人 GPA 由高到低排序。
- Response：`ReviewApplicationOut[] = { application_id, student_id, student_name, scholarship_id, scholarship_name, gpa, status, statement, created_at }`

### POST /api/ras/applications/{id}/decision  （僅 REVIEWER / ADMIN）
- Request：`{ "result": "APPROVED" | "REJECTED" | "NEED_SUPPLEMENT", "comment": "..." }`
- 行為：寫入一筆審查紀錄，並透過 SAS 介面更新該申請案狀態。
- Response：`{ "detail": "審查完成", "application_id": 1, "result": "APPROVED" }`

---

## TRS 教師推薦

（v1 尚未實作，後續版本補上。）

## NCS 通知與溝通

（v1 尚未實作，後續版本補上。）
