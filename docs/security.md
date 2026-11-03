# Security and governance

Security is built into the pipeline, not added at the end.

## Identity and access

| Role | Purpose | Can read |
|---|---|---|
| `DATABANK_INGEST` | loaders (service user `SVC_DATABANK_INGEST`) | write to `INGEST`, `RAW`; read 2 narrow views of card tokens and merchant ids |
| `DATABANK_ENGINEER` | data team, dbt | everything |
| `DATABANK_ANALYST` | BI, dashboards | `STAGING`, `MARTS`, personal data masked |
| `DATABANK_COMPLIANCE` | AML, regulators | `MARTS` unmasked |
| `DATABANK_CLIENT_APP` | mobile app backend | only `MARTS.APP_MY_*` secure views, one client at a time |

- The service user is `TYPE = SERVICE`: no password, key-pair authentication only. The private key lives in
  a GitHub encrypted secret, never in the repo (`.gitignore` blocks `*.p8`, `*.pem`).
- Least privilege: the loader cannot read client names, IBANs or balances.

## Data protection

| Control | Where |
|---|---|
| Masking `MP_PII_TEXT` (name, email, phone) | `CORE_BANKING.CLIENTS`, `MARTS.DIM_CLIENTS` |
| Masking `MP_IBAN` (shows last 4) | accounts |
| Masking `MP_BIRTH_DATE` (year only) | clients |
| Masking `MP_PII_VARIANT` (removes PII keys from JSON) | `RAW.CORE_BANKING_CHANGES.record` |
| Row access policy `RAP_OWN_CLIENT_ONLY` | app secure views, mapped by `GOVERNANCE.APP_USER_MAP` |
| Card tokenization | terminals send `card_token`, never the card number (PCI DSS) |
| Encryption | Snowflake encrypts at rest (AES-256) and in transit (TLS); stages use SSE |

## Regulation

| Rule | How the platform answers |
|---|---|
| GDPR | EU region, masking, minimization in Gold, teardown script for deletion |
| PCI DSS | tokenized cards, no PAN stored |
| DORA / ACPR | resource monitor, freshness checks, task history, reproducible infra as code |
| AML (LCB-FT) | `AML_ALERTS`, fraud score, retention of raw messages |

## Verified, not just configured

Each control was tested on 3 November 2026 with `USE SECONDARY ROLES NONE` (results in
[evidence.md](evidence.md#2-access-control-allowed-and-denied)):

- the analyst reads Gold with names, IBANs and birth dates masked, and is **denied** on the raw layer;
- compliance sees the same rows in clear;
- the client app sees only its own client's 29 payments and is **denied** on the fact table.

## Secrets

- Two service users, each with its own key pair: `SVC_DATABANK_INGEST` (loaders, role `DATABANK_INGEST`
  only) and `SVC_DATABANK_TERRAFORM` (Terraform, `SYSADMIN` + `SECURITYADMIN`).
- Private keys exist only as GitHub encrypted secrets; the Docker image receives the key at run time and
  never contains it; `.gitignore` and `.dockerignore` exclude `*.p8`, `*.pem` and `.env`.
- The Terraform state (which can hold sensitive values) is never committed; it lives in an encrypted stage
  readable by `SYSADMIN` only.

## Audit and monitoring

`snowflake/08_monitoring.sql`: source freshness, file load history (`COPY_HISTORY`), pipe status, task
history, credits per warehouse. `SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY` shows who read which column.
