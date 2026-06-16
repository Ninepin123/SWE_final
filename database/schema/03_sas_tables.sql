-- =====================================================================
-- 03_sas_tables.sql
-- 子系統：SAS 學生申請 (Student Application)
-- 負責人：（填上負責組員姓名）
-- 本檔包含的資料表：申請案
-- 規則：只有 SAS 負責人可以修改本檔。
-- 相依：01_aas_tables.sql（users）、02_sms_tables.sql（scholarships）
-- v1：先做申請案本體（含狀態機）；文件上傳 / 補件紀錄資料表後續再補。
-- =====================================================================
USE nuksams;

CREATE TABLE IF NOT EXISTS applications (
    application_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id     INT NOT NULL,
    scholarship_id INT NOT NULL,
    -- 狀態：審核中 / 需補件 / 已通過 / 未通過（NUKSAMS014）
    status         ENUM('UNDER_REVIEW','NEED_SUPPLEMENT','APPROVED','REJECTED')
                      NOT NULL DEFAULT 'UNDER_REVIEW',
    statement      TEXT,                                -- 申請理由/自述（v1 以文字代替文件）
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_student_scholarship UNIQUE (student_id, scholarship_id),
    CONSTRAINT fk_app_student     FOREIGN KEY (student_id)     REFERENCES users(user_id),
    CONSTRAINT fk_app_scholarship FOREIGN KEY (scholarship_id) REFERENCES scholarships(scholarship_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
