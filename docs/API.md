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

### GET /api/sas/scholarships/available  （僅 STUDENT）
- 依目前登入學生的 `department` 與 `gpa` 判斷資格。
- Query：`keyword?`, `category?`, `department?`, `deadline_before?`, `eligible_only?`
- Response：`ScholarshipEligibilityOut[]`
- 每筆包含 `remaining_quota`, `already_applied`, `can_apply`, `ineligibility_reasons`。
- 不可申請原因可能包含：未開放、已截止、名額已滿、GPA 未達、科系不符、資料不足或已申請。
- 目前 SMS 尚未提供必要文件資料結構，因此 `required_documents` 暫時回傳空陣列。

### POST /api/sas/applications  （僅 STUDENT）
- 建立申請草稿；檢查獎學金開放中、未截止、資格符合且沒有重複草稿或申請。
- Request：`{ scholarship_id, statement?, contact_phone?, address?, household_status?, academic_note? }`
- Response：`ApplicationOut`（201），初始 `status=DRAFT`。

### PUT /api/sas/applications/{id}  （僅申請學生）
- 更新自己的草稿。正式送出、已截止或關閉後不可修改。
- Request：`{ statement?, contact_phone?, address?, household_status?, academic_note? }`

### POST /api/sas/applications/{id}/submit  （僅申請學生）
- 正式送出草稿；重新檢查資格、期限、申請表必填欄位及至少一份文字文件。
- 成功後狀態由 `DRAFT` 改為 `UNDER_REVIEW`，寫入 `submitted_at` 並發送通知。
- 正式送出後不可再次修改或重複送出。

### GET /api/sas/applications/{id}  （僅申請學生）
- 查詢自己的單筆申請或草稿。

### GET /api/sas/applications/{id}/events  （僅申請學生）
- 查詢自己的申請進度與重要操作紀錄。
- 記錄草稿建立/修改、文字文件異動、正式送出、補件要求、補件提交及狀態變更。
- Response 包含操作者、事件類型、前後狀態、摘要與時間；不複製完整敏感文件內容。

### GET /api/sas/applications/{id}/documents  （僅申請學生）
- 查詢自己的申請文字文件。

### POST /api/sas/applications/{id}/documents  （僅申請學生）
- 新增或更新同類型文字文件。
- Request：`{ document_type, title, content_text }`
- `document_type`：`TRANSCRIPT / AUTOBIOGRAPHY / CERTIFICATE / OTHER`
- 目前只儲存文字內容；資料表預留實體檔案路徑、MIME type 與檔案大小欄位。

### DELETE /api/sas/applications/{id}/documents/{document_id}
- 刪除自己的草稿文件。
- 正式送出、申請截止或獎學金關閉後禁止修改與刪除。

### POST /api/sas/applications/{id}/supplement-requests  （僅 REVIEWER）
- 建立補件要求。Request：`{ required_items, deadline }`
- 審查人員必須與該獎學金屬於相同單位。
- 建立後申請狀態改為 `NEED_SUPPLEMENT`，並通知學生。
- 供 RAS 子系統呼叫；RAS 不應直接寫入 SAS 資料表。

### GET /api/sas/applications/{id}/supplement-requests  （僅申請學生）
- 查詢自己的補件要求、期限、狀態與歷史內容。

### POST /api/sas/applications/{id}/supplement-requests/{supplement_id}/submit
- 學生在期限內提交文字補件：`{ response_text }`
- 成功後補件狀態改為 `SUBMITTED`，申請重新進入 `UNDER_REVIEW`，並通知審查人員。

### GET /api/sas/applications/me  （僅 STUDENT）
- Response：`ApplicationOut[]`
- `status`：`DRAFT`(草稿) / `UNDER_REVIEW`(審核中) / `NEED_SUPPLEMENT`(需補件) / `APPROVED`(已通過) / `REJECTED`(未通過)
- `ApplicationOut` 包含 `created_at`, `updated_at`, `submitted_at`, `can_edit`。

---

## RAS 審查與核發

### GET /api/ras/applications?scholarship_id=  （僅 REVIEWER；v2 起移除 ADMIN）
- 預設依申請人 GPA 由高到低排序。
- Response：`ReviewApplicationOut[] = { application_id, student_id, student_name, scholarship_id, scholarship_name, gpa, status, statement, created_at }`

### POST /api/ras/applications/{id}/decision  （僅 REVIEWER；v2 起移除 ADMIN）
- Request：`{ "result": "APPROVED" | "REJECTED" | "NEED_SUPPLEMENT", "comment": "..." }`
- 行為：寫入一筆審查紀錄，並透過 SAS 介面更新該申請案狀態。
- Response：`{ "detail": "審查完成", "application_id": 1, "result": "APPROVED" }`

---

## TRS 教師推薦

### GET /api/trs/recommendations/teacher  （僅 TEACHER）
- Query：`keyword?`, `status?`, `sort_by?`, `order?`
- Response：`RecommendationTeacherOut[]`
- 僅回傳目前登入教師自己的推薦案件。

### PUT /api/trs/recommendations/{rec_id}  （僅 TEACHER）
- Request：`{ content?: string, submit: boolean }`
- `submit=false`：存草稿（`DRAFT`）
- `submit=true`：正式提交（`SUBMITTED`）
- 已提交案件不可再修改（回 409）。
- 提交後會發送站內通知給學生與審查對象。

