-- =====================================================================
-- 02_sms_tables.sql
-- 子系統：SMS 獎助學金資料管理 (Scholarship Management)
-- 負責人：（填上負責組員姓名）
-- 本檔包含的資料表：獎學金基本資料（含條件/名額/截止/分類）
-- 規則：只有 SMS 負責人可以修改本檔。
-- 相依：01_aas_tables.sql（units, users）
-- v1：申請條件（GPA/科系）以欄位形式內嵌於 scholarships；
--     scholarship_criteria / categories / tags 等細分資料表後續再拆。
-- =====================================================================
USE nuksams;

CREATE TABLE IF NOT EXISTS scholarships (
    scholarship_id   INT AUTO_INCREMENT PRIMARY KEY,
    unit_id          INT NOT NULL,
    name             VARCHAR(150) NOT NULL,
    year             INT NOT NULL,
    amount           INT NOT NULL DEFAULT 0,
    quota            INT NOT NULL DEFAULT 1,
    min_gpa          DECIMAL(3,2) NULL,                 -- 申請門檻（NUKSAMS006）
    department_limit VARCHAR(100) NULL,                 -- 科系限制（NULL = 不限）
    category         ENUM('SCHOOL','GOVERNMENT','PRIVATE','LOW_INCOME','MERIT','OTHER')
                        NOT NULL DEFAULT 'OTHER',
    description      TEXT,
    deadline         DATETIME NULL,                     -- 截止時間（NUKSAMS007）
    status           ENUM('OPEN','CLOSED') NOT NULL DEFAULT 'OPEN',
    created_by       INT NULL,
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sch_unit    FOREIGN KEY (unit_id)    REFERENCES units(unit_id),
    CONSTRAINT fk_sch_creator FOREIGN KEY (created_by) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
