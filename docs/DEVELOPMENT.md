# NUKSAMS 開發說明（必讀）

高雄大學獎(助)學金申請與管理系統。需求規格見 [`requirement.md`](../requirement.md)。
本文件說明：環境建置、目錄結構、分工方式、協作規則。**開始寫 code 前請先讀完。**

## 1. 技術棧

| 層 | 技術 | 位置 |
|----|------|------|
| 前端 | Vue 3 + Vite + Vue Router + Pinia + Axios | `frontend/` |
| 後端 | Python FastAPI + SQLAlchemy | `backend/` |
| 資料庫 | MySQL 8（DBS 子系統） | `database/` |

前後端分離：前端只透過 HTTP 呼叫 `/api/...`，後端不產生任何 HTML。

## 2. 啟動系統

### 一鍵啟動（推薦）：雙擊 `start.bat`

前置條件只有兩個（裝一次就好）：**Node.js 20+**、**Python 3.10+**。
**MySQL 不用安裝**——腳本會自動下載官方免安裝版（可攜版）放進專案的 `tools/` 資料夾。

之後每次要測試，**直接雙擊專案根目錄的 `start.bat`**，它會自動：

1. 檢查 Node / Python 是否存在（缺了會給下載連結）
2. 建立後端 venv 並安裝套件（`requirements.txt` 有變動才重裝）
3. 沒有 `backend/.env` 時自動從範本建立
4. 啟動 MySQL——第一次自動下載可攜版（約 230MB，只下載一次）並初始化，
   之後直接啟動在 port 3307；**全程不需要輸入任何密碼**
5. 自動建庫並重跑 `database/` 全部 SQL 腳本，拿到別人最新的資料表
6. 若資料庫沒有任何管理員，建立一個必要的預設 ADMIN 帳號
7. `npm install`（`package.json` 有變動才重裝）
8. 開視窗分別跑後端（:8000）與前端（:5173），並自動打開瀏覽器

前後端都支援熱重載——**改完程式存檔就能直接在瀏覽器測**，不用重啟。
停止系統：關掉「前端」「後端」兩個視窗即可；「MySQL」視窗可以留著，
下次啟動會直接沿用（要關也可以，下次會自動再啟動）。

> 已經自己裝了 MySQL 的人：把 `backend/.env` 的 `DATABASE_URL` 改成你的
> host:port（例如 3306），`start.bat` 偵測到有回應就會直接用你的，不會再下載可攜版。

驗證：瀏覽器開 <http://localhost:5173> 看到首頁、<http://localhost:8000/docs> 看到 Swagger、
`GET http://localhost:8000/api/aas/ping` 回 `{"module":"aas","status":"ok"}` 即成功。

> 因為 SQL 腳本每次啟動都會重跑，所有 schema 都必須可重複執行
> （例如 `CREATE TABLE IF NOT EXISTS`），詳見 `database/README.md`。專案不再提供或自動執行開發假資料 seed。

預設管理員不是 demo/mock 資料，而是系統初始管理入口。預設帳號密碼由 `backend/.env` 控制：
`BOOTSTRAP_ADMIN_ACCOUNT=admin`、`BOOTSTRAP_ADMIN_PASSWORD=ChangeMe!12345`。首次登入後請立即修改密碼，或在第一次啟動前先改 `.env`。

### 手動啟動（備用，macOS/Linux 或腳本出問題時）

macOS/Linux 需自行安裝 MySQL 8（或自行起一個 MySQL，再把 `backend/.env` 指過去）。

```bash
# (1) 取得程式碼
git clone <repo-url>
cd SWE_final

# (2) 初始化資料庫（依序執行，詳見 database/README.md）
mysql -u root -p < database/schema/00_create_database.sql
mysql -u root -p nuksams < database/schema/01_aas_tables.sql
# ...依編號 02~06 全部執行；不需執行 seed

# (3) 後端
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows（macOS/Linux: source .venv/bin/activate）
pip install -r requirements.txt
copy .env.example .env          # 再打開 .env 填本機 MySQL 帳密
python -m app.modules.aas.bootstrap_admin
uvicorn app.main:app --reload   # 跑在 http://localhost:8000

# (4) 前端（另開一個終端機）
cd frontend
npm install
npm run dev                     # 跑在 http://localhost:5173
```

