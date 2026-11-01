-- =====================================================================
-- DATABANK · 04 · Service user for the GitHub Actions loaders
--
-- Loaders authenticate with a KEY PAIR (no password, no MFA prompt):
-- the private key lives only in GitHub Secrets, Snowflake keeps the
-- public key. Rotate by setting RSA_PUBLIC_KEY_2, then removing the old.
--
-- To run by the account owner - see docs/setup_github_actions.md:
--   1. openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
--      openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
--   2. Paste the public key body (between the BEGIN/END lines, no line
--      breaks) below, run this file.
--   3. gh secret set SNOWFLAKE_PRIVATE_KEY < rsa_key.p8   (then delete rsa_key.p8)
-- =====================================================================
USE ROLE ACCOUNTADMIN;

CREATE USER IF NOT EXISTS SVC_DATABANK_INGEST
    TYPE              = SERVICE
    DEFAULT_ROLE      = DATABANK_INGEST
    DEFAULT_WAREHOUSE = DATABANK_INGEST_WH
    COMMENT           = 'GitHub Actions ingestion loaders (key-pair auth only)';

ALTER USER SVC_DATABANK_INGEST SET RSA_PUBLIC_KEY = '<PASTE_PUBLIC_KEY_BODY_HERE>';

GRANT ROLE DATABANK_INGEST TO USER SVC_DATABANK_INGEST;

-- Check: RSA_PUBLIC_KEY_FP must be set
DESC USER SVC_DATABANK_INGEST;
