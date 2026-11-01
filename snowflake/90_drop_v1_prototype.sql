-- =====================================================================
-- DATABANK · 90 · Remove the v1 prototype schemas (BRONZE/SILVER/GOLD/SIM)
-- Run once v2 is built and checked. The shared workspace (DATABANK.PUBLIC)
-- and the v2 schemas are not touched.
-- =====================================================================
USE ROLE ACCOUNTADMIN;
DROP SCHEMA IF EXISTS DATABANK.GOLD;
DROP SCHEMA IF EXISTS DATABANK.SILVER;
DROP SCHEMA IF EXISTS DATABANK.SIM;
DROP SCHEMA IF EXISTS DATABANK.BRONZE;
