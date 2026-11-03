-- =====================================================================
-- DATABANK · 10 · Evidence drills (reproduce docs/evidence.md)
-- Results are written to DATABANK.OPS.EVIDENCE_LOG. Uses free trial credits only.
-- Run block by block in a Snowflake workspace as ACCOUNTADMIN.
-- =====================================================================
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE DATABANK_WH;

CREATE TABLE IF NOT EXISTS DATABANK.OPS.EVIDENCE_LOG (
    drill STRING, step STRING, metric STRING, value STRING, logged_at TIMESTAMP_NTZ DEFAULT SYSDATE());

-- ---------------------------------------------------------------------
-- 1. Output vs known data: injected defect rates (~1 % duplicates, ~0.2 % broken, ~0.3 % > €1,000)
-- ---------------------------------------------------------------------
SELECT COUNT(*) AS raw_messages,
       COUNT_IF(is_parsable) - COUNT(DISTINCT IFF(is_parsable, transaction_id, NULL)) AS duplicate_messages,
       COUNT_IF(is_parsable AND (amount_eur IS NULL OR amount_eur <= 0))           AS invalid_amount,
       COUNT_IF(amount_eur > 1000)                                                  AS over_1000
FROM DATABANK.STAGING.STG_TPE__AUTHORIZATIONS;

-- Independent recomputation of one day of the Banque de France report, straight from the raw JSON
WITH indep AS (
  SELECT j, TRY_TO_NUMBER(j:amount::STRING, 12, 2) AS amt
  FROM (SELECT TRY_PARSE_JSON(record_json) AS j, ingested_at FROM DATABANK.RAW.TPE_AUTHORIZATIONS)
  WHERE j:transaction_id IS NOT NULL AND TRY_TO_NUMBER(j:amount::STRING, 12, 2) > 0
    AND TRY_TO_TIMESTAMP_NTZ(j:event_ts::STRING)::DATE = '2026-10-15'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY j:transaction_id::STRING ORDER BY ingested_at) = 1)
SELECT 'recomputed' AS source, COUNT(*) AS n, ROUND(SUM(IFF(j:status::STRING = 'AUTHORIZED', amt, 0)), 2) AS authorized_eur FROM indep
UNION ALL
SELECT 'gold', n_transactions, ROUND(authorized_amount_eur, 2) FROM DATABANK.MARTS.REG_BDF_DAILY_REPORT WHERE event_date = '2026-10-15';

-- ---------------------------------------------------------------------
-- 2. Access control: allowed / denied (no secondary roles, so only the tested role counts)
-- ---------------------------------------------------------------------
USE ROLE DATABANK_ANALYST;   USE SECONDARY ROLES NONE;
SELECT client_id, first_name, iban, birth_date FROM DATABANK.MARTS.DIM_CLIENTS LIMIT 2;   -- allowed, masked
SELECT COUNT(*) FROM DATABANK.RAW.TPE_AUTHORIZATIONS;                                       -- DENIED (expected error)
USE ROLE DATABANK_COMPLIANCE; USE SECONDARY ROLES NONE;
SELECT client_id, first_name, iban FROM DATABANK.MARTS.DIM_CLIENTS LIMIT 2;                -- allowed, clear
USE ROLE DATABANK_CLIENT_APP; USE SECONDARY ROLES NONE;
SELECT COUNT(*), LISTAGG(DISTINCT client_id, ',') FROM DATABANK.MARTS.APP_MY_TRANSACTIONS;  -- only C000042
SELECT COUNT(*) FROM DATABANK.MARTS.FCT_CARD_TRANSACTIONS;                                  -- DENIED (expected error)
USE ROLE ACCOUNTADMIN; USE SECONDARY ROLES ALL;

-- ---------------------------------------------------------------------
-- 3. Incident 1 · replay: resend 500 already-loaded messages, figures must not change
-- ---------------------------------------------------------------------
INSERT INTO DATABANK.OPS.EVIDENCE_LOG (drill, step, metric, value)
SELECT 'replay', 'before', 'fct_rows', COUNT(*)::STRING FROM DATABANK.MARTS.FCT_CARD_TRANSACTIONS
UNION ALL SELECT 'replay', 'before', 'raw_rows', COUNT(*)::STRING FROM DATABANK.RAW.TPE_AUTHORIZATIONS
UNION ALL SELECT 'replay', 'before', 'bdf_2026_10_15_authorized', ROUND(authorized_amount_eur, 2)::STRING
          FROM DATABANK.MARTS.REG_BDF_DAILY_REPORT WHERE event_date = '2026-10-15';

