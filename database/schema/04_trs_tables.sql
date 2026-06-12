-- =====================================================================
-- 04_trs_tables.sql
-- 子系統：TRS 教師推薦 (Teacher Recommendation)
-- 負責人：（填上負責組員姓名）
-- 本檔包含的資料表：推薦邀請、推薦信（含草稿）
-- 規則：只有 TRS 負責人可以修改本檔。
-- 相依：01_aas_tables.sql（users）、03_sas_tables.sql（applications）
-- =====================================================================
USE nuksams;

-- TODO(TRS): 依需求書 7.2 節設計資料表，預計包含：
--   recommendation_requests  推薦邀請（老師只能看到自己負責的案件, NUKSAMS004）
--   recommendation_letters   推薦信內容與草稿（status: DRAFT/SUBMITTED, 7.2.4）
--   （推薦信內容僅老師與審查人員可見，學生只能看到是否提交, 7.2.5 —
--    權限控制在 service 層實作，資料表需保留 visibility 所需欄位）
