# `snowflake/`: the SQL that builds the platform

Every Snowflake object (warehouses, database, schemas, roles, stages, pipes, policies, tasks) is created
by one of these scripts. They are numbered in the order to run them and can be run again safely
(`CREATE … IF NOT EXISTS`). This is our form of **Infrastructure as Code**: the whole platform can be
rebuilt from this folder (see [docs/orchestration_containers_iac.md](../docs/orchestration_containers_iac.md#3-infrastructure-as-code-terraform)).

## Build scripts (run once, in this order)

| Order | Script | What it creates | Pillar |
|---|---|---|---|
| 1 | [`00_account_setup.sql`](00_account_setup.sql) | budget (resource monitor), 2 warehouses, database `DATABANK`, one schema per layer, 5 roles | foundations |
| 2 | [`02_raw_landing.sql`](02_raw_landing.sql) | file formats, stages, landing tables for A, D, E, F, the Snowpipe for E | ingest |
| 3 | [`01_core_banking.sql`](01_core_banking.sql) | the simulated core banking system (source B), its streams and the CDC procedure | ingest |
| 4 | [`03_marketplace_share.sql`](03_marketplace_share.sql) | access to the free Marketplace data (source C) | ingest |
| 5 | [`04_service_user_github.sql`](04_service_user_github.sql) | the two service users GitHub Actions logs in with (loaders, Terraform; key pairs) and the encrypted Terraform state stage | ingest + IaC |
| 6 | [`05_security.sql`](05_security.sql) | permissions per role, masking policies, row access policy | security |
| 7 | [`06_dbt_deploy_and_dag.sql`](06_dbt_deploy_and_dag.sql) | runs dbt, then creates the task graph (DAG) | transform + orchestrate |
| 8 | [`08_monitoring.sql`](08_monitoring.sql) | monitoring views in `OPS` (freshness, file loads, task runs, credits) | operate |
| 9 | [`09_git_integration.sql`](09_git_integration.sql) | link between Snowflake and this GitHub repository | operate |
| 10 | [`10_evidence_drills.sql`](10_evidence_drills.sql) | reproduces the proof: known-data checks, access tests, replay, failing test, outage | operate |

Why is `02` before `01`? The core banking script fills the change log table, which is created in `02`.

## Day-to-day scripts

| Script | When to use it |
|---|---|
| [`DEMO_START.sql`](DEMO_START.sql) / [`DEMO_STOP.sql`](DEMO_STOP.sql) | one-click switch for the oral defense: *Run all* before the demo / after it (also in the Snowflake workspace) |
| [`07_live_demo.sql`](07_live_demo.sql) | about 10 minutes before a demo: turns on the live tables, the schedule and the activity simulator |
| [`11_demo_script.sql`](11_demo_script.sql) | the queries shown during the oral defense, in order (see [docs/live_demo.md](../docs/live_demo.md)) |
| [`98_pause_all.sql`](98_pause_all.sql) | **after every demo**: stops everything that costs credits |
| [`99_teardown.sql`](99_teardown.sql) | after the exam only: deletes the whole platform |
| [`90_drop_v1_prototype.sql`](90_drop_v1_prototype.sql) | removes the schemas of our first prototype (not run yet) |
| [`migrations/001_seed_from_v1.sql`](migrations/001_seed_from_v1.sql) | one-off: moved the data of the first prototype into this version |

## Schemas created (one per layer)

| Schema | Layer | Content |
|---|---|---|
| `INGEST` | | stages, file formats and pipes used by the loaders |
| `RAW` | Bronze | data from external sources, exactly as received |
| `CORE_BANKING` | Bronze | replica of the bank's operational database (source of the CDC) |
| `STAGING` | Silver | dbt views: typed and renamed, one per source table |
| `INTERMEDIATE` | Silver | dbt tables: de-duplicated, history, combined sources |
| `MARTS` | Gold | dbt tables and views, one per business need |
| `GOVERNANCE` | | masking and row access policies |
| `DBT` | | the dbt project object and the orchestration tasks |
| `OPS` | | monitoring views |
