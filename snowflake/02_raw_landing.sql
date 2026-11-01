-- =====================================================================
-- DATABANK · 02 · Landing zone for external sources (Bronze)
--
--   A  Card terminals (TPE)      -> RAW.TPE_AUTHORIZATIONS   micro-batch streaming (Python producer)
--   D  ECB exchange-rate API     -> RAW.ECB_FX_RATES         REST API pull, incremental MERGE
--   E  Banque de France files    -> RAW.BDF_REGISTRY         Snowpipe (REST-triggered) from a stage
--   F  Mobile app events (JSON)  -> RAW.APP_EVENTS           batch COPY INTO from a stage
--
-- Loaders run outside Snowflake (GitHub Actions, see /ingestion and
-- /.github/workflows) with the DATABANK_INGEST service role.
-- =====================================================================
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE DATABANK_WH;
USE DATABASE DATABANK;

-- ---------------------------------------------------------------------
-- File formats and internal stages (encrypted at rest by Snowflake)
-- ---------------------------------------------------------------------
CREATE FILE FORMAT IF NOT EXISTS INGEST.FF_BDF_CSV
    TYPE = CSV FIELD_DELIMITER = ';' SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"' NULL_IF = ('') EMPTY_FIELD_AS_NULL = TRUE;

CREATE FILE FORMAT IF NOT EXISTS INGEST.FF_NDJSON
    TYPE = JSON STRIP_OUTER_ARRAY = FALSE;   -- one JSON object per line

CREATE STAGE IF NOT EXISTS INGEST.STG_BDF
    FILE_FORMAT = INGEST.FF_BDF_CSV ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
    COMMENT = 'Landing zone for Banque de France registry extracts (source E)';

CREATE STAGE IF NOT EXISTS INGEST.STG_APP_EVENTS
    FILE_FORMAT = INGEST.FF_NDJSON ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
    COMMENT = 'Landing zone for mobile app event files (source F)';

-- ---------------------------------------------------------------------
-- A - Card terminal authorizations (raw JSON text, parsed in dbt)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS RAW.TPE_AUTHORIZATIONS (
    RECORD_JSON  STRING        COMMENT 'Authorization message exactly as sent by the acquirer',
    PRODUCER_ID  STRING        COMMENT 'Which producer instance sent it',
    BATCH_ID     STRING        COMMENT 'Micro-batch identifier',
    INGESTED_AT  TIMESTAMP_NTZ COMMENT 'When Databank received it (UTC)'
) COMMENT = 'Source A - card terminal (TPE) authorizations, micro-batch streaming';

-- ---------------------------------------------------------------------
-- D - ECB reference exchange rates (from the ECB Data Portal REST API)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS RAW.ECB_FX_RATES (
    RATE_DATE      DATE,
    CURRENCY       STRING   COMMENT 'Quoted currency, e.g. USD',
    BASE_CURRENCY  STRING   COMMENT 'Always EUR for ECB reference rates',
    RATE           FLOAT    COMMENT 'Units of CURRENCY for 1 EUR',
    SERIES_KEY     STRING   COMMENT 'ECB series key, e.g. EXR.D.USD.EUR.SP00.A',
    LOADED_AT      TIMESTAMP_NTZ,
    RUN_ID         STRING   COMMENT 'GitHub Actions run that loaded the row'
) COMMENT = 'Source D - ECB euro reference rates, REST API, incremental';

-- ---------------------------------------------------------------------
-- E - Banque de France credit-incident registry extracts (CSV files)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS RAW.BDF_REGISTRY (
    CLIENT_ID      STRING,
    REGISTRY       STRING,
    INCIDENT_FLAG  BOOLEAN,
    INCIDENT_TYPE  STRING,
    INCIDENT_DATE  DATE,
    EXTRACT_DATE   DATE,
    SOURCE_FILE    STRING        COMMENT 'Lineage: file the row came from',
    LOADED_AT      TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
) COMMENT = 'Source E - Banque de France registry extracts, loaded by Snowpipe';

