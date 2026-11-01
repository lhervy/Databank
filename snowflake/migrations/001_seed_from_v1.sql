-- =====================================================================
-- One-off migration: v1 prototype (BRONZE/SILVER/GOLD schemas) -> v2
-- Only for the account where the v1 prototype ran. Run BEFORE
-- 01_core_banking.sql: it creates the core banking tables from the v1
-- data, so the 300k historical card payments keep matching their cards.
-- A fresh install skips this file and uses the producer's --backfill-days.
-- =====================================================================
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE DATABANK_WH;
USE DATABASE DATABANK;

CREATE TABLE IF NOT EXISTS CORE_BANKING.CLIENTS AS
SELECT client_id, first_name, last_name, email, iban, birth_date, city, segment, client_since, SYSDATE() AS updated_at
FROM BRONZE.CORE_CLIENTS;

CREATE TABLE IF NOT EXISTS CORE_BANKING.ACCOUNTS AS
SELECT account_id, client_id, account_type, card_token, ledger_balance_eur, balance_as_of, status, SYSDATE() AS updated_at
FROM BRONZE.CORE_ACCOUNTS;

CREATE TABLE IF NOT EXISTS CORE_BANKING.MERCHANTS AS
SELECT merchant_id, category, merchant_name, city FROM BRONZE.REF_MERCHANTS;

-- Historical card payments (bulk one-time load into the v2 landing table)
INSERT INTO RAW.TPE_AUTHORIZATIONS (RECORD_JSON, PRODUCER_ID, BATCH_ID, INGESTED_AT)
SELECT TO_JSON(RECORD_CONTENT), 'v1-migration', BATCH_ID, INGESTED_AT
FROM BRONZE.CARD_AUTH_RAW
WHERE NOT EXISTS (SELECT 1 FROM RAW.TPE_AUTHORIZATIONS WHERE PRODUCER_ID = 'v1-migration');

-- Banque de France extracts already received
INSERT INTO RAW.BDF_REGISTRY (CLIENT_ID, REGISTRY, INCIDENT_FLAG, INCIDENT_TYPE, INCIDENT_DATE, EXTRACT_DATE, SOURCE_FILE, LOADED_AT)
SELECT client_id, registry, incident_flag, incident_type, incident_date, extract_date, source_file, loaded_at
FROM BRONZE.BDF_REGISTRY_RAW
WHERE NOT EXISTS (SELECT 1 FROM RAW.BDF_REGISTRY);

SELECT 'clients' t, COUNT(*) FROM CORE_BANKING.CLIENTS
UNION ALL SELECT 'accounts', COUNT(*) FROM CORE_BANKING.ACCOUNTS
UNION ALL SELECT 'tpe history', COUNT(*) FROM RAW.TPE_AUTHORIZATIONS
UNION ALL SELECT 'bdf lines', COUNT(*) FROM RAW.BDF_REGISTRY;
