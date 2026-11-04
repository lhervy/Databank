-- =====================================================================
-- DATABANK · Live error demo (slide 9 · Reliability, about 2 minutes)
--
-- Two prepared errors, shown live:
--   ERROR 1 · a broken message      -> handled automatically (quarantine)
--   ERROR 2 · an impossible date    -> a check fails and blocks the bad data,
--                                      then we fix it and re-run
--
-- HOW TO RUN: put the cursor in a block and press Ctrl+Enter (one statement)
-- or select the block and press Ctrl+Enter. Do NOT use "Run all": the
-- dbt run in 2b is EXPECTED to fail, and Run all would stop there.
-- Everything uses producer_id 'error-demo', so the clean-up is exact.
-- =====================================================================
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE DATABANK_WH;

-- ---------------------------------------------------------------------
-- 0 · BEFORE: the data is clean
-- ---------------------------------------------------------------------
SELECT COUNT(*) AS payments_in_the_future            -- expected: 0
FROM DATABANK.MARTS.FCT_CARD_TRANSACTIONS
WHERE event_ts > DATEADD(minute, 5, SYSDATE());

-- =====================================================================
-- ERROR 1 · A broken message: the amount is "abc" instead of a number
--           Handled automatically, nobody has to do anything.
-- =====================================================================
-- 1a · a card terminal sends a broken message (copy of a real one, amount = "abc")
INSERT INTO DATABANK.RAW.TPE_AUTHORIZATIONS (record_json, producer_id, batch_id, ingested_at)
SELECT TO_JSON(OBJECT_INSERT(OBJECT_INSERT(TRY_PARSE_JSON(record_json),
                 'transaction_id', 'DEMO-BROKEN-0001', TRUE),
                 'amount', 'abc', TRUE)),
       'error-demo', 'error-demo-batch', SYSDATE()
FROM DATABANK.RAW.TPE_AUTHORIZATIONS
WHERE producer_id = 'v1-migration'
LIMIT 1;

-- 1b · it lands in QUARANTINE, with the reason (expected: 1 row, INVALID_AMOUNT)
SELECT reject_reason, ingested_at, record_json
FROM DATABANK.MARTS.DQ_REJECTED_AUTHORIZATIONS
WHERE record_json LIKE '%DEMO-BROKEN-0001%';

-- 1c · and it never reaches Gold (expected: 0)
SELECT COUNT(*) AS broken_payment_in_gold
FROM DATABANK.MARTS.FCT_CARD_TRANSACTIONS
WHERE transaction_id = 'DEMO-BROKEN-0001';

-- =====================================================================
-- ERROR 2 · A payment dated 1 January 2030 (clock or parsing bug)
--           The amount is valid, so it passes the quarantine filters:
--           this time a dbt TEST must catch it.
-- =====================================================================
-- 2a · inject the impossible payment
INSERT INTO DATABANK.RAW.TPE_AUTHORIZATIONS (record_json, producer_id, batch_id, ingested_at)
SELECT TO_JSON(OBJECT_INSERT(OBJECT_INSERT(TRY_PARSE_JSON(record_json),
                 'transaction_id', 'DEMO-FUTURE-0001', TRUE),
                 'event_ts', '2030-01-01T12:00:00', TRUE)),
       'error-demo', 'error-demo-batch', SYSDATE()
FROM DATABANK.RAW.TPE_AUTHORIZATIONS
WHERE producer_id = 'v1-migration' AND TRY_PARSE_JSON(record_json):amount::FLOAT > 10
LIMIT 1;
ALTER DYNAMIC TABLE DATABANK.MARTS.FCT_CARD_TRANSACTIONS REFRESH;

-- 2b · run the pipeline: EXPECTED TO FAIL (red error = the check did its job)
--      In the error text: "Failure in test assert_transactions_not_in_future",
--      ERROR=1, and the models that depend on it are SKIPPED.
EXECUTE DBT PROJECT DATABANK.DBT.DATABANK_DBT ARGS = 'build --select fct_card_transactions+';

-- 2c · what the check found (expected: 1 row, DEMO-FUTURE-0001, 2030-01-01)
SELECT transaction_id, event_ts, amount_eur
FROM DATABANK.MARTS.FCT_CARD_TRANSACTIONS
WHERE event_ts > DATEADD(minute, 5, SYSDATE());

-- 2d · the Banque de France report was protected: no 2030 line in it
--      (expected: last_day is today or earlier, days_in_2030 = 0)
SELECT MAX(event_date) AS last_day,
       COUNT_IF(event_date >= '2030-01-01') AS days_in_2030
FROM DATABANK.MARTS.REG_BDF_DAILY_REPORT;

-- =====================================================================
-- FIX · what the data engineer does: remove the bad message, re-run
-- =====================================================================
DELETE FROM DATABANK.RAW.TPE_AUTHORIZATIONS WHERE producer_id = 'error-demo';
ALTER DYNAMIC TABLE DATABANK.MARTS.FCT_CARD_TRANSACTIONS REFRESH;

-- expected: success, ERROR=0
EXECUTE DBT PROJECT DATABANK.DBT.DATABANK_DBT ARGS = 'build --select fct_card_transactions+';

-- AFTER: clean again (expected: 0)
SELECT COUNT(*) AS payments_in_the_future
FROM DATABANK.MARTS.FCT_CARD_TRANSACTIONS
WHERE event_ts > DATEADD(minute, 5, SYSDATE());
