-- =====================================================================
-- DEMO START · open this file, then Run all: the small arrow next to ▶ → "Run all"
--              (or Ctrl + Shift + Enter)
-- Turns ON the live parts of the pipeline (they are paused between demos
-- to save free credits). Run it about 10 minutes before the demo,
-- after starting "A · Card terminals" on GitHub.
-- =====================================================================
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE DATABANK_WH;

ALTER DYNAMIC TABLE DATABANK.MARTS.FCT_CARD_TRANSACTIONS RESUME;   -- card payments, refreshed every minute
ALTER DYNAMIC TABLE DATABANK.MARTS.ACCOUNT_LIVE_BALANCE  RESUME;   -- live balances, refreshed every minute
-- the 15-minute pipeline (3 steps): pause it first, so this file also works when it is already on,
-- then switch on the 3 steps together
ALTER TASK DATABANK.DBT.T_00_ROOT SUSPEND;
SELECT SYSTEM$TASK_DEPENDENTS_ENABLE('DATABANK.DBT.T_00_ROOT');
ALTER TASK DATABANK.CORE_BANKING.T_SIMULATE_ACTIVITY RESUME;       -- core banking simulator

SELECT 'Live parts are ON - the demo is ready' AS status;
