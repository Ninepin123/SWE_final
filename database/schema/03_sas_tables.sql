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
    status           ENUM('DRAFT','UNDER_REVIEW','NEED_SUPPLEMENT','APPROVED','REJECTED')
                        NOT NULL DEFAULT 'DRAFT',
    -- 申請表欄位（NUKSAMS012）
    statement        TEXT,            -- 申請理由 / 自述
    contact_phone    VARCHAR(30),     -- 聯絡電話
    address          VARCHAR(255),    -- 通訊地址
    household_status TEXT,            -- 家庭狀況
    academic_note    TEXT,            -- 在學成績 / 排名說明
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    submitted_at     DATETIME NULL,
    CONSTRAINT uq_student_scholarship UNIQUE (student_id, scholarship_id),
    CONSTRAINT fk_app_student     FOREIGN KEY (student_id)     REFERENCES users(user_id),
    CONSTRAINT fk_app_scholarship FOREIGN KEY (scholarship_id) REFERENCES scholarships(scholarship_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET @c := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='applications' AND column_name='submitted_at');
SET @s := IF(@c=0, 'ALTER TABLE applications ADD COLUMN submitted_at DATETIME NULL', 'SELECT 1');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
ALTER TABLE applications MODIFY COLUMN status
    ENUM('DRAFT','UNDER_REVIEW','NEED_SUPPLEMENT','APPROVED','REJECTED')
    NOT NULL DEFAULT 'DRAFT';

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
    grade                   VARCHAR(20),
    identity_type           VARCHAR(50),
    contact_email           VARCHAR(100),
    contact_phone           VARCHAR(30),
    address                 VARCHAR(255),
    emergency_contact_name  VARCHAR(100),
    emergency_contact_phone VARCHAR(30),
    updated_at              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_profile_user FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 文字文件替代版（SAS017-SAS020）。
-- content_text 為目前使用欄位；storage_path/mime_type/file_size 預留未來實體附件整合。
CREATE TABLE IF NOT EXISTS application_documents (
    document_id    INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    document_type  ENUM('TRANSCRIPT','AUTOBIOGRAPHY','CERTIFICATE','OTHER') NOT NULL,
    title          VARCHAR(100) NOT NULL,
    content_text   TEXT NOT NULL,
    storage_path   VARCHAR(500) NULL,
    mime_type      VARCHAR(100) NULL,
    file_size      INT NULL,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_application_document_type UNIQUE (application_id, document_type),
    CONSTRAINT fk_document_application FOREIGN KEY (application_id)
        REFERENCES applications(application_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS supplement_requests (
    supplement_id  INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    reviewer_id    INT NOT NULL,
    required_items TEXT NOT NULL,
    deadline       DATETIME NOT NULL,
    status         ENUM('REQUESTED','SUBMITTED') NOT NULL DEFAULT 'REQUESTED',
    response_text  TEXT NULL,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    submitted_at   DATETIME NULL,
    CONSTRAINT fk_supplement_application FOREIGN KEY (application_id)
        REFERENCES applications(application_id) ON DELETE CASCADE,
    CONSTRAINT fk_supplement_reviewer FOREIGN KEY (reviewer_id)
        REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS application_events (
    event_id       INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    actor_id       INT NULL,
    event_type     VARCHAR(50) NOT NULL,
    from_status    VARCHAR(20) NULL,
    to_status      VARCHAR(20) NULL,
    detail         VARCHAR(500) NULL,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_event_application FOREIGN KEY (application_id)
        REFERENCES applications(application_id) ON DELETE CASCADE,
    CONSTRAINT fk_event_actor FOREIGN KEY (actor_id)
        REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET @c := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='student_profiles' AND column_name='grade');
SET @s := IF(@c=0, 'ALTER TABLE student_profiles ADD COLUMN grade VARCHAR(20) NULL', 'SELECT 1');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
SET @c := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='student_profiles' AND column_name='identity_type');
SET @s := IF(@c=0, 'ALTER TABLE student_profiles ADD COLUMN identity_type VARCHAR(50) NULL', 'SELECT 1');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
SET @c := (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='student_profiles' AND column_name='contact_email');
SET @s := IF(@c=0, 'ALTER TABLE student_profiles ADD COLUMN contact_email VARCHAR(100) NULL', 'SELECT 1');
PREPARE st FROM @s; EXECUTE st; DEALLOCATE PREPARE st;
