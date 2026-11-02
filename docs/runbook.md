# Runbook: deploy, demo, pause, costs

## Current status (November 2026)

| Part | Status |
|---|---|
| Snowflake platform (schemas, roles, policies, stages, pipe) | ✅ deployed |
| Sources B (CDC) and C (Marketplace) | ✅ running |
| Sources A and E | ✅ history loaded; new data arrives when the GitHub workflows run |
| Sources D and F | ⏳ waiting for the GitHub ↔ Snowflake key (see [setup_github_actions.md](setup_github_actions.md)) |
| dbt project + task graph | ✅ deployed, last run: 75 passed, 0 errors |
| Dashboard | ✅ deployed |
| Snowflake ↔ GitHub link (Git workspace) | ✅ connected |

## Deploy from scratch (about 20 minutes)

Run in a Snowflake workspace as `ACCOUNTADMIN`, in this order:

| Step | File | What it does |
|---|---|---|
| 1 | `snowflake/00_account_setup.sql` | budget, warehouses, database, schemas, roles |
| 2 | `snowflake/02_raw_landing.sql` | stages, file formats, landing tables, Snowpipe |
| 3 | `snowflake/01_core_banking.sql` | simulated core banking system, streams, CDC procedure |
| 4 | `snowflake/03_marketplace_share.sql` | after getting the free *Snowflake Curated Data* listing in the Marketplace |
| 5 | `snowflake/04_service_user_github.sql` | service user for GitHub (see [setup_github_actions.md](setup_github_actions.md)) |
| 6 | `snowflake/05_security.sql` | permissions, masking and row access policies |
| 7 | deploy `dbt/databank` as `DATABANK.DBT.DATABANK_DBT`, then `06_dbt_deploy_and_dag.sql` | dbt build + task graph |
| 8 | `snowflake/08_monitoring.sql` | monitoring views |
| 9 | `streamlit/streamlit_app.py` | dashboard (Streamlit in Snowflake, warehouse `DATABANK_WH`) |
| 10 | `snowflake/09_git_integration.sql` | link Snowflake to this GitHub repository |

Upgrading from our first prototype: run `snowflake/migrations/001_seed_from_v1.sql` between steps 2 and 3.

## Live demo (5 minutes)

1. About 10 minutes before: run `snowflake/07_live_demo.sql` (turns on the live tables, the schedule and
   the activity simulator).
2. Start the card stream: GitHub → *Actions* → **A · Card terminals** → *Run workflow* (10 minutes).
3. Open the dashboard, pick a client, show the pending payments and the balance changing (about 1 minute).
4. Show the lineage (dbt graph) and the governance: query `MARTS.DIM_CLIENTS` as `DATABANK_ANALYST`
   (names masked), then as `DATABANK_COMPLIANCE` (names visible).
5. Afterwards: run `snowflake/98_pause_all.sql` and stop the dashboard (see below).

## Costs

Measured on this account: **about 11.5 credits (≈ $34) for the whole project so far**, about $3 per credit.

| Action | Approximate cost |
|---|---|
| One full dbt build (32 models + 43 tests, ~17 s) | ~$0.05 |
| A 1-hour live demo (live tables + dashboard) | ~$3–4 |
| Task graph left on all day (every 15 min) | ~$5 per day: paused between demos |
| Dashboard container left open | ~2.7 credits (~$8) per day, up to 3 days |
| GitHub loaders, Snowpipe, storage (< 1 GB) | close to $0 |

**The dashboard was the biggest cost** (about three quarters of the total): once opened, its container
keeps running for up to 3 days. To stop it after a demo:

```sql
ALTER COMPUTE POOL SYSTEM_COMPUTE_POOL_CPU STOP ALL;   -- it restarts the next time someone opens the app
```

Guard rail: the resource monitor `DATABANK_RM` (20 credits per month) suspends the warehouses at 100 %.
`99_teardown.sql` deletes everything (after the exam only).

## Troubleshooting

| Symptom | Check |
|---|---|
| No new card payments | `SELECT * FROM OPS.SOURCE_FRESHNESS`; is the GitHub stream workflow running? |
| Banque de France file not loaded | `SELECT SYSTEM$PIPE_STATUS('INGEST.PIPE_BDF_REGISTRY')`, then `OPS.FILE_LOADS` |
| dbt failed | task history: `SELECT * FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY()) WHERE DATABASE_NAME = 'DATABANK'` |
| GitHub run fails with a JWT error | the public key in Snowflake does not match the GitHub secret |
