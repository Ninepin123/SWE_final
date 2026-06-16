-- =====================================================================
-- 01_aas_tables.sql
-- 子系統：AAS 帳號與權限管理 (Account and Authority Management)
-- 本檔資料表：單位、使用者、稽核紀錄(audit_logs)
-- 相依：無
-- =====================================================================
USE nuksams;

CREATE TABLE IF NOT EXISTS units (
    unit_id       INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL UNIQUE,
    type          ENUM('SCHOOL','GOVERNMENT','PRIVATE','OTHER') NOT NULL DEFAULT 'OTHER',
    contact_email VARCHAR(100),
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS users (
    user_id     INT AUTO_INCREMENT PRIMARY KEY,
    account     VARCHAR(50)  NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(100),
    role        ENUM('STUDENT','TEACHER','SPONSOR','REVIEWER','ADMIN') NOT NULL,
    unit_id     INT NULL,
    gpa         DECIMAL(3,2) NULL,
    department  VARCHAR(100) NULL,
    status      ENUM('ACTIVE','DISABLED') NOT NULL DEFAULT 'ACTIVE',
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_unit FOREIGN KEY (unit_id) REFERENCES units(unit_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 稽核紀錄（4.2.5 / NUKSAMS038）：記錄管理與審查等重要操作
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id      INT AUTO_INCREMENT PRIMARY KEY,
    actor_id    INT NULL,
    action      VARCHAR(100) NOT NULL,
    target_type VARCHAR(50)  NULL,
    target_id   INT NULL,
    detail      VARCHAR(500) NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_actor FOREIGN KEY (actor_id) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
