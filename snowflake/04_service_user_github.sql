-- =====================================================================
-- DATABANK · 04 · Service users for GitHub Actions (key-pair auth only)
--
--   SVC_DATABANK_INGEST     the loaders (sources A, D, E, F)  -> role DATABANK_INGEST only
--   SVC_DATABANK_TERRAFORM  Terraform (terraform/ folder)     -> roles SYSADMIN + SECURITYADMIN
--
-- Two users, two keys: if one key leaks, the other job is not affected (least privilege).
-- No password, no MFA prompt: the private keys live only in GitHub Secrets,
-- Snowflake keeps the public keys. Rotate with RSA_PUBLIC_KEY_2, then remove the old one.
--
-- To run by the account owner - see docs/setup_github_actions.md:
--   1. Generate two key pairs (one per user) with openssl.
--   2. Paste each PUBLIC key body (between the BEGIN/END lines, no line breaks) below.
--   3. gh secret set SNOWFLAKE_PRIVATE_KEY    < rsa_ingest.p8
--      gh secret set SNOWFLAKE_TF_PRIVATE_KEY < rsa_terraform.p8     (then delete the .p8 files)
-- Public keys are not secret: they can be shared and pasted safely.
-- =====================================================================
USE ROLE ACCOUNTADMIN;

-- ---------------------------------------------------------------------
-- A. Loaders
-- ---------------------------------------------------------------------
CREATE USER IF NOT EXISTS SVC_DATABANK_INGEST
    TYPE              = SERVICE
    DEFAULT_ROLE      = DATABANK_INGEST
    DEFAULT_WAREHOUSE = DATABANK_INGEST_WH
    COMMENT           = 'GitHub Actions ingestion loaders (key-pair auth only)';

ALTER USER SVC_DATABANK_INGEST SET RSA_PUBLIC_KEY = '<PASTE_INGEST_PUBLIC_KEY_BODY_HERE>';
GRANT ROLE DATABANK_INGEST TO USER SVC_DATABANK_INGEST;

-- ---------------------------------------------------------------------
-- B. Terraform
-- ---------------------------------------------------------------------
CREATE USER IF NOT EXISTS SVC_DATABANK_TERRAFORM
    TYPE              = SERVICE
    DEFAULT_ROLE      = SYSADMIN
    DEFAULT_WAREHOUSE = DATABANK_WH
    COMMENT           = 'Terraform via GitHub Actions (key-pair auth only)';

ALTER USER SVC_DATABANK_TERRAFORM SET RSA_PUBLIC_KEY = '<PASTE_TERRAFORM_PUBLIC_KEY_BODY_HERE>';
GRANT ROLE SYSADMIN      TO USER SVC_DATABANK_TERRAFORM;   -- creates warehouses and schemas
GRANT ROLE SECURITYADMIN TO USER SVC_DATABANK_TERRAFORM;   -- creates roles and grants

-- What Terraform needs on objects created by the SQL scripts
GRANT CREATE SCHEMA ON DATABASE DATABANK TO ROLE SYSADMIN;
GRANT USAGE ON DATABASE DATABANK         TO ROLE SYSADMIN;
GRANT USAGE ON SCHEMA DATABANK.OPS       TO ROLE SYSADMIN;
GRANT USAGE ON WAREHOUSE DATABANK_WH     TO ROLE SYSADMIN;

-- Remote Terraform state: an encrypted internal stage, readable and writable by SYSADMIN only.
-- The workflow downloads the latest state before a run and uploads a new version after it.
CREATE STAGE IF NOT EXISTS DATABANK.OPS.TF_STATE
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
    COMMENT    = 'Terraform state files (one version per run) - never in Git';
GRANT READ, WRITE ON STAGE DATABANK.OPS.TF_STATE TO ROLE SYSADMIN;

-- Check: RSA_PUBLIC_KEY_FP must be set on both users
DESC USER SVC_DATABANK_INGEST;
DESC USER SVC_DATABANK_TERRAFORM;