## 3. 目錄結構與「誰負責哪裡」

系統依需求書分成 6 個功能子系統 + 資料庫，**每位組員認領一個子系統**，
只在自己的資料夾內開發，就不會跟別人衝突。

| 代號 | 子系統 | 負責人 | 後端 | 前端 | 資料庫 |
|------|--------|--------|------|------|--------|
| AAS | 帳號與權限管理 |（填）| `backend/app/modules/aas/` | `frontend/src/views/aas/` 等 | `database/schema/01_aas_tables.sql` |
| SMS | 獎助學金資料管理 |（填）| `backend/app/modules/sms/` | `frontend/src/views/sms/` 等 | `database/schema/02_sms_tables.sql` |
| SAS | 學生申請 |（填）| `backend/app/modules/sas/` | `frontend/src/views/sas/` 等 | `database/schema/03_sas_tables.sql` |
| TRS | 教師推薦 |（填）| `backend/app/modules/trs/` | `frontend/src/views/trs/` 等 | `database/schema/04_trs_tables.sql` |
| RAS | 審查與核發 |（填）| `backend/app/modules/ras/` | `frontend/src/views/ras/` 等 | `database/schema/05_ras_tables.sql` |
| NCS | 通知與溝通 |（填）| `backend/app/modules/ncs/` | `frontend/src/views/ncs/` 等 | `database/schema/06_ncs_tables.sql` |
| DBS | 資料庫/共用基礎 | 組長 | `backend/app/core/`、`main.py` | `router/index.js`、`api/http.js` 等共用檔 | `00_create_database.sql` |

每個子系統「自己的檔案」一覽（以 AAS 為例，其他子系統同構）：

```
backend/app/modules/aas/
├── router.py      # API 端點（已寫好 TODO 清單與路徑規劃）
├── service.py     # 商業邏輯、權限檢查
├── models.py      # SQLAlchemy model（對應 database/schema 的資料表）
└── schemas.py     # Pydantic request/response 格式

frontend/src/
├── views/aas/         # 頁面元件（XxxView.vue）
├── router/modules/aas.js   # 自己的路由（index.js 會自動載入）
└── api/aas.js              # 自己的 API 呼叫函式

database/schema/01_aas_tables.sql   # 自己的資料表
```

### 共用檔案（紅線區 ⚠️）

以下檔案**由組長維護**，其他人需要改動時先在群組提出：

- `backend/app/main.py`、`backend/app/core/*`
- `frontend/src/main.js`、`App.vue`、`router/index.js`、`api/http.js`
- `frontend/vite.config.js`、`package.json`、`backend/requirements.txt`
- `database/schema/00_create_database.sql`
- `start.bat`、`scripts/`（一鍵啟動腳本）
- 跨子系統共用元件放 `frontend/src/components/common/`（新增前先在群組講一聲）

### 跨子系統的依賴

- **登入者資訊**：後端用 AAS 提供的 `get_current_user` dependency；前端用 `stores/auth.js`（AAS 維護）。
- **發通知**：SAS/RAS/TRS 狀態異動時呼叫 NCS 提供的 service 函式，不要自己寫 Email 邏輯。
- **別人的資料表**：可以 `import` 別人的 model 來查詢（read），但**不要寫入**別人子系統的資料表——需要寫入就呼叫對方的 service 函式，或在群組提出。

## 4. Git 協作流程

1. `main` 為穩定分支，**禁止直接 push**，一律走 Pull Request。
2. 分支命名：`feature/<子系統>-<功能>`，例如 `feature/aas-login`、`fix/sas-upload-size`。
3. 流程：

   ```bash
   git checkout main && git pull
   git checkout -b feature/aas-login
   # ...開發、commit...
   git push -u origin feature/aas-login
   # 開 PR → 找一位組員 review → 通過後 merge
   ```

