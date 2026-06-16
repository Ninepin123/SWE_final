-- =====================================================================
-- 01_aas_tables.sql
-- 子系統：AAS 帳號與權限管理 (Account and Authority Management)
-- 負責人：（填上負責組員姓名）
-- 本檔包含的資料表：單位、使用者
-- 規則：只有 AAS 負責人可以修改本檔；其他子系統需要 user/unit 欄位異動時，
--       請在群組提出，由 AAS 負責人修改。
-- v1：先建立登入/權限所需的最小資料表（units, users）。
--     audit_logs（4.2.5）尚未實作，後續版本再補。
-- =====================================================================
USE nuksams;

-- 單位（獎助單位 / 審查單位），供單位資料隔離使用（NUKSAMS010）
CREATE TABLE IF NOT EXISTS units (
    unit_id       INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL UNIQUE,
    type          ENUM('SCHOOL','GOVERNMENT','PRIVATE','OTHER') NOT NULL DEFAULT 'OTHER',
    contact_email VARCHAR(100),
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 使用者帳號（學生 / 老師 / 獎助單位 / 審查人員 / 管理員）
CREATE TABLE IF NOT EXISTS users (
    user_id     INT AUTO_INCREMENT PRIMARY KEY,
    account     VARCHAR(50)  NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,                 -- bcrypt 雜湊，禁止明碼
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(100),
    role        ENUM('STUDENT','TEACHER','SPONSOR','REVIEWER','ADMIN') NOT NULL,
    unit_id     INT NULL,
    gpa         DECIMAL(3,2) NULL,                     -- v1 簡化：學生 GPA 暫存於此
    department  VARCHAR(100) NULL,
    status      ENUM('ACTIVE','DISABLED') NOT NULL DEFAULT 'ACTIVE',
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_unit FOREIGN KEY (unit_id) REFERENCES units(unit_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
