-- =====================================================================
-- 03_sas_tables.sql
-- 子系統：SAS 學生申請 (Student Application)
-- 本檔資料表：申請案(applications)、學生個人資料(student_profiles)
-- 相依：01_aas_tables.sql（users）、02_sms_tables.sql（scholarships）
-- =====================================================================
USE nuksams;

CREATE TABLE IF NOT EXISTS applications (
    application_id   INT AUTO_INCREMENT PRIMARY KEY,
    student_id       INT NOT NULL,
    scholarship_id   INT NOT NULL,
    status           ENUM('UNDER_REVIEW','NEED_SUPPLEMENT','APPROVED','REJECTED')
                        NOT NULL DEFAULT 'UNDER_REVIEW',
    -- 申請表欄位（NUKSAMS012）
    statement        TEXT,            -- 申請理由 / 自述
    contact_phone    VARCHAR(30),     -- 聯絡電話
    address          VARCHAR(255),    -- 通訊地址
    household_status TEXT,            -- 家庭狀況
    academic_note    TEXT,            -- 在學成績 / 排名說明
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_student_scholarship UNIQUE (student_id, scholarship_id),
    CONSTRAINT fk_app_student     FOREIGN KEY (student_id)     REFERENCES users(user_id),
    CONSTRAINT fk_app_scholarship FOREIGN KEY (scholarship_id) REFERENCES scholarships(scholarship_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 相容舊版(v1)資料表：若缺少新欄位則補上（MySQL 8 沒有 ADD COLUMN IF NOT EXISTS，
-- 改用 information_schema 判斷 + PREPARE，全部為頂層語句，可被資料庫載入腳本逐句執行）。
SET @c := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='applications' AND column_name='contact_phone');
SET @s := IF(@c=0, 'ALTER TABLE applications ADD COLUMN contact_phone VARCHAR(30) NULL', 'SELECT 1');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
SET @c := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='applications' AND column_name='address');
SET @s := IF(@c=0, 'ALTER TABLE applications ADD COLUMN address VARCHAR(255) NULL', 'SELECT 1');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
SET @c := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='applications' AND column_name='household_status');
SET @s := IF(@c=0, 'ALTER TABLE applications ADD COLUMN household_status TEXT NULL', 'SELECT 1');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
SET @c := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='applications' AND column_name='academic_note');
SET @s := IF(@c=0, 'ALTER TABLE applications ADD COLUMN academic_note TEXT NULL', 'SELECT 1');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;

-- 學生個人資料（6.2.1：學號等核心欄位不可由學生修改，這裡僅放可編輯欄位；身分資料讀 users）
CREATE TABLE IF NOT EXISTS student_profiles (
    user_id                 INT PRIMARY KEY,
    contact_phone           VARCHAR(30),
    address                 VARCHAR(255),
    emergency_contact_name  VARCHAR(100),
    emergency_contact_phone VARCHAR(30),
    updated_at              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_profile_user FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
