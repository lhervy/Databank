-- =====================================================================
-- DATABANK · 06 · dbt on Snowflake + the orchestration DAG
--
-- The dbt project (folder /dbt/databank) is deployed as a native
-- Snowflake DBT PROJECT object and run by a TASK GRAPH (DAG):
--
--   T_00_ROOT (every 15 min)            capture core banking CDC
--      └── T_10_DBT_BUILD               dbt build  (run + test, all layers)
--             └── T_20_DBT_FRESHNESS    dbt source freshness (alerts on late sources)
--
-- The live models (balances, portfolio) are DYNAMIC TABLES declared in
-- dbt: Snowflake refreshes them every minute on its own.
-- See the DAG in Snowsight: Transformation > Tasks > T_00_ROOT > Graph.
-- =====================================================================
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE DATABANK_WH;
USE DATABASE DATABANK;

-- ---------------------------------------------------------------------
-- 1. Deploy the dbt project
--    Easiest: open /dbt/databank/dbt_project.yml in the "Databank_Team"
--    workspace > Deploy (top right) > DATABANK.DBT.DATABANK_DBT.
--    Equivalent SQL (path of the shared workspace):
-- ---------------------------------------------------------------------
-- CREATE OR REPLACE DBT PROJECT DATABANK.DBT.DATABANK_DBT
--   FROM 'snow://workspace/DATABANK.PUBLIC."Databank_Team"/versions/live/dbt/databank';

-- First full build (also creates the dynamic tables)
EXECUTE DBT PROJECT DATABANK.DBT.DATABANK_DBT ARGS = 'build';

-- ---------------------------------------------------------------------
-- 2. The task graph (created suspended)
-- ---------------------------------------------------------------------
CREATE OR REPLACE TASK DBT.T_00_ROOT
    WAREHOUSE = DATABANK_WH
    SCHEDULE  = 'USING CRON */15 * * * * UTC'
    COMMENT   = 'DAG root: capture core banking changes (CDC)'
AS CALL DATABANK.CORE_BANKING.CAPTURE_CHANGES();

CREATE OR REPLACE TASK DBT.T_10_DBT_BUILD
    WAREHOUSE = DATABANK_WH
    COMMENT   = 'dbt build: staging -> intermediate -> marts, with tests'
    AFTER DBT.T_00_ROOT
AS EXECUTE DBT PROJECT DATABANK.DBT.DATABANK_DBT ARGS = 'build';

CREATE OR REPLACE TASK DBT.T_20_DBT_FRESHNESS
    WAREHOUSE = DATABANK_WH
    COMMENT   = 'dbt source freshness: warns when a source stops arriving'
    AFTER DBT.T_10_DBT_BUILD
AS EXECUTE DBT PROJECT DATABANK.DBT.DATABANK_DBT ARGS = 'source freshness';

-- Children can be resumed safely: they only run after the root.
ALTER TASK DBT.T_20_DBT_FRESHNESS RESUME;
ALTER TASK DBT.T_10_DBT_BUILD RESUME;
-- The root (the schedule) is resumed by 07_live_demo.sql:
-- ALTER TASK DBT.T_00_ROOT RESUME;

-- Run the whole DAG once, now
EXECUTE TASK DBT.T_00_ROOT;

SELECT name, state, scheduled_time, completed_time, error_message
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(RESULT_LIMIT => 20))
ORDER BY scheduled_time DESC;