4. Commit 訊息格式：`<子系統>: <做了什麼>`，例如 `AAS: 完成登入 API 與 JWT 發放`。
5. **每天開工先 `git pull` 同步 main**，避免分支差距太大。
6. PR 若改了 `database/schema/`，請在描述註明「**需要重跑資料庫腳本**」並通知群組。

## 5. 開發一個功能的標準流程（端到端範例）

以「SMS 新增獎學金」為例：

1. **資料庫**：在 `database/schema/02_sms_tables.sql` 加 `scholarships` 資料表，本機重跑腳本。
2. **後端 model**：在 `backend/app/modules/sms/models.py` 寫對應的 SQLAlchemy model。
3. **後端 schema**：在 `schemas.py` 定義 `ScholarshipCreate`、`ScholarshipOut`。
4. **後端邏輯**：在 `service.py` 寫 `create_scholarship(db, data, current_user)`（含權限檢查）。
5. **後端路由**：在 `router.py` 加 `POST /api/sms/scholarships`，呼叫 service。
6. **更新契約**：把 request/response 格式寫進 `docs/API.md` 的 SMS 章節。
7. **前端 API**：在 `frontend/src/api/sms.js` 加 `createScholarship(data)`。
8. **前端頁面**：在 `frontend/src/views/sms/` 寫 `ScholarshipFormView.vue`。
9. **前端路由**：在 `frontend/src/router/modules/sms.js` 註冊路徑。
10. **測試**：後端在 `backend/tests/` 加 pytest；手動跑過畫面流程。
11. 開 PR。

## 6. 命名與程式風格

| 項目 | 規範 | 範例 |
|------|------|------|
| API 路徑 | `/api/<子系統>/<資源複數>`，kebab-case | `/api/ras/supplement-requests` |
| Python | snake_case；遵循 PEP 8 | `get_scholarship_list()` |
| Vue 元件 | PascalCase，頁面以 `View` 結尾 | `LoginView.vue`、`ScholarshipCard.vue` |
| JS 函式/變數 | camelCase | `fetchApplications()` |
| 資料表 | 小寫複數 + 底線 | `scholarship_criteria` |
| 路由 name | `<子系統>-<頁面>` | `sas-application-list` |

其他約定：

- 前端呼叫 API 一律經過 `src/api/<子系統>.js` + 共用 `http.js`，元件內不直接用 axios。
- 後端權限檢查寫在 service 層；老師只能看自己案件（NUKSAMS004）、單位資料隔離（NUKSAMS010）這類規則**不能只靠前端隱藏按鈕**。
- 密碼必須雜湊儲存（passlib/bcrypt），禁止明碼。
- 機密設定只放 `backend/.env`（不入版控），範本維護在 `.env.example`。

## 7. 常見問題

- **前端打 API 出現 404/CORS**：確認後端有跑在 8000 port；前端要用相對路徑 `/api/...`（由 Vite proxy 轉發），不要寫 `http://localhost:8000/...`。
- **後端起不來說連不上 DB**：確認「NUKSAMS MySQL」視窗還開著；被關掉的話重跑 `start.bat` 會自動再啟動。
- **MySQL 視窗一閃就關 / 啟動逾時**：多半是缺少 VC++ 執行環境，安裝後重試：<https://aka.ms/vs/17/release/vc_redist.x64.exe>。
- **想換回自己裝的 MySQL**：改 `backend/.env` 的 `DATABASE_URL` 指向你的 host:port，`start.bat` 會直接沿用。
- **npm install / pip install 失敗**：確認 Node 20+、Python 3.10+；Python 套件裝在 `.venv` 虛擬環境內。
- **改了別人也在改的檔案**：理論上不會發生（見第 3 節分工）；若真的需要，先在群組講。
