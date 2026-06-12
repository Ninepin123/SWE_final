-- =====================================================================
-- 02_sms_tables.sql
-- 子系統：SMS 獎助學金資料管理 (Scholarship Management)
-- 負責人：（填上負責組員姓名）
-- 本檔包含的資料表：獎學金基本資料、申請條件、分類與標籤
-- 規則：只有 SMS 負責人可以修改本檔。
-- 相依：01_aas_tables.sql（units 由 AAS 定義）
-- =====================================================================
USE nuksams;

-- TODO(SMS): 依需求書 5.2 節設計資料表，預計包含：
--   scholarships             獎學金基本資料（名稱/年度/金額/聯絡方式, NUKSAMS005）
--   scholarship_criteria     申請條件（GPA/科系/家庭狀況, NUKSAMS006）
--   scholarship_categories   分類（校內/政府/私人贊助..., NUKSAMS022）
--   scholarship_tags         標籤（NUKSAMS023）
--   （截止日期與名額欄位請放在 scholarships，供自動關閉申請使用, NUKSAMS007）
