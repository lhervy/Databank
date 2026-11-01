-- =====================================================================
-- DATABANK · 98 · Pause everything (after each demo - stops credits)
-- Also cancel the "A · Card terminals" workflow run on GitHub if running.
-- =====================================================================
USE ROLE ACCOUNTADMIN;
USE DATABASE DATABANK;

ALTER TASK IF EXISTS DBT.T_00_ROOT SUSPEND;
ALTER TASK IF EXISTS CORE_BANKING.T_SIMULATE_ACTIVITY SUSPEND;
ALTER DYNAMIC TABLE IF EXISTS MARTS.FCT_CARD_TRANSACTIONS SUSPEND;
ALTER DYNAMIC TABLE IF EXISTS MARTS.ACCOUNT_LIVE_BALANCE  SUSPEND;

-- v1 prototype objects, if still present
ALTER TASK IF EXISTS SIM.T_LIVE_FEED SUSPEND;
ALTER TASK IF EXISTS SILVER.T_PROCESS_CARD_EVENTS SUSPEND;
