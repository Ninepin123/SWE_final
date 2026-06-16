# NUKSAMS v1 初版（核心流程）說明

這份 v1 把系統最核心的一條流程打通成可實際操作的版本，給團隊一個能跑、能 demo 的基礎，
其餘子系統與細項功能在這條主軸上往外長即可。

## 這版做了什麼（端到端流程）

> 獎助單位張貼獎學金 → 學生線上申請 → 審查人員通過/不通過/要求補件 → 學生看到結果
> 全程需先登入，並依角色限制可用功能。

涵蓋四個子系統的最小可用功能：

- **AAS 帳號與權限**：JWT 登入 / 登出 / 查目前登入者；管理員可查詢與新增帳號；
  提供 `get_current_user`、`require_roles()` 給其他子系統共用（依需求書 4.2 規劃）。
- **SMS 獎助學金**：獎學金列表 / 查詢（所有登入者）；獎助單位、管理員可新增獎學金
  （含金額、名額、最低 GPA、截止時間、分類）。
- **SAS 學生申請**：學生瀏覽「開放中」獎學金、線上申請（含截止/GPA/重複申請檢查）、查看自己的申請進度。
- **RAS 審查與核發**：審查人員查看申請案（依 GPA 自動排序）、做出通過/不通過/補件決定，
  並透過 SAS 介面回寫申請案狀態。

## 這版「還沒做」（後續版本）

- **TRS 教師推薦**、**NCS 通知與溝通**：保留骨架，尚未實作。
- 文件上傳、補件流程、核發名單(awards)、年度統計報表、稽核紀錄(audit log)、
  單位資料隔離的完整權限、分頁，以及學生個人資料(SAS profile)的獨立資料表。
- 為求精簡，學生 GPA 暫存於 `users` 表、申請條件以欄位內嵌於 `scholarships`；
  日後要拆成獨立資料表時再調整。

## 怎麼跑起來

1. 裝好 **Node.js 20+ / Python 3.10+**（MySQL 不用裝）。
2. **雙擊 `start.bat`**：會自動裝套件、建資料庫與資料表、開前後端、開瀏覽器。
3. **第一次**請建立示範帳號與資料（資料表建立後執行一次即可）：
   在 `backend/` 目錄、venv 啟用後執行——
   - Windows：`.venv\Scripts\python -m app.modules.aas.dev_seed`
   - macOS/Linux：`python -m app.modules.aas.dev_seed`
4. 瀏覽器開 <http://localhost:5173>，用下列示範帳號登入（密碼皆為 `password123`）。

> 後端 API 文件：<http://localhost:8000/docs>

### 示範帳號

| 帳號 | 角色 | 用途 |
|------|------|------|
| `admin` | 管理員 | 帳號管理 |
| `sponsor` | 獎助單位 | 新增/管理獎學金 |
| `reviewer` | 審查人員 | 審查申請案 |
| `teacher` | 老師 | （TRS 尚未實作） |
| `A1125529` | 學生（GPA 3.85）| 申請、查看進度 |
| `A1125599` | 學生（GPA 3.20）| 申請、查看進度 |

## 三分鐘 Demo 腳本

1. 用 `sponsor` 登入 → 獎學金管理 → 新增一筆獎學金（設個最低 GPA，例如 3.5）。
2. 用 `A1125529`（GPA 3.85）登入 → 申請獎學金 → 送出 → 我的申請進度顯示「審核中」。
3.（可選）用 `A1125599`（GPA 3.20）登入申請同一筆，會被擋下（GPA 未達門檻）。
4. 用 `reviewer` 登入 → 審查申請案（依 GPA 排序）→ 對 A1125529 按「通過」。
5. 回到 `A1125529` 的「我的申請進度」→ 狀態變成「已通過」。

## 這版改了哪些檔案

- 後端：`backend/app/modules/{aas,sms,sas,ras}/` 的 `models/schemas/service/router.py`，
  新增 `aas/security.py`（JWT/權限）與 `aas/dev_seed.py`（示範資料）。
- 資料庫：`database/schema/{01_aas,02_sms,03_sas,05_ras}_tables.sql` 補上實際資料表。
- 前端：`stores/auth.js`、`api/{aas,sms,sas,ras}.js`、`router/modules/{aas,sms,sas,ras}.js`、
  `views/{aas,sms,sas,ras}/*.vue`、`views/common/HomeView.vue`。
- **未更動**組長維護的紅線檔（`main.py`、`core/*`、`router/index.js`、`api/http.js`、
  `package.json`、`requirements.txt`、`start.bat`、`scripts/*`、`00_create_database.sql`）。

> 路由守衛：目前各頁面在載入時自行檢查登入/角色。若要做「全域未登入導向 /login」，
> 需動到 `router/index.js`（紅線檔），建議由組長加上。
