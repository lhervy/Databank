-- =====================================================================
-- DATABANK · 08 · Monitoring views (OPS schema)
-- "Who fixes a broken arrow at 3 a.m.?" - these views tell them where.
-- =====================================================================
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE DATABANK_WH;
USE DATABASE DATABANK;

-- Freshness of every source, in one place
CREATE OR REPLACE VIEW OPS.SOURCE_FRESHNESS AS
SELECT 'A · Card terminals' AS source, MAX(ingested_at) AS last_arrival, COUNT(*) AS total_rows FROM RAW.TPE_AUTHORIZATIONS
UNION ALL SELECT 'B · Core banking CDC', MAX(captured_at), COUNT(*) FROM RAW.CORE_BANKING_CHANGES
UNION ALL SELECT 'D · ECB API',          MAX(loaded_at), COUNT(*) FROM RAW.ECB_FX_RATES
UNION ALL SELECT 'E · Banque de France', MAX(loaded_at)::TIMESTAMP_NTZ, COUNT(*) FROM RAW.BDF_REGISTRY
UNION ALL SELECT 'F · App events',       MAX(loaded_at)::TIMESTAMP_NTZ, COUNT(*) FROM RAW.APP_EVENTS;

-- File loads (Snowpipe + COPY) of the last 7 days
CREATE OR REPLACE VIEW OPS.FILE_LOADS AS
SELECT table_name, file_name, status, row_count, first_error_message, last_load_time
FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(TABLE_NAME => 'DATABANK.RAW.BDF_REGISTRY', START_TIME => DATEADD(day, -7, CURRENT_TIMESTAMP())))
UNION ALL
SELECT table_name, file_name, status, row_count, first_error_message, last_load_time
FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(TABLE_NAME => 'DATABANK.RAW.APP_EVENTS', START_TIME => DATEADD(day, -7, CURRENT_TIMESTAMP())));

SELECT * FROM OPS.SOURCE_FRESHNESS;
SELECT SYSTEM$PIPE_STATUS('DATABANK.INGEST.PIPE_BDF_REGISTRY') AS bdf_pipe_status;

-- DAG runs
SELECT name, state, scheduled_time, completed_time, error_message
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(RESULT_LIMIT => 30))
ORDER BY scheduled_time DESC;

-- Credits per warehouse (workload isolation makes the cost driver visible)
SELECT warehouse_name, SUM(credits_used) AS credits_last_7_days
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time > DATEADD(day, -7, CURRENT_TIMESTAMP())
GROUP BY 1 ORDER BY 2 DESC;
