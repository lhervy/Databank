-- =====================================================================
-- DATABANK · 00 · Account setup
-- Budget, warehouses (workload isolation), database, schemas, roles.
-- Run once as ACCOUNTADMIN. Idempotent (safe to re-run).
-- =====================================================================
USE ROLE ACCOUNTADMIN;

-- ---------------------------------------------------------------------
-- 1. Cost control first: a budget before any query
-- ---------------------------------------------------------------------
CREATE RESOURCE MONITOR IF NOT EXISTS DATABANK_RM
  WITH CREDIT_QUOTA = 20
  FREQUENCY = MONTHLY
  START_TIMESTAMP = IMMEDIATELY
  TRIGGERS ON 75 PERCENT DO NOTIFY
           ON 100 PERCENT DO SUSPEND;

-- ---------------------------------------------------------------------
-- 2. Compute: one warehouse per workload (ingestion never slows analytics)
-- ---------------------------------------------------------------------
CREATE WAREHOUSE IF NOT EXISTS DATABANK_INGEST_WH
  WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Ingestion workloads: GitHub Actions loaders, COPY, micro-batches';

CREATE WAREHOUSE IF NOT EXISTS DATABANK_WH
  WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Transformation (dbt), dynamic tables, dashboards';

ALTER WAREHOUSE DATABANK_INGEST_WH SET RESOURCE_MONITOR = DATABANK_RM;
ALTER WAREHOUSE DATABANK_WH        SET RESOURCE_MONITOR = DATABANK_RM;

-- ---------------------------------------------------------------------
-- 3. Storage: one database, one schema per layer
--    RAW / CORE_BANKING = Bronze · STAGING / INTERMEDIATE = Silver · MARTS = Gold
-- ---------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS DATABANK COMMENT = 'Databank - fictive bank data platform';

CREATE SCHEMA IF NOT EXISTS DATABANK.INGEST       COMMENT = 'Stages, file formats and pipes used by the loaders';
CREATE SCHEMA IF NOT EXISTS DATABANK.RAW          COMMENT = 'Bronze - data exactly as received from external sources';
CREATE SCHEMA IF NOT EXISTS DATABANK.CORE_BANKING COMMENT = 'Bronze - replica of the core banking OLTP system (source of CDC)';
CREATE SCHEMA IF NOT EXISTS DATABANK.STAGING      COMMENT = 'Silver - dbt staging views: typed, renamed, one per source table';
CREATE SCHEMA IF NOT EXISTS DATABANK.INTERMEDIATE COMMENT = 'Silver - dbt intermediate models: deduplicated, enriched';
CREATE SCHEMA IF NOT EXISTS DATABANK.MARTS        COMMENT = 'Gold - dbt marts: one model per business use case';
CREATE SCHEMA IF NOT EXISTS DATABANK.GOVERNANCE   COMMENT = 'Masking and row access policies';
CREATE SCHEMA IF NOT EXISTS DATABANK.DBT          COMMENT = 'dbt project object and orchestration tasks';
CREATE SCHEMA IF NOT EXISTS DATABANK.OPS          COMMENT = 'Monitoring views (loads, pipes, dbt runs, costs)';

-- ---------------------------------------------------------------------
-- 4. Roles (least privilege). Grants on objects are in 06_security.sql
-- ---------------------------------------------------------------------
CREATE ROLE IF NOT EXISTS DATABANK_INGEST     COMMENT = 'Service role used by GitHub Actions loaders';
CREATE ROLE IF NOT EXISTS DATABANK_ENGINEER   COMMENT = 'Builds and runs the pipeline - PII masked';
CREATE ROLE IF NOT EXISTS DATABANK_ANALYST    COMMENT = 'Reads Gold - PII masked';
CREATE ROLE IF NOT EXISTS DATABANK_COMPLIANCE COMMENT = 'Regulatory reporting - PII in clear';
CREATE ROLE IF NOT EXISTS DATABANK_CLIENT_APP COMMENT = 'Mobile app - sees only the logged-in client rows';

GRANT ROLE DATABANK_INGEST     TO ROLE SYSADMIN;
GRANT ROLE DATABANK_ENGINEER   TO ROLE SYSADMIN;
GRANT ROLE DATABANK_ANALYST    TO ROLE SYSADMIN;
GRANT ROLE DATABANK_COMPLIANCE TO ROLE SYSADMIN;
GRANT ROLE DATABANK_CLIENT_APP TO ROLE SYSADMIN;

-- Ingestion service role
GRANT USAGE ON WAREHOUSE DATABANK_INGEST_WH TO ROLE DATABANK_INGEST;
GRANT USAGE ON DATABASE DATABANK            TO ROLE DATABANK_INGEST;
GRANT USAGE ON SCHEMA DATABANK.INGEST       TO ROLE DATABANK_INGEST;
GRANT USAGE ON SCHEMA DATABANK.RAW          TO ROLE DATABANK_INGEST;
GRANT USAGE ON SCHEMA DATABANK.CORE_BANKING TO ROLE DATABANK_INGEST;
