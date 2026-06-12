-- =====================================================================
-- 06_ncs_tables.sql
-- 子系統：NCS 通知與溝通 (Notification and Communication)
-- 負責人：（填上負責組員姓名）
-- 本檔包含的資料表：通知、公告、留言、問題回報
-- 規則：只有 NCS 負責人可以修改本檔。
-- 相依：01_aas_tables.sql（users）
-- =====================================================================
USE nuksams;

-- TODO(NCS): 依需求書 9.2 節設計資料表，預計包含：
--   notifications    站內通知與 Email 發送紀錄（含失敗重送紀錄, NUKSAMS036）
--   announcements    全域公告（NUKSAMS020）
--   messages         留言板（學生與審查者互動, NUKSAMS018）
--   issue_reports    問題回報（NUKSAMS021）
