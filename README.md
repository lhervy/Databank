# Databank · data platform

Final project for the *Data Engineering & Cloud Computing* course.
**Databank** is a fictive French retail and investment bank. This repository is its complete data platform:
**6 sources, 6 ingestion methods, one cloud (AWS), Snowflake, dbt, GitHub Actions.**

![Architecture](docs/img/architecture.png)

## Business case

| # | Use case | Freshness | Served by |
|---|---|---|---|
| 1 | Clients see card payments in the app, live | < 2 min (demo) | `MARTS.ACCOUNT_LIVE_BALANCE` (dynamic table) |
| 2 | Reliable market data for live investments | daily close | `MARTS.PORTFOLIO_VALUATION` |
| 3 | Personalized dashboards | 15 min | `MARTS.CLIENT_DAILY_SPEND`, Streamlit |
| 4 | Banque de France and State reporting | daily | `MARTS.REG_BDF_DAILY_REPORT`, `MARTS.AML_ALERTS` |

## Sources and ingestion methods

| | Source | Data | Ingestion method | Code |
|---|---|---|---|---|
| A | Card terminals (TPE) | simulated JSON authorizations | **Micro-batch streaming** (Python producer, every 10 s) | [`ingestion/a_tpe_stream`](ingestion/a_tpe_stream) |
| B | Core banking (OLTP) | simulated clients, accounts, positions | **CDC** with Snowflake streams + task | [`snowflake/01_core_banking.sql`](snowflake/01_core_banking.sql) |
| C | Market data | **real** Nasdaq prices, FX (Snowflake Marketplace) | **Secure data share** (zero-copy) | [`snowflake/03_marketplace_share.sql`](snowflake/03_marketplace_share.sql) |
| D | ECB Data Portal API | **real** euro reference rates | **REST API pull**, incremental (watermark + MERGE) | [`ingestion/d_ecb_api`](ingestion/d_ecb_api) |
| E | Banque de France | simulated registry CSV extracts | **PUT + Snowpipe** (REST-triggered) | [`ingestion/e_bdf_snowpipe`](ingestion/e_bdf_snowpipe) |
| F | Mobile app | simulated JSON-lines events | **PUT + batch COPY INTO** (S3 auto-ingest option) | [`ingestion/f_app_events`](ingestion/f_app_events) |

No drag and drop anywhere: every load is code, scheduled or triggered by GitHub Actions or a Snowflake task.

## Repository layout

```
.
├── .github/workflows/      CI (lint + dbt parse) and the scheduled loaders A, D, E, F
├── ingestion/              Python loaders (one folder per source) + shared connection
├── snowflake/              SQL to build the platform, in run order (00 → 08), pause, teardown
├── dbt/databank/           dbt project: staging (Silver) → intermediate (Silver) → marts (Gold)
├── streamlit/              Client dashboard + pipeline health (Streamlit in Snowflake)
└── docs/                   Architecture, sources, warehouse choice, data model, security, runbook
```

## Medallion layers

| Layer | Snowflake schemas | Built by |
|---|---|---|
| Bronze | `RAW`, `CORE_BANKING`, shared DB `SNOWFLAKE_CURATED_DATA_FREE` | loaders, Snowpipe, CDC task |
| Silver | `STAGING` (11 views), `INTERMEDIATE` | dbt |
| Gold | `MARTS` (finance, serving, regulatory, market, digital, dq) | dbt (tables, dynamic tables, secure views) |

Orchestration: a Snowflake **task graph** (CDC capture → `dbt build` → `dbt source freshness`) every 15 min,
plus **dynamic tables** refreshed every minute for the live path. See [docs/architecture.md](docs/architecture.md).

## Documentation

- [Architecture and data flow](docs/architecture.md)
- [Sources and ingestion methods](docs/sources_and_ingestion.md)
- [Why Snowflake on AWS (warehouse choice)](docs/warehouse_choice.md)
- [Data model and dbt](docs/data_model.md)
- [Security and governance](docs/security.md)
- [Setup GitHub Actions (key pair)](docs/setup_github_actions.md)
- [Runbook: deploy, demo, costs](docs/runbook.md)

## Team

[Name 1] · [Name 2] · [Name 3] — Albert School, November 2026.
All client data is random and fictive. Market data (C) and ECB rates (D) are real public data.
