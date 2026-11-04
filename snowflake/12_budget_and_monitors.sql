-- =====================================================================
-- DATABANK · 12 · Cost guard rails: resource monitors + account budget
-- Run once as ACCOUNTADMIN (Run all). Safe to run again.
--
-- Two different tools, used together:
--   * Resource monitors watch WAREHOUSES only. They can SUSPEND them.
--   * The budget watches EVERYTHING that uses credits (warehouses, the
--     dashboard container, Snowpipe, serverless tasks...). It sends
--     alerts; it does not stop anything by itself.
-- =====================================================================
USE ROLE ACCOUNTADMIN;

-- 1. Per-warehouse monitor (already existed): 20 credits a month on the project warehouses
CREATE RESOURCE MONITOR IF NOT EXISTS DATABANK_RM
  WITH CREDIT_QUOTA = 20 FREQUENCY = MONTHLY START_TIMESTAMP = IMMEDIATELY
  TRIGGERS ON 75 PERCENT DO NOTIFY
           ON 100 PERCENT DO SUSPEND;
ALTER WAREHOUSE DATABANK_WH        SET RESOURCE_MONITOR = DATABANK_RM;
ALTER WAREHOUSE DATABANK_INGEST_WH SET RESOURCE_MONITOR = DATABANK_RM;
ALTER WAREHOUSE DATABANK_BI_WH     SET RESOURCE_MONITOR = DATABANK_RM;

-- 2. Account-level monitor: a safety net for EVERY warehouse, including ones created later
CREATE RESOURCE MONITOR IF NOT EXISTS DATABANK_ACCOUNT_RM
  WITH CREDIT_QUOTA = 30 FREQUENCY = MONTHLY START_TIMESTAMP = IMMEDIATELY
  TRIGGERS ON 50 PERCENT  DO NOTIFY
           ON 80 PERCENT  DO NOTIFY
           ON 100 PERCENT DO SUSPEND
           ON 110 PERCENT DO SUSPEND_IMMEDIATE;
ALTER ACCOUNT SET RESOURCE_MONITOR = DATABANK_ACCOUNT_RM;

-- 3. Account budget: 30 credits a month across ALL services (alerts when spending is forecast to exceed it)
CALL SNOWFLAKE.LOCAL.ACCOUNT_ROOT_BUDGET!ACTIVATE();
CALL SNOWFLAKE.LOCAL.ACCOUNT_ROOT_BUDGET!SET_SPENDING_LIMIT(30);
-- Email alerts: add your (verified) email in Snowsight > Admin > Cost management > Budgets,
-- or: CALL SNOWFLAKE.LOCAL.ACCOUNT_ROOT_BUDGET!SET_EMAIL_NOTIFICATIONS('<your verified email>');

-- 4. Check
SHOW RESOURCE MONITORS;

-- Check the budget limit (should say 30)
CALL SNOWFLAKE.LOCAL.ACCOUNT_ROOT_BUDGET!GET_SPENDING_LIMIT();