-- Snowpipe: the loader PUTs a file on the stage, then calls the Snowpipe
-- REST endpoint (insertFiles). Snowflake loads it with serverless compute.
-- (With an S3 bucket the same pipe would use AUTO_INGEST = TRUE.)
CREATE PIPE IF NOT EXISTS INGEST.PIPE_BDF_REGISTRY
    COMMENT = 'Loads Banque de France files from INGEST.STG_BDF'
AS
COPY INTO RAW.BDF_REGISTRY (CLIENT_ID, REGISTRY, INCIDENT_FLAG, INCIDENT_TYPE, INCIDENT_DATE, EXTRACT_DATE, SOURCE_FILE)
FROM (SELECT $1, $2, $3, $4, $5, $6, METADATA$FILENAME FROM @INGEST.STG_BDF)
FILE_FORMAT = (FORMAT_NAME = 'INGEST.FF_BDF_CSV');

-- ---------------------------------------------------------------------
-- F - Mobile app events (newline-delimited JSON files)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS RAW.APP_EVENTS (
    RECORD       VARIANT       COMMENT 'One app event (screen view, login, budget set...)',
    SOURCE_FILE  STRING,
    FILE_ROW     NUMBER,
    LOADED_AT    TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
) COMMENT = 'Source F - mobile app events, batch COPY INTO';

-- ---------------------------------------------------------------------
-- Grants for the ingestion service role (least privilege)
-- ---------------------------------------------------------------------
GRANT INSERT, SELECT ON TABLE RAW.TPE_AUTHORIZATIONS TO ROLE DATABANK_INGEST;
GRANT INSERT, SELECT, UPDATE ON TABLE RAW.ECB_FX_RATES TO ROLE DATABANK_INGEST;
GRANT INSERT, SELECT ON TABLE RAW.BDF_REGISTRY TO ROLE DATABANK_INGEST;
GRANT INSERT, SELECT ON TABLE RAW.APP_EVENTS TO ROLE DATABANK_INGEST;
GRANT CREATE TABLE, CREATE STAGE ON SCHEMA RAW TO ROLE DATABANK_INGEST;   -- temp objects used by write_pandas / MERGE
GRANT READ, WRITE ON STAGE INGEST.STG_BDF        TO ROLE DATABANK_INGEST;
GRANT READ, WRITE ON STAGE INGEST.STG_APP_EVENTS TO ROLE DATABANK_INGEST;
GRANT USAGE ON FILE FORMAT INGEST.FF_BDF_CSV     TO ROLE DATABANK_INGEST;
GRANT USAGE ON FILE FORMAT INGEST.FF_NDJSON      TO ROLE DATABANK_INGEST;
GRANT OPERATE, MONITOR ON PIPE INGEST.PIPE_BDF_REGISTRY TO ROLE DATABANK_INGEST;


-- =====================================================================
-- OPTIONAL - own S3 bucket with Snowpipe auto-ingest (when AWS is ready)
-- Replace <bucket> and <role-arn>, run, then follow DESC INTEGRATION
-- output to set the trust policy and the S3 event notification.
-- =====================================================================
-- CREATE STORAGE INTEGRATION S3_DATABANK
--   TYPE = EXTERNAL_STAGE STORAGE_PROVIDER = 'S3' ENABLED = TRUE
--   STORAGE_AWS_ROLE_ARN = '<role-arn>'
--   STORAGE_ALLOWED_LOCATIONS = ('s3://<bucket>/app-events/');
-- CREATE STAGE INGEST.S3_APP_EVENTS URL = 's3://<bucket>/app-events/'
--   STORAGE_INTEGRATION = S3_DATABANK FILE_FORMAT = INGEST.FF_NDJSON;
-- CREATE PIPE INGEST.PIPE_APP_EVENTS_S3 AUTO_INGEST = TRUE AS
--   COPY INTO RAW.APP_EVENTS (RECORD, SOURCE_FILE, FILE_ROW)
--   FROM (SELECT $1, METADATA$FILENAME, METADATA$FILE_ROW_NUMBER FROM @INGEST.S3_APP_EVENTS);
