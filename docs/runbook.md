# Runbook: deploy, demo, costs

## Deploy from scratch (about 20 minutes)

Run in a Snowflake workspace as `ACCOUNTADMIN`, in this order:

| Step | File | What it does |
|---|---|---|
| 1 | `snowflake/00_account_setup.sql` | warehouses, database, schemas, roles, resource monitor |
| 2 | `snowflake/02_raw_landing.sql` | stages, file formats, RAW tables, Snowpipe |
| 3 | `snowflake/01_core_banking.sql` | simulated OLTP, streams, CDC procedure |
| 4 | `snowflake/03_marketplace_share.sql` | after getting the free *Snowflake Curated Data* listing |
| 5 | `snowflake/04_service_user_github.sql` | service user for GitHub (see setup_github_actions.md) |
| 6 | `snowflake/05_security.sql` | grants, masking and row access policies |
| 7 | deploy `dbt/databank` as `DATABANK.DBT.DATABANK_DBT`, then `06_dbt_deploy_and_dag.sql` | dbt build + task graph |
| 8 | `snowflake/08_monitoring.sql` | OPS views |
| 9 | `streamlit/streamlit_app.py` | dashboard (Streamlit in Snowflake, warehouse `DATABANK_WH`) |
| 10 | `snowflake/09_git_integration.sql` | link Snowflake to this GitHub repo (Git workspace) |

Upgrading from the v1 prototype: run `snowflake/migrations/001_seed_from_v1.sql` between steps 2 and 3.

## Live demo (5 minutes)

1. Run `snowflake/07_live_demo.sql` (resumes dynamic tables, tasks, simulator).
2. Start the card stream: `gh workflow run stream-a-card-terminals.yml -f minutes=10`.
3. Open the Streamlit app, pick a client, show the pending payments and balance updating (~1 min).
4. Show lineage: dbt docs graph. Show governance: query `MARTS.DIM_CLIENTS` as `DATABANK_ANALYST` (masked)
   then as `DATABANK_COMPLIANCE`.
5. Pause afterwards: `snowflake/98_pause_all.sql`.

## Costs

| Item | Setting | Estimate (trial credits) |
|---|---|---|
| `DATABANK_WH` XSMALL | 60 s auto-suspend, task every 15 min | ~1 credit / hour while running |
| Dynamic tables 1 min | only during demos | ~1 credit / hour |
| Snowpipe | serverless, per file | negligible |
| Storage | < 1 GB | negligible |
| Guard rail | `DATABANK_RM` 20 credits / month, suspends at 100 % | |

Always run `98_pause_all.sql` after a demo. `99_teardown.sql` deletes everything (after the exam).

## Troubleshooting

| Symptom | Check |
|---|---|
| No new card payments | `OPS.SOURCE_FRESHNESS`; is the stream workflow running? |
| BdF file not loaded | `SELECT SYSTEM$PIPE_STATUS('INGEST.PIPE_BDF_REGISTRY')`, `OPS.FILE_LOADS` |
| dbt failed | `SELECT * FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY()) WHERE NAME LIKE 'T_%'` |
| GitHub run fails with JWT error | public key in Snowflake doesn't match the secret |
