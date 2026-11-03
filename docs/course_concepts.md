# Course concepts → where they are in the project

This page follows the course session by session. For each concept: what it means in one line,
and where the project uses it (or why it deliberately does not).

## Session 1 · Architecture and cloud infrastructure

| Concept | In one line | In Databank |
|---|---|---|
| The 3 pillars | ingest → transform → consume | ingest: [ingestion/](../ingestion/) + [snowflake/](../snowflake/) · transform: [dbt/databank/](../dbt/databank/) · consume: `MARTS`, [streamlit/](../streamlit/) |
| Cloud providers (AWS, Azure, GCP) | three big platforms with similar services | **AWS** chosen; comparison in [warehouse_choice.md](warehouse_choice.md) |
| Shared responsibility (IaaS / PaaS / SaaS) | the more managed the service, the less you operate | Snowflake = **SaaS** (no servers to patch), GitHub Actions = SaaS, AWS = the infrastructure underneath |
| Warehouse / lake / lakehouse | where and how data is stored | a **cloud data warehouse** (Snowflake) with internal stages for files; a lakehouse on S3 + Iceberg is the documented next step |
| Medallion architecture | Bronze (raw) → Silver (clean) → Gold (business) | schemas `RAW` / `STAGING` + `INTERMEDIATE` / `MARTS`, see [data_model.md](data_model.md) |
| OLTP vs OLAP | operational database vs analytics database | the core banking system (source B) is the OLTP side; Snowflake is the OLAP side; CDC connects them |
| Security and compliance | where personal data is and who sees it | [security.md](security.md): masking, row access, EU region, GDPR / PCI DSS / DORA |
| Object storage, Parquet vs CSV | columnar files are smaller and faster to query | files land in Snowflake stages (encrypted); Snowflake stores tables in its own columnar format; see [design_questions.md](design_questions.md#7-file-formats-csv-json-parquet) |

## Session 2 · Ingestion

| Concept | In one line | In Databank |
|---|---|---|
| ETL vs ELT | transform before loading, or after | **ELT**: raw data is loaded as is, dbt transforms it inside Snowflake |
| Batch | load everything on a schedule | source F (app events, 3 times a day) |
| Incremental | load only what is new since last time | source D (ECB API): watermark + MERGE |
| Micro-batch | very small batches, very often | source A (card terminals, every 10 seconds) |
| CDC | copy only the changes of an operational database | source B (Snowflake streams on the core banking tables) |
| Streaming | records arrive one by one, continuously | source A simulates it; Kafka / Snowpipe Streaming would be used in production |
| Data sharing / Marketplace | use data another account maintains, without copying | source C (Snowflake Curated Data: real stock prices and FX) |
| Modern data stack, connectors (Fivetran…) | managed tools that move data | we wrote our own loaders to show each method; a managed connector is an option for production |
| Snowflake scaling (up / out / across) | bigger warehouse, more clusters, separate warehouses | **across**: two warehouses, one for ingestion and one for transformation, so they never slow each other down |

## Session 3 · Warehousing and transformation

| Concept | In one line | In Databank |
|---|---|---|
| Users and roles (1 user, many roles) | permissions are given to roles, roles to users | 5 roles (ingest, engineer, analyst, compliance, client app), [security.md](security.md) |
| Warehouses | compute you start and stop | `DATABANK_INGEST_WH` and `DATABANK_WH`, XSMALL, suspend after 60 seconds |
| Stage + `COPY INTO` | landing zone for files, then load into a table | sources E and F; `METADATA$FILENAME` is kept for lineage |
| Snowflake remembers loaded files (64 days) | re-running a load gives 0 duplicates | used by sources E and F |
| Watermark + MERGE | "where did I stop?" then update or insert | source D |
| Idempotency | running a job twice gives the same result | every loader and every SQL script (`IF NOT EXISTS`, MERGE, file history) |
| Key pair vs OAuth | how a program logs in without a password | **key pair** for GitHub Actions → Snowflake; **OAuth** for the Snowflake ↔ GitHub workspace link |
| Budget first | create a cost limit before any query | resource monitor `DATABANK_RM` is the first object in `00_account_setup.sql` |
| Data mesh | each domain owns its data products | not used on purpose: one small data team, see [design_questions.md](design_questions.md#3-ownership-who-fixes-a-broken-arrow-at-3-am) |
| Data as a product | a reusable, governed data package | each Gold model has a description, tests and an owner (e.g. `ACCOUNT_LIVE_BALANCE`) |
| Micro-partitions and pruning | skip the parts of a table that cannot match the filter | dashboard queries filter on dates (`event_date`, `price_date`), which lets Snowflake skip partitions |
| Materialized views | pre-computed results kept fresh | we use **dynamic tables** (same idea, but joins are allowed) for the live path |
| "The fastest query is the one you don't run" | pre-compute what is read often | Gold tables are pre-computed; the app never queries Bronze |
| dbt | SQL transformations with tests and documentation | 32 models, 43 tests, lineage graph, runs inside Snowflake |

## Session 4.1 · Containers (Docker)

| Concept | In one line | In Databank |
|---|---|---|
| "Works on my laptop, crashes on the server" | the problem Docker solves | the ECB loader runs inside our Docker image in GitHub Actions: same pinned Python and libraries everywhere |
| Image vs container | the package vs a running copy of it | the Streamlit dashboard runs as a **container** in Snowflake (container runtime on a compute pool) |
| One container per source | isolate dependencies per loader | one pinned loader image ([`ingestion/Dockerfile`](../ingestion/Dockerfile)); each run starts a container for one source, loads into Bronze, stops |
| When **not** to use Docker | keep it simple when the platform already runs the code | dbt runs as a native dbt Project in Snowflake and orchestration uses Snowflake tasks, so no container there |

Full discussion: [orchestration_containers_iac.md](orchestration_containers_iac.md#2-containers-docker).

## Session 4.2 · Orchestration and Terraform

| Concept | In one line | In Databank |
|---|---|---|
| Orchestration ≠ automation | automation runs one job; orchestration manages a chain of dependent jobs | GitHub schedules = automation; the Snowflake task graph = orchestration |
| DAG | tasks with dependencies, no loops | `T_00_ROOT → T_10_DBT_BUILD → T_20_DBT_FRESHNESS` |
| Fault tolerance | a failed step stops what depends on it | if the dbt build fails, the freshness step does not run and the Gold tables keep their last good version |
| Dependency management | B starts only after A succeeds | `AFTER` clauses in `06_dbt_deploy_and_dag.sql` |
| Resource management | start and stop compute at the right time | warehouses resume on demand and suspend after 60 s; the schedule is paused between demos |
| Monitoring | see what ran and what failed | task history, `OPS.SOURCE_FRESHNESS`, `OPS.FILE_LOADS`, dashboard "Pipeline health" tab |
| Airflow / Dagster | external orchestrators | not needed at our size: the course's own advice is to use internal warehouse features (Snowflake tasks) first |
| Infrastructure as Code | infrastructure described in versioned files | [terraform/](../terraform/): warehouse, schema, role and grants, provider pinned, state protected in an encrypted stage; core platform in re-runnable SQL scripts |

Full discussion: [orchestration_containers_iac.md](orchestration_containers_iac.md).

## Mid-term "things to rework" and how the project addresses them

| Topic | Where it is answered |
|---|---|
| Real-time analytics (ClickHouse and similar) | [design_questions.md § Latency](design_questions.md#1-latency-what-does-the-business-really-need) |
| Schema on read or on write? | [design_questions.md § Schema](design_questions.md#8-schema-on-read-or-on-write) |
| Serverless features | [design_questions.md § Serverless](design_questions.md#9-serverless-features-we-use) |
| CSV vs Parquet | [design_questions.md § File formats](design_questions.md#7-file-formats-csv-json-parquet) |
| Pruning | [design_questions.md § Performance](design_questions.md#10-performance-pruning-and-pre-computation) |
