-- =====================================================================
-- 01_aas_tables.sql
-- 子系統：AAS 帳號與權限管理 (Account and Authority Management)
-- 負責人：（填上負責組員姓名）
-- 本檔包含的資料表：使用者、角色權限、單位、稽核紀錄
-- 規則：只有 AAS 負責人可以修改本檔；其他子系統需要 user 欄位異動時，
--       請在群組提出，由 AAS 負責人修改。
-- =====================================================================
USE nuksams;

-- TODO(AAS): 依需求書 4.2 節設計資料表，預計包含：
--   users          使用者帳號（學生/老師/獎助單位/審查人員/管理員）
--   roles          角色定義
--   units          單位資料（單位資料隔離用, NUKSAMS010）
--   audit_logs     管理操作紀錄（NUKSAMS038, 4.2.5）

-- 範例格式（實作時請替換）：
-- CREATE TABLE IF NOT EXISTS users (
--     user_id     INT AUTO_INCREMENT PRIMARY KEY,
--     account     VARCHAR(50)  NOT NULL UNIQUE,
--     password    VARCHAR(255) NOT NULL,          -- 雜湊後儲存，禁止明碼
--     name        VARCHAR(100) NOT NULL,
--     email       VARCHAR(100),
--     role        ENUM('STUDENT','TEACHER','SPONSOR','REVIEWER','ADMIN') NOT NULL,
--     unit_id     INT NULL,
--     status      ENUM('ACTIVE','DISABLED') NOT NULL DEFAULT 'ACTIVE',
--     created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
