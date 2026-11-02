# Databank · a complete data platform for a fictive bank

Final project for the *Data Engineering* course at Albert School (oral defense, November 2026).

**Databank** is an imaginary French bank with a mobile app, cards and investment accounts.
This repository contains its whole data platform: data comes from **6 different sources**, enters
through **6 different ingestion methods**, is stored and transformed in **Snowflake on AWS (Paris region)**
with **dbt**, and is served to a client app, analysts and the regulator.

![Architecture of the Databank data platform](docs/img/architecture.png)

> **New here? Read in this order (about 10 minutes):**
> 1. This page: the business problem, the picture above and the checklist below.
> 2. [docs/architecture.md](docs/architecture.md): what each letter (sources) and number (steps) in the picture means.
> 3. [docs/course_concepts.md](docs/course_concepts.md): where every concept from the course appears in the project.
> 4. [docs/design_questions.md](docs/design_questions.md): our answers to the six questions every architecture should face (latency, scaling, ownership, single source of truth, cost, security).

---

## 1. The business problem

Databank has data everywhere and no single view of it. Four needs drive the platform:

| # | What the business needs | How fresh it must be | Where it is served |
|---|---|---|---|
| 1 | A client sees a card payment in the app right after paying | about 1 minute | `MARTS.ACCOUNT_LIVE_BALANCE` |
| 2 | Investment accounts valued with real market prices | once a day (market close) | `MARTS.PORTFOLIO_VALUATION` |
| 3 | Personal dashboards (spending by category) | every 15 minutes | `MARTS.CLIENT_DAILY_SPEND` + Streamlit dashboard |
| 4 | Reports for the Banque de France and anti-money-laundering checks | once a day | `MARTS.REG_BDF_DAILY_REPORT`, `MARTS.AML_ALERTS` |

