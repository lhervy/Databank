-- =====================================================================
-- DATABANK · 11 · Live demo script (oral defense, ~3 minutes)
--
-- Before (T-10 min): GitHub > Actions > "A · Card terminals" > Run workflow
--                    (minutes = 20), then run 07_live_demo.sql once.
-- Run each block below with "Run selection" (Ctrl/Cmd + Enter), in order.
-- Every table name is complete (DATABANK.…), so each block also runs on its own.
-- After: 98_pause_all.sql + ALTER COMPUTE POOL SYSTEM_COMPUTE_POOL_CPU STOP ALL;
-- Full speaking script: docs/live_demo.md
-- =====================================================================
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE DATABANK_WH;
USE DATABASE DATABANK;

-- ---------------------------------------------------------------------
-- STEP 1 · Thomas · data is arriving right now (Bronze)
-- ---------------------------------------------------------------------
SELECT COUNT(*)              AS messages_last_5_min,
       MAX(ingested_at)      AS last_message_utc,
       ANY_VALUE(producer_id) AS sent_by
FROM DATABANK.RAW.TPE_AUTHORIZATIONS
WHERE ingested_at > DATEADD(minute, -5, SYSDATE());

-- ---------------------------------------------------------------------
-- STEP 2 · Thomas · the same payments, cleaned, in Gold (seconds later)
-- ---------------------------------------------------------------------
SELECT event_ts, client_id, merchant_name, amount_eur, booking_status,
       DATEDIFF(second, event_ts, SYSDATE()) AS seconds_since_payment
FROM DATABANK.MARTS.FCT_CARD_TRANSACTIONS
ORDER BY event_ts DESC
LIMIT 10;

-- STEP 3 · Adrien · open the dashboard (Projects > Streamlit > Databank):
--          client C000042 > pending payments > "Refresh" > Pipeline health tab

-- ---------------------------------------------------------------------
-- STEP 4 · Lélia · same table, two roles: masked vs clear
-- ---------------------------------------------------------------------
USE SECONDARY ROLES NONE;          -- only the tested role's rights apply

USE ROLE DATABANK_ANALYST;
SELECT client_id, first_name, last_name, iban, birth_date FROM DATABANK.MARTS.DIM_CLIENTS LIMIT 5;   -- masked
SELECT COUNT(*) FROM DATABANK.RAW.TPE_AUTHORIZATIONS;                                    -- denied (expected error)

USE ROLE DATABANK_COMPLIANCE;
SELECT client_id, first_name, last_name, iban, birth_date FROM DATABANK.MARTS.DIM_CLIENTS LIMIT 5;   -- in clear

USE ROLE ACCOUNTADMIN;
USE SECONDARY ROLES ALL;

-- ---------------------------------------------------------------------
-- STEP 5 · a check that fails and blocks bad data
--          For the defense, use ERROR_DEMO.sql (two errors, commented, block by block).
--          The block below is the short version of the same drill.
-- ---------------------------------------------------------------------
INSERT INTO DATABANK.RAW.TPE_AUTHORIZATIONS (record_json, producer_id, batch_id, ingested_at)
SELECT TO_JSON(OBJECT_INSERT(OBJECT_INSERT(TRY_PARSE_JSON(record_json), 'transaction_id', 'DRILL-FUTURE-0001', TRUE),
                             'event_ts', '2030-01-01T12:00:00', TRUE)),
       'drill-future', 'drill-future-batch', SYSDATE()
FROM DATABANK.RAW.TPE_AUTHORIZATIONS
WHERE producer_id = 'v1-migration' AND TRY_PARSE_JSON(record_json):amount::FLOAT > 10
LIMIT 1;
ALTER DYNAMIC TABLE DATABANK.MARTS.FCT_CARD_TRANSACTIONS REFRESH;
-- Expected: fails on assert_transactions_not_in_future, ERROR=1, downstream SKIPPED
EXECUTE DBT PROJECT DATABANK.DBT.DATABANK_DBT ARGS = 'build --select fct_card_transactions+';

-- Recovery (run right after, expected PASS, ERROR=0)
DELETE FROM DATABANK.RAW.TPE_AUTHORIZATIONS WHERE producer_id = 'drill-future';
ALTER DYNAMIC TABLE DATABANK.MARTS.FCT_CARD_TRANSACTIONS REFRESH;
EXECUTE DBT PROJECT DATABANK.DBT.DATABANK_DBT ARGS = 'build --select fct_card_transactions+';
