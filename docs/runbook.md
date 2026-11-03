# Runbook: deploy, demo, pause, costs

## Current status (November 2026)

| Part | Status |
|---|---|
| Snowflake platform (schemas, roles, policies, stages, pipe) | ✅ deployed |
| Sources B (CDC) and C (Marketplace) | ✅ running |
| Sources A and E | ✅ running from GitHub Actions (card stream on demand, Banque de France file through Snowpipe) |
| Sources D and F | ✅ running from GitHub Actions (ECB job in its Docker container; app events by `COPY INTO`) |
| dbt project + task graph | ✅ deployed, last run: 75 passed, 0 errors |
| Dashboard | ✅ deployed |
| Containerised job (`ingestion/Dockerfile`) | ✅ runs in GitHub Actions: build the image, `docker run` the ECB loader |
| Terraform (`terraform/`) | ✅ applied from GitHub Actions; state in the encrypted stage `OPS.TF_STATE` |
| Proof (drills, access tests) | ✅ logged in `OPS.EVIDENCE_LOG`, see [evidence.md](evidence.md) |
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

For the oral defense, follow [live_demo.md](live_demo.md) (running order, who says what, backups).

1. About 10 minutes before: run `snowflake/07_live_demo.sql` (turns on the live tables, the schedule and
   the activity simulator).
2. Start the card stream: GitHub → *Actions* → **A · Card terminals** → *Run workflow* (10 minutes).
3. Open the dashboard, pick a client, show the pending payments and the balance changing (about 1 minute).
4. Show the lineage (dbt graph) and the governance: query `MARTS.DIM_CLIENTS` as `DATABANK_ANALYST`
   (names masked), then as `DATABANK_COMPLIANCE` (names visible).
5. Afterwards: run `snowflake/98_pause_all.sql` and stop the dashboard (see below).

## Costs

**The project costs €0.** Everything runs on the free Snowflake trial credits and free tiers (GitHub,
GitHub Actions, Terraform, Docker, public APIs). No credit card is charged and no paid service is used.
Costs are therefore tracked in **trial credits**, the unit Snowflake would bill for compute.

| | Trial credits |
|---|---|
| Free credits included in the trial | 400 (the trial shows them as a dollar balance) |
| Used for the whole project so far (prototype v1 + v2, drills included) | about 11.5 |
| Guard rail: resource monitor `DATABANK_RM` | 20 credits per month; warehouses suspended at 100 % |

**What each action uses (measured or estimated on this account):**

| Action | Trial credits |
|---|---|
| One full dbt build (32 models + 43 tests, ~17 s on XSMALL) | ~0.02 |
| A 1-hour live demo (live tables + warehouse) | ~1 |
| Task graph left on every 15 minutes for a day | ~1.5 per day: paused between demos |
| Dashboard container left open | ~2.7 per day, up to 3 days: the biggest consumer so far (about three quarters of the total) |
| GitHub loaders, Snowpipe, storage (< 1 GB) | close to 0 |

**Projection (assumptions):** at Databank's full size (250,000 clients, assumption A2 in
[company.md](company.md)), card volume is 25× the prototype. With the same design, transformation stays on
one XSMALL warehouse for most jobs (a full build of today's 300,000 rows takes 17 s), the live path runs
during business hours only, and the dashboard container stops after each use. Estimated at about
**60–120 credits per month** for production, against about 4 per month for the prototype as used today.
A real bank would pay for this; our project never does.

**Shutdown and clean-up procedure:**
1. After every demo: run `snowflake/98_pause_all.sql` (stops the schedule, the simulator and the live tables).
2. Stop the dashboard container: `ALTER COMPUTE POOL SYSTEM_COMPUTE_POOL_CPU STOP ALL;` (it restarts the next time the app is opened).
3. After the exam: `snowflake/99_teardown.sql` deletes the whole platform; the trial then expires by itself, with nothing billed.

## Troubleshooting

| Symptom | Check |
|---|---|
| No new card payments | `SELECT * FROM OPS.SOURCE_FRESHNESS`; is the GitHub stream workflow running? |
| Banque de France file not loaded | `SELECT SYSTEM$PIPE_STATUS('INGEST.PIPE_BDF_REGISTRY')`, then `OPS.FILE_LOADS` |
| dbt failed | task history: `SELECT * FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY()) WHERE DATABASE_NAME = 'DATABANK'` |
| GitHub run fails with a JWT error | the public key in Snowflake does not match the GitHub secret |
