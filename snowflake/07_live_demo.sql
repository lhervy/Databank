-- =====================================================================
-- DATABANK · 07 · Start everything for a live demo (~10 min before)
--
--   1. GitHub > Actions > "A · Card terminals" > Run workflow (20 min)
--   2. Run this file: resumes the DAG, the core banking simulator and
--      the dynamic tables.
--   3. Afterwards: 98_pause_all.sql  (stops credit consumption)
-- =====================================================================
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE DATABANK_WH;
USE DATABASE DATABANK;

ALTER DYNAMIC TABLE MARTS.FCT_CARD_TRANSACTIONS RESUME;
ALTER DYNAMIC TABLE MARTS.ACCOUNT_LIVE_BALANCE  RESUME;

ALTER TASK DBT.T_20_DBT_FRESHNESS RESUME;
ALTER TASK DBT.T_10_DBT_BUILD     RESUME;
ALTER TASK DBT.T_00_ROOT          RESUME;
ALTER TASK CORE_BANKING.T_SIMULATE_ACTIVITY RESUME;

-- Watch it move (re-run every minute) -------------------------------
-- A: messages arriving
SELECT COUNT(*) AS messages_last_5_min, MAX(ingested_at) AS last_message_utc
FROM RAW.TPE_AUTHORIZATIONS WHERE ingested_at > DATEADD(minute, -5, SYSDATE());

-- Gold: latest payments and their end-to-end latency
SELECT event_ts, client_id, merchant_name, amount_eur, booking_status,
       DATEDIFF(second, event_ts, SYSDATE()) AS seconds_since_payment
FROM MARTS.FCT_CARD_TRANSACTIONS ORDER BY event_ts DESC LIMIT 10;

-- Dynamic table refreshes
SELECT name, state, refresh_action, refresh_start_time, refresh_end_time
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
ORDER BY refresh_start_time DESC LIMIT 10;
