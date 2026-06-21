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
    department_limit TEXT NULL,                         -- 科系限制（NULL = 不限；以 JSON 陣列儲存科系名稱）
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

-- 相容舊版(v1)資料表：新增申請條件、標籤、文件等欄位
-- 科系限制原為 VARCHAR(100)，改用 JSON 陣列（可複選科系）後可能超過 100 字，放寬為 TEXT。
SET @c := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='scholarships' AND column_name='department_limit' AND data_type='varchar');
SET @s := IF(@c=1, 'ALTER TABLE scholarships MODIFY COLUMN department_limit TEXT NULL', 'SELECT 1');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
SET @c := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='scholarships' AND column_name='grade_limit');
SET @s := IF(@c=0, 'ALTER TABLE scholarships ADD COLUMN grade_limit TEXT NULL', 'SELECT 1');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
SET @c := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='scholarships' AND column_name='identity_limit');
SET @s := IF(@c=0, 'ALTER TABLE scholarships ADD COLUMN identity_limit TEXT NULL', 'SELECT 1');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
SET @c := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='scholarships' AND column_name='family_status_limit');
SET @s := IF(@c=0, 'ALTER TABLE scholarships ADD COLUMN family_status_limit TEXT NULL', 'SELECT 1');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
SET @c := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='scholarships' AND column_name='require_recommendation');
SET @s := IF(@c=0, 'ALTER TABLE scholarships ADD COLUMN require_recommendation TINYINT(1) NOT NULL DEFAULT 0', 'SELECT 1');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
SET @c := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='scholarships' AND column_name='required_docs');
SET @s := IF(@c=0, 'ALTER TABLE scholarships ADD COLUMN required_docs TEXT NULL', 'SELECT 1');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
SET @c := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='scholarships' AND column_name='tags');
SET @s := IF(@c=0, 'ALTER TABLE scholarships ADD COLUMN tags TEXT NULL', 'SELECT 1');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
SET @c := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='scholarships' AND column_name='criteria_note');
SET @s := IF(@c=0, 'ALTER TABLE scholarships ADD COLUMN criteria_note TEXT NULL', 'SELECT 1');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
SET @c := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='scholarships' AND column_name='start_date');
SET @s := IF(@c=0, 'ALTER TABLE scholarships ADD COLUMN start_date DATETIME NULL', 'SELECT 1');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;

-- 新增聯絡資訊欄位
SET @c := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='scholarships' AND column_name='contact_name');
SET @s := IF(@c=0, 'ALTER TABLE scholarships ADD COLUMN contact_name VARCHAR(100) NULL', 'SELECT 1');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
SET @c := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='scholarships' AND column_name='contact_phone');
SET @s := IF(@c=0, 'ALTER TABLE scholarships ADD COLUMN contact_phone VARCHAR(50) NULL', 'SELECT 1');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
SET @c := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='scholarships' AND column_name='contact_email');
SET @s := IF(@c=0, 'ALTER TABLE scholarships ADD COLUMN contact_email VARCHAR(100) NULL', 'SELECT 1');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
SET @c := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='scholarships' AND column_name='contact_address');
SET @s := IF(@c=0, 'ALTER TABLE scholarships ADD COLUMN contact_address VARCHAR(255) NULL', 'SELECT 1');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
SET @c := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='scholarships' AND column_name='website');
SET @s := IF(@c=0, 'ALTER TABLE scholarships ADD COLUMN website VARCHAR(255) NULL', 'SELECT 1');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;

-- 動態分類與標籤選項表
ALTER TABLE scholarships MODIFY COLUMN category VARCHAR(50) NOT NULL DEFAULT 'OTHER';

CREATE TABLE IF NOT EXISTS scholarship_options (
    option_id INT AUTO_INCREMENT PRIMARY KEY,
    type ENUM('CATEGORY', 'TAG') NOT NULL,
    name VARCHAR(50) NOT NULL,
    UNIQUE KEY uq_type_name (type, name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
