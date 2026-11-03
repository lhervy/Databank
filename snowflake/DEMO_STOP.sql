-- =====================================================================
-- DEMO STOP · open this file, then Run all: the small arrow next to ▶ → "Run all"
--             (or Ctrl + Shift + Enter)
-- Turns OFF everything that uses credits: schedule, simulator, live
-- tables and the dashboard container. Also cancel the "A · Card terminals"
-- run on GitHub if it is still going.
-- =====================================================================
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE DATABANK_WH;

ALTER TASK DATABANK.DBT.T_00_ROOT SUSPEND;
ALTER TASK DATABANK.CORE_BANKING.T_SIMULATE_ACTIVITY SUSPEND;
ALTER DYNAMIC TABLE DATABANK.MARTS.FCT_CARD_TRANSACTIONS SUSPEND;
ALTER DYNAMIC TABLE DATABANK.MARTS.ACCOUNT_LIVE_BALANCE  SUSPEND;
ALTER COMPUTE POOL SYSTEM_COMPUTE_POOL_CPU STOP ALL;               -- the dashboard container

SELECT 'Everything is OFF - no more credits used' AS status;