INSERT INTO DATABANK.RAW.TPE_AUTHORIZATIONS (RECORD_JSON, PRODUCER_ID, BATCH_ID, INGESTED_AT)
SELECT RECORD_JSON, 'drill-replay', 'drill-replay-batch', SYSDATE() FROM DATABANK.RAW.TPE_AUTHORIZATIONS
WHERE TRY_PARSE_JSON(RECORD_JSON):event_ts::STRING LIKE '2026-10-15%' AND PRODUCER_ID <> 'drill-replay' LIMIT 500;

ALTER DYNAMIC TABLE DATABANK.MARTS.FCT_CARD_TRANSACTIONS REFRESH;
ALTER DYNAMIC TABLE DATABANK.MARTS.ACCOUNT_LIVE_BALANCE REFRESH;
EXECUTE DBT PROJECT DATABANK.DBT.DATABANK_DBT ARGS = 'build --select fct_card_transactions+';

INSERT INTO DATABANK.OPS.EVIDENCE_LOG (drill, step, metric, value)
SELECT 'replay', 'after', 'fct_rows', COUNT(*)::STRING FROM DATABANK.MARTS.FCT_CARD_TRANSACTIONS
UNION ALL SELECT 'replay', 'after', 'raw_rows', COUNT(*)::STRING FROM DATABANK.RAW.TPE_AUTHORIZATIONS
UNION ALL SELECT 'replay', 'after', 'bdf_2026_10_15_authorized', ROUND(authorized_amount_eur, 2)::STRING
          FROM DATABANK.MARTS.REG_BDF_DAILY_REPORT WHERE event_date = '2026-10-15';

-- ---------------------------------------------------------------------
-- 4. A check that fails: a payment dated 2030 must stop the build before Gold
-- ---------------------------------------------------------------------
INSERT INTO DATABANK.RAW.TPE_AUTHORIZATIONS (RECORD_JSON, PRODUCER_ID, BATCH_ID, INGESTED_AT)
SELECT TO_JSON(OBJECT_INSERT(OBJECT_INSERT(TRY_PARSE_JSON(RECORD_JSON), 'transaction_id', 'DRILL-FUTURE-0001', TRUE),
                             'event_ts', '2030-01-01T12:00:00', TRUE)),
       'drill-future', 'drill-future-batch', SYSDATE()
FROM DATABANK.RAW.TPE_AUTHORIZATIONS WHERE PRODUCER_ID = 'v1-migration' AND TRY_PARSE_JSON(RECORD_JSON):amount::FLOAT > 10 LIMIT 1;

ALTER DYNAMIC TABLE DATABANK.MARTS.FCT_CARD_TRANSACTIONS REFRESH;
-- Expected: "DBT job failed ... Failure in test assert_transactions_not_in_future ... ERROR=1 SKIP=13"
EXECUTE DBT PROJECT DATABANK.DBT.DATABANK_DBT ARGS = 'build --select fct_card_transactions+';

-- Recovery: remove the bad record, rebuild: expected PASS=22, ERROR=0
DELETE FROM DATABANK.RAW.TPE_AUTHORIZATIONS WHERE PRODUCER_ID = 'drill-future';
ALTER DYNAMIC TABLE DATABANK.MARTS.FCT_CARD_TRANSACTIONS REFRESH;
ALTER DYNAMIC TABLE DATABANK.MARTS.ACCOUNT_LIVE_BALANCE REFRESH;
EXECUTE DBT PROJECT DATABANK.DBT.DATABANK_DBT ARGS = 'build --select fct_card_transactions+';

-- ---------------------------------------------------------------------
-- 5. Incident 2 · ECB outage: freshness warns, rates fall back to the Marketplace
-- ---------------------------------------------------------------------
EXECUTE DBT PROJECT DATABANK.DBT.DATABANK_DBT ARGS = 'source freshness';
SELECT rate_source, COUNT(*) FROM DATABANK.MARTS.FX_RATES_DAILY GROUP BY 1;

-- Review everything that was logged
SELECT drill, step, metric, value, logged_at FROM DATABANK.OPS.EVIDENCE_LOG ORDER BY logged_at;

-- Afterwards: stop what costs credits
-- ALTER DYNAMIC TABLE DATABANK.MARTS.FCT_CARD_TRANSACTIONS SUSPEND;
-- ALTER DYNAMIC TABLE DATABANK.MARTS.ACCOUNT_LIVE_BALANCE SUSPEND;
