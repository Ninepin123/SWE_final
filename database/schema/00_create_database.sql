-- =====================================================================
-- 00_create_database.sql
-- 負責人：組長（全體共用，修改前須告知群組）
-- 用途：建立資料庫與開發用帳號。所有人本機第一個執行的腳本。
-- =====================================================================

CREATE DATABASE IF NOT EXISTS nuksams
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- 開發用帳號（本機開發環境使用；正式環境帳密由部署者另行設定）
-- localhost 與 127.0.0.1 都建立，確保 TCP 連線在任何名稱解析設定下都能登入
CREATE USER IF NOT EXISTS 'nuksams_dev'@'localhost' IDENTIFIED BY 'nuksams_dev_password';
CREATE USER IF NOT EXISTS 'nuksams_dev'@'127.0.0.1' IDENTIFIED BY 'nuksams_dev_password';
GRANT ALL PRIVILEGES ON nuksams.* TO 'nuksams_dev'@'localhost';
GRANT ALL PRIVILEGES ON nuksams.* TO 'nuksams_dev'@'127.0.0.1';
FLUSH PRIVILEGES;

USE nuksams;
