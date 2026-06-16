-- =====================================================================
-- 04_trs_tables.sql
-- 子系統：TRS 教師推薦 (Teacher Recommendation)
-- 本檔資料表：推薦案（邀請 + 推薦信草稿/內容）
-- 相依：01_aas_tables.sql（users）、03_sas_tables.sql（applications）
-- 隱私（7.2.5）：推薦信內容僅老師與審查人員可見，學生只看得到狀態。
-- =====================================================================
USE nuksams;

CREATE TABLE IF NOT EXISTS recommendations (
    rec_id         INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    student_id     INT NOT NULL,
    teacher_id     INT NOT NULL,
    content        TEXT,
    -- REQUESTED：學生已邀請、老師尚未動筆；DRAFT：老師存草稿；SUBMITTED：已送出
    status         ENUM('REQUESTED','DRAFT','SUBMITTED') NOT NULL DEFAULT 'REQUESTED',
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_app_teacher UNIQUE (application_id, teacher_id),
    CONSTRAINT fk_rec_app     FOREIGN KEY (application_id) REFERENCES applications(application_id),
    CONSTRAINT fk_rec_student FOREIGN KEY (student_id)     REFERENCES users(user_id),
    CONSTRAINT fk_rec_teacher FOREIGN KEY (teacher_id)     REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
