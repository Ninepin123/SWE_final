# NUKSAMS — 高雄大學獎(助)學金申請與管理系統

軟體工程期末專案（第 2 組）。讓學生、教師、獎助單位、審查人員與系統管理員在線上完成獎助學金的申請、推薦、審查、通知與管理。

- 📄 需求規格書：[`requirement.md`](requirement.md)
- 🛠 **開發說明（組員必讀）：[`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)**
- 🔌 API 介面契約：[`docs/API.md`](docs/API.md)

## 快速開始

裝好 **Node.js 20+ / Python 3.10+** 後（MySQL 不用裝），**雙擊 `start.bat`** 即可一鍵啟動：
自動下載可攜版 MySQL、裝套件、建資料庫、開前後端、開瀏覽器，全程免輸入密碼。
寫完 code 存檔即熱重載，直接測試。詳見 [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)。

## 技術棧

| 層 | 技術 |
|----|------|
| 前端 | Vue 3 + Vite + Vue Router + Pinia |
| 後端 | Python FastAPI + SQLAlchemy |
| 資料庫 | MySQL 8 |

## 專案結構

```
SWE_final/
├── frontend/                  # 前端 Vue 3（npm run dev → :5173）
│   └── src/
│       ├── api/               # 各子系統 API 呼叫（aas.js, sms.js, ...）
│       ├── router/modules/    # 各子系統路由（自動合併）
│       ├── views/<子系統>/     # 各子系統頁面
│       ├── components/common/ # 共用元件
│       └── stores/            # Pinia（auth 由 AAS 維護）
├── backend/                   # 後端 FastAPI（uvicorn → :8000，/docs 看 API）
│   └── app/
│       ├── core/              # 設定、DB 連線（共用，組長維護）
│       └── modules/<子系統>/   # router / service / models / schemas
├── database/                  # MySQL 腳本（schema 依子系統分檔）
├── docs/                      # 開發說明與 API 契約
└── requirement.md             # 需求規格書
```

## 子系統分工

| 代號 | 子系統 | 範圍 |
|------|--------|------|
| AAS | 帳號與權限管理 | 登入、帳號 CRUD、角色權限、稽核紀錄 |
| SMS | 獎助學金資料管理 | 獎學金資料、申請條件、名額/截止、分類標籤 |
| SAS | 學生申請 | 個人資料、查詢篩選、線上申請、文件上傳、補件 |
| TRS | 教師推薦 | 推薦案件、推薦信撰寫/草稿、進度查詢 |
| RAS | 審查與核發 | 案件審查、自動排序、補件要求、核發名單、統計 |
| NCS | 通知與溝通 | 站內/Email 通知、公告、留言板、問題回報 |
| DBS | 資料庫 | MySQL schema 與共用基礎設施 |

詳細的環境建置、Git 流程、命名規範與開發範例請看 [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)。

## TRS 教師推薦

- 教師僅能看到自己負責的推薦案件列表。
- 支援推薦信草稿儲存與正式提交。
- 提交後鎖定，不可再修改推薦內容。
- 教師可查看自己案件的學生完整申請資料。
- 列表支援搜尋、篩選、排序與 dashboard 統計（待處理/草稿/已提交/即將截止/已逾期）。
- 學生端僅可查看推薦狀態，不會回傳推薦信內容。
- Reviewer 端僅可查看 `SUBMITTED` 推薦信內容，未提交案件只顯示狀態。
- 提交推薦信與即將截止（48 小時）會建立站內通知（NCS）。
- TRS 重要操作會寫入既有 `audit_logs`（不記錄推薦信全文）。
