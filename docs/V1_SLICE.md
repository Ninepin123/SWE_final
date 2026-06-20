# NUKSAMS v1 初版（核心流程）說明

這份 v1 把系統最核心的一條流程打通成可實際操作的版本，給團隊一個能跑的基礎，
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
3. 瀏覽器開 <http://localhost:5173>，使用正式建立的帳號登入。

> 後端 API 文件：<http://localhost:8000/docs>

### 帳號來源

系統不再提供種子帳號或假資料，但會在沒有任何 `ADMIN` 時建立必要的 bootstrap 管理員。預設帳號為 `admin`，密碼由 `BOOTSTRAP_ADMIN_PASSWORD` 設定控制。其餘使用者、單位與獎學金資料請由正式管理流程建立。

## 流程驗證腳本

1. 用正式獎助單位帳號登入 → 獎學金管理 → 新增一筆獎學金。
2. 用正式學生帳號登入 → 申請獎學金 → 送出 → 我的申請進度顯示「審核中」。
3. 用正式審查人員帳號登入 → 審查申請案 → 做出審查決定。
4. 回到學生帳號的「我的申請進度」確認結果。

## 這版改了哪些檔案

- 後端：`backend/app/modules/{aas,sms,sas,ras}/` 的 `models/schemas/service/router.py`，
  新增 `aas/security.py`（JWT/權限）。
- 資料庫：`database/schema/{01_aas,02_sms,03_sas,05_ras}_tables.sql` 補上實際資料表。
- 前端：`stores/auth.js`、`api/{aas,sms,sas,ras}.js`、`router/modules/{aas,sms,sas,ras}.js`、
  `views/{aas,sms,sas,ras}/*.vue`、`views/common/HomeView.vue`。
- **未更動**組長維護的紅線檔（`main.py`、`core/*`、`router/index.js`、`api/http.js`、
  `package.json`、`requirements.txt`、`start.bat`、`scripts/*`、`00_create_database.sql`）。

> 路由守衛：目前各頁面在載入時自行檢查登入/角色。若要做「全域未登入導向 /login」，
> 需動到 `router/index.js`（紅線檔），建議由組長加上。
