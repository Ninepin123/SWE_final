# database/ — 資料庫腳本（DBS 子系統）

依需求書 Chapter 10（DBS）規劃，資料庫為 MySQL（NUKSAMS049），所有子系統共用 `nuksams` 一個 database。

## 目錄

| 路徑 | 用途 |
|------|------|
| `schema/00_create_database.sql` | 建 DB 與開發帳號（共用，組長維護） |
| `schema/01_aas_tables.sql` | AAS：使用者、角色、單位、稽核紀錄 |
| `schema/02_sms_tables.sql` | SMS：獎學金、申請條件、分類標籤 |
| `schema/03_sas_tables.sql` | SAS：個人資料、申請案、文件、補件 |
| `schema/04_trs_tables.sql` | TRS：推薦邀請、推薦信 |
| `schema/05_ras_tables.sql` | RAS：審查紀錄、核發名單 |
| `schema/06_ncs_tables.sql` | NCS：通知、公告、留言、問題回報 |
| `seed/99_dev_seed.sql` | 開發用測試資料（依子系統分區塊） |

## 本機初始化

**直接雙擊專案根目錄的 `start.bat` 即可**——它會自動下載可攜版 MySQL（免安裝）、
自動建庫並依編號執行所有腳本，全程不需輸入密碼。

手動執行（備用）：

```bash
mysql -u root -p < schema/00_create_database.sql
mysql -u root -p nuksams < schema/01_aas_tables.sql
mysql -u root -p nuksams < schema/02_sms_tables.sql
mysql -u root -p nuksams < schema/03_sas_tables.sql
mysql -u root -p nuksams < schema/04_trs_tables.sql
mysql -u root -p nuksams < schema/05_ras_tables.sql
mysql -u root -p nuksams < schema/06_ncs_tables.sql
mysql -u root -p nuksams < seed/99_dev_seed.sql
```

（編號即執行順序，後面的檔案可以 FOREIGN KEY 參照前面檔案建立的資料表。）

## 協作規則（重要，避免衝突）

1. **一個子系統一個檔**：只能修改自己負責的 `0X_*.sql`。
2. 需要動到**別人的資料表**（例如想在 `users` 加欄位）→ 在群組提出，由該檔負責人修改。
3. 所有 SQL 都必須**可重複執行**（schema 用 `CREATE TABLE IF NOT EXISTS`、seed 用 `INSERT IGNORE`），因為 `start.bat` 每次啟動都會重跑全部腳本，確保大家的本機資料庫自動保持最新。
4. 改了 schema 請在 PR 描述註明「需要重跑 database 腳本」，並通知群組。
5. 資料表命名：小寫複數 + 底線，例如 `users`、`scholarship_criteria`。
