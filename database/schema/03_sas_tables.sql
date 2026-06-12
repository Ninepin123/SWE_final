-- =====================================================================
-- 03_sas_tables.sql
-- 子系統：SAS 學生申請 (Student Application)
-- 負責人：（填上負責組員姓名）
-- 本檔包含的資料表：學生個人資料、申請案、上傳文件、補件紀錄
-- 規則：只有 SAS 負責人可以修改本檔。
-- 相依：01_aas_tables.sql（users）、02_sms_tables.sql（scholarships）
-- =====================================================================
USE nuksams;

-- TODO(SAS): 依需求書 6.2 節設計資料表，預計包含：
--   student_profiles     學生個人資料（學號等核心欄位不可由學生修改, 6.2.1）
--   applications         申請案（狀態：審核中/需補件/已通過/未通過, NUKSAMS014）
--   application_documents 上傳文件（限制格式與大小, 6.2.4）
--   supplements          補件紀錄（補件期限與通知, NUKSAMS017）
--   （申請截止後鎖定 NUKSAMS008 以 status / 截止時間判斷實作）