### GET /api/trs/recommendations/{rec_id}/student-profile  （僅 TEACHER）
- 只允許被指派該推薦案件的教師查看。
- 非負責教師或學生存取回 403。

### GET /api/trs/recommendations/student  （僅 STUDENT）
- Response 僅含推薦狀態資訊：`rec_id, application_id, teacher_id/teacher_name, status, submitted_at, deadline, scholarship_name`。
- 不回傳推薦信內容欄位（`content`, `draft_content`, `letter_content`）。

### GET /api/trs/recommendations/teacher/dashboard  （僅 TEACHER）
- 回傳 `total_count`, `pending_count`, `draft_count`, `submitted_count`, `due_soon_count`, `overdue_count`。

### POST /api/trs/recommendations/due-soon-notifications  （僅 ADMIN）
- 手動觸發 48 小時內即將截止且未提交推薦案件提醒（站內通知）。
- Response：`{ checked_count, created_count }`
- 僅手動觸發，不含排程器。

## NCS 通知與溝通

（v2 已實作，詳見下方「v2 變更與新增 → NCS」。）

---

# v2 變更與新增（依審查回饋）

> v2 修正了審查權限、補齊帳號/獎學金的修改與刪除、新增申請表欄位與學生個人資料維護，
> 並實作 TRS 推薦信與 NCS 通知/公告，審查改為僅 REVIEWER 並會留下紀錄。

## AAS（變更/新增）
- **GET /api/aas/teachers**（任何登入者）：老師清單 `TeacherOut[] = { user_id, name, department }`，給學生邀請推薦用。
- **PUT /api/aas/users/{id}**（僅 ADMIN）：修改帳號。Request 為 `UserUpdate`（只送要改的欄位；`password` 留空表示不改）。
- **DELETE /api/aas/users/{id}**（僅 ADMIN）：刪除帳號；若已有關聯資料回 409（建議改為停用 `status=DISABLED`）。
- **GET /api/aas/audit-logs**（僅 ADMIN）：稽核紀錄 `AuditLogOut[] = { log_id, actor_id, actor_name, action, target_type, target_id, detail, created_at }`。
- `UserOut` 增加 `email, unit_id, department, gpa, status`。

## SMS（新增）
- **PUT /api/sms/scholarships/{id}**（SPONSOR/ADMIN）：修改獎學金（含 `status` OPEN/CLOSED）。獎助單位僅能改自己單位的。
- **DELETE /api/sms/scholarships/{id}**（SPONSOR/ADMIN）：刪除；若已有申請回 409（可改為將狀態設為 CLOSED）。

## SAS（變更/新增）
- 申請表（`POST /api/sas/applications`）新增欄位：`statement(申請理由), contact_phone, address, household_status, academic_note`。
- 申請成功會透過 NCS 發送通知給學生。
- **GET /api/sas/profile**（僅 STUDENT）：`ProfileOut = { user_id, account, name, department, grade, gpa, identity_type, email, contact_phone, address, emergency_contact_name, emergency_contact_phone }`。
  - `account/name/department/grade/gpa/identity_type` 為核心身分資料，只讀。
  - `email/contact_phone/address/emergency_contact_name/emergency_contact_phone` 為學生可維護的聯絡資料。
- **PUT /api/sas/profile**（僅 STUDENT）：只接受 `email, contact_phone, address, emergency_contact_name, emergency_contact_phone`。即使 request 夾帶學號、姓名、科系、年級、GPA 或身份類別，也不會修改核心資料。

## RAS（變更）
- 兩支端點改為 **僅 REVIEWER**（移除 ADMIN）。
- `GET /api/ras/applications` 回傳加入：完整申請表欄位、`recommendations[]`（僅 `SUBMITTED` 會有 `content`；`REQUESTED/DRAFT/PENDING` 只回傳狀態與 `content_available=false`）、以及最近一次審查紀錄 `reviewer_name / review_result / review_comment / reviewed_at`。
- `POST .../decision` 會寫入審查紀錄並通知學生審查結果。

## TRS 教師推薦（新增實作）
- **POST /api/trs/recommendations**（STUDENT）：`{ application_id, teacher_id }` 邀請老師；通知該老師。
- **GET /api/trs/recommendations/student**（STUDENT）：自己各申請的推薦狀態（**不含內容**，隱私）。
- **GET /api/trs/recommendations/teacher**（TEACHER）：被指派的推薦邀請（含內容）。
- **PUT /api/trs/recommendations/{rec_id}**（TEACHER）：`{ content, submit }`，`submit=true` 送出（通知學生），否則存草稿。
- 狀態：`REQUESTED`(已邀請) / `DRAFT`(撰寫中) / `SUBMITTED`(已送出)。

## NCS 通知與溝通（新增實作）
- **GET /api/ncs/notifications**（登入者）：我的通知 `NotificationOut[]`。
- **GET /api/ncs/notifications/unread_count**（登入者）：`{ count }`（導覽列鈴鐺用）。
- **POST /api/ncs/notifications/{id}/read**（登入者）：標記已讀。
- **GET /api/ncs/announcements**（登入者）：公告列表。
- **POST /api/ncs/announcements**（僅 ADMIN）：發布公告 `{ title, body }`。