The required freshness decides the technology: only the first need justifies near-real-time processing,
everything else runs in cheaper batches (see [design_questions.md](docs/design_questions.md#1-latency-what-does-the-business-really-need)).

## 2. Project checklist (course requirements)

| Requirement | Status | Where to check |
|---|---|---|
| Multiple sources (3 to 15) | ✅ 6 sources, 2 of them real public data | [Section 3](#3-the-six-sources-and-how-each-one-is-ingested) |
| Data from different kinds of sources | ✅ payment terminals, an internal database, a data marketplace, a public API, regulator files, app logs | [docs/sources_and_ingestion.md](docs/sources_and_ingestion.md) |
| Multiple ingestion methods, no drag and drop | ✅ 6 methods, all written as code and scheduled | [ingestion/](ingestion/), [.github/workflows/](.github/workflows/) |
| One cloud | ✅ AWS only (Snowflake runs on AWS `eu-west-3`, Paris) | [docs/warehouse_choice.md](docs/warehouse_choice.md) |
| Warehouse choice justified | ✅ Snowflake compared with Redshift, BigQuery and Databricks | [docs/warehouse_choice.md](docs/warehouse_choice.md) |
| dbt | ✅ 32 models and 43 tests, running inside Snowflake | [dbt/databank/](dbt/databank/) |
| Orchestration | ✅ task graph (DAG) in Snowflake + scheduled GitHub Actions | [docs/orchestration_containers_iac.md](docs/orchestration_containers_iac.md) |
| Documentation | ✅ this README, one README per folder, 13 documents in `docs/` | [docs/](docs/) |
| GitHub with a clear folder system | ✅ one folder per pipeline stage | [Section 7](#7-how-the-repository-is-organised) |
| Every person owns something in the pipeline | ✅ one owner per area | [Section 8](#8-team-and-ownership) |

## 3. The six sources and how each one is ingested

The letters match the diagram. Each source uses a **different** ingestion method, chosen for how that data
behaves in real life.

| | Source | Real or simulated | Ingestion method | Why this method |
|---|---|---|---|---|
| A | Card payment terminals | simulated | **Micro-batch streaming**: small batches every 10 seconds | payments must reach the app within a minute |
| B | Core banking system (clients, accounts, positions) | simulated | **CDC** (change data capture) with Snowflake streams | only changes are copied, never the whole table again |
| C | Stock prices and exchange rates (Snowflake Marketplace) | **real** | **Secure data sharing**: zero copy | the provider maintains the data; nothing to load |
| D | European Central Bank exchange-rate API | **real** | **REST API pull, incremental**: only new days, then MERGE | a public API that publishes once a day |
| E | Banque de France registry files (CSV) | simulated | **File + Snowpipe**: file is put in a stage, Snowpipe loads it | regulators send files; Snowpipe never loads a file twice |
| F | Mobile app events (JSON) | simulated | **Batch file load** (`COPY INTO`) | logs are large but not urgent: load them 3 times a day |

Details, volumes and schedules: [docs/sources_and_ingestion.md](docs/sources_and_ingestion.md).

## 4. How the data flows: Bronze → Silver → Gold

We use the **medallion architecture** seen in class. Each layer is a separate schema in Snowflake.

| Layer | Snowflake schemas | What it contains | Built by |
|---|---|---|---|
| **Bronze** (raw) | `RAW`, `CORE_BANKING`, shared database from the Marketplace | data exactly as received, kept for replay and audit | the 6 ingestion methods |
| **Silver** (clean) | `STAGING` (11 views), `INTERMEDIATE` (3 tables) | typed, renamed, de-duplicated, history of changes | dbt |
| **Gold** (business) | `MARTS` (18 models) | one table per business need, ready for the app and reports | dbt |

The approach is **ELT**: we load first, then transform inside the warehouse. Bad records are not deleted,
they are set aside in a quarantine table (`MARTS.DQ_REJECTED_AUTHORIZATIONS`) so they can be investigated.

## 5. How it runs by itself (orchestration)

- **Inside Snowflake:** a task graph (DAG) runs every 15 minutes:
  1. capture core banking changes,
  2. then `dbt build` (transform and test every layer),
  3. then `dbt source freshness` (raise an alert if a source stops arriving).

  A step only starts if the previous one succeeded.
- **Live path:** two **dynamic tables** refresh themselves every minute (card payments and live balances).
- **Outside Snowflake:** GitHub Actions runs the loaders on a schedule (ECB rates every working day,
  Banque de France file every morning, app events 3 times a day).

Why Snowflake tasks rather than Airflow, why no Docker image, and how Terraform would fit:
[docs/orchestration_containers_iac.md](docs/orchestration_containers_iac.md).

## 6. Who uses the data (consumption)

| Consumer | What they see | Protection |
|---|---|---|
| Mobile app (the client) | their own payments, balance, portfolio | row access policy: a client only sees their own rows |
| Analysts and dashboards | all Gold tables | names, emails and IBANs are masked |
| Compliance team | AML alerts, credit risk list | full access, for legal checks |
| Banque de France | daily regulatory report | aggregated figures only |

A Streamlit dashboard ([streamlit/](streamlit/)) shows the client view, the markets and the health of the pipeline.

## 7. How the repository is organised

Each folder is one stage of the pipeline and has its own README explaining what is inside.

```
databank-data-platform/
├── README.md               ← you are here
├── docs/                   ← all documentation (start with architecture.md)
│   └── img/                ← architecture diagram
├── snowflake/              ← SQL that builds the platform, numbered in run order (00 → 09)
├── ingestion/              ← Python loaders, one folder per source (a_, d_, e_, f_)
├── .github/workflows/      ← schedules that run the loaders + automatic checks on every change
├── dbt/databank/           ← dbt project: staging (Silver) → intermediate → marts (Gold)
└── streamlit/              ← dashboard (client view, markets, pipeline health)
```

| Folder | Pillar | README |
|---|---|---|
| `ingestion/`, `.github/workflows/` | 1 · Ingest | [ingestion/README.md](ingestion/README.md), [.github/workflows/README.md](.github/workflows/README.md) |
| `snowflake/` | Store, secure, orchestrate | [snowflake/README.md](snowflake/README.md) |
| `dbt/databank/` | 2 · Transform | [dbt/databank/README.md](dbt/databank/README.md) |
| `streamlit/` | 3 · Consume | [streamlit/README.md](streamlit/README.md) |

## 8. Team and ownership

Every area of the pipeline has one owner: the person who answers "who fixes it at 3 a.m.?".

| Area | What it covers | Owner |
|---|---|---|
| Ingestion | sources A, D, E, F, the Python loaders and GitHub Actions | *[Name]* |
| Core banking, security and governance | source B (CDC), roles, masking, row access, cost control | *[Name]* |
| Transformation and serving | dbt models and tests, task graph, dynamic tables, dashboard | *[Name]* |

## 9. Documentation

| Document | What it explains |
|---|---|
| [architecture.md](docs/architecture.md) | the diagram, step by step (sources A–F, steps 1–9) |
| [sources_and_ingestion.md](docs/sources_and_ingestion.md) | each source, its method, volume and schedule |
| [warehouse_choice.md](docs/warehouse_choice.md) | why Snowflake on AWS (vs Redshift, BigQuery, Databricks) |
| [data_model.md](docs/data_model.md) | the dbt models, layer by layer, and the tests |
| [orchestration_containers_iac.md](docs/orchestration_containers_iac.md) | orchestration, Docker and Terraform: what we use and why |
| [security.md](docs/security.md) | roles, masking, row access, regulation (GDPR, PCI DSS, DORA) |
| [design_questions.md](docs/design_questions.md) | latency, scaling, ownership, single source of truth, cost, security |
| [course_concepts.md](docs/course_concepts.md) | every course concept and where to find it in the project |
| [runbook.md](docs/runbook.md) | how to deploy, run the demo, pause, and what it costs |
| [setup_github_actions.md](docs/setup_github_actions.md) | how GitHub connects to Snowflake (key pair) |
| [target_architecture.md](docs/target_architecture.md) | the best-case design with unlimited budget, compared with today |
| [forecast.md](docs/forecast.md) | 2027–2030 forecast based on Gartner research and emerging tools |
| [glossary.md](docs/glossary.md) | every technical word used here, in plain language |

## 10. Key figures (measured in Snowflake, November 2026)

| | |
|---|---|
| Clients / accounts / merchants | 10,000 / 13,583 / 400 |
| Card messages received → valid transactions | 303,295 → 299,747 (557 quarantined, the rest were duplicates) |
| Investment positions valued with real prices | 10,575 |
| dbt build (32 models + 43 tests) | 75 passed, 0 errors, about 17 seconds |
| Total Snowflake spend for the whole project so far | about 11.5 credits (≈ $34) |

## 11. And with an unlimited budget?

We also designed the **best-case version** of this pipeline: Kafka and Flink for millisecond fraud checks,
an open Iceberg lakehouse, managed connectors, machine learning, Airflow, Terraform and a second region
for disaster recovery. It keeps the same cloud, warehouse, layers and dbt models, so today's pipeline can
grow into it step by step.

[![Target architecture](docs/img/target_architecture.png)](docs/target_architecture.md)

Full comparison, costs and migration plan: [docs/target_architecture.md](docs/target_architecture.md).

## 12. Where it is heading (2027–2030)

Based on Gartner's research (AI-ready data, the shift to event streaming, AI agents and their failure
rates, decision governance, semantic layers, open table formats, sovereignty) and the EU AI Act deadline
for credit scoring (2 December 2027), we forecast how Databank's platform should evolve, with three
scenarios and a watchlist of emerging tools: [docs/forecast.md](docs/forecast.md).

---

All client data is **random and fictive**. Market data (source C) and ECB exchange rates (source D) are
**real public data**. No real person or bank is represented.
