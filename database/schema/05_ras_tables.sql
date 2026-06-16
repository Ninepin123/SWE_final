-- =====================================================================
-- 05_ras_tables.sql
-- 子系統：RAS 審查與核發 (Review and Award)
-- 負責人：（填上負責組員姓名）
-- 本檔包含的資料表：審查紀錄
-- 規則：只有 RAS 負責人可以修改本檔。
-- 相依：01_aas_tables.sql（users）、03_sas_tables.sql（applications）
-- v1：先做審查紀錄（reviews）；核發名單 awards / 補件要求資料表後續再補。
--     申請案最終狀態存於 SAS 的 applications.status（由 RAS 透過 SAS 介面更新）。
-- =====================================================================
USE nuksams;

CREATE TABLE IF NOT EXISTS reviews (
    review_id      INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    reviewer_id    INT NOT NULL,
    result         ENUM('APPROVED','REJECTED','NEED_SUPPLEMENT') NOT NULL,
    comment        TEXT,
    reviewed_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_review_app      FOREIGN KEY (application_id) REFERENCES applications(application_id),
    CONSTRAINT fk_review_reviewer FOREIGN KEY (reviewer_id)    REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
