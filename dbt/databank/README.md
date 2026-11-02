# `dbt/databank/`: the transformations (pillar 2 · Transform)

This dbt project turns the raw data (Bronze) into clean data (Silver) and business tables (Gold).
It runs **inside Snowflake** as a native dbt Project (`DATABANK.DBT.DATABANK_DBT`), launched by the task
graph every 15 minutes. Last full run: **32 models + 43 tests, 75 passed, 0 errors, about 17 seconds.**

## How to read it

```
models/
├── staging/        Silver · 11 views, one per source table: rename, cast types, parse JSON
├── intermediate/   Silver · 3 tables: combine sources, rebuild history, de-duplicate
└── marts/          Gold · 18 models, grouped by business domain
    ├── finance/        card transactions (star schema: 1 fact + 3 dimensions), daily spend
    ├── serving/        live balances, portfolio value, the 4 secure views read by the mobile app
    ├── regulatory/     Banque de France report, AML alerts, credit risk watchlist
    ├── market/         exchange rates and stock prices
    ├── digital/        app usage
    └── dq/             quarantine of rejected payment messages
tests/              3 custom tests (business rules)
macros/             reusable SQL: schema names, masking, row access, fraud score
dbt_project.yml     configuration: which folder goes to which schema, variables
```

Every model is a SQL file with a comment at the top explaining what it does. Each model reads the
previous layer with `ref('…')` and raw tables with `source('…')`, which is how dbt knows the order to
build them in and draws the lineage graph.

## A few models worth opening

| Model | Why it is interesting |
|---|---|
| [`staging/stg_tpe__authorizations.sql`](models/staging/stg_tpe__authorizations.sql) | parses raw JSON safely: broken messages are flagged, not dropped |
| [`intermediate/int_client_history.sql`](models/intermediate/int_client_history.sql) | rebuilds the history of each client from the CDC change log (slowly changing dimension, type 2) |
| [`intermediate/int_fx_rates_daily.sql`](models/intermediate/int_fx_rates_daily.sql) | compares two independent sources of exchange rates (ECB API vs Marketplace) |
| [`marts/finance/fct_card_transactions.sql`](models/marts/finance/fct_card_transactions.sql) | a **dynamic table** (refreshed every minute): de-duplication, enrichment, fraud score |
| [`marts/serving/account_live_balance.sql`](models/marts/serving/account_live_balance.sql) | live balance = booked balance − pending payments (single source of truth) |
| [`marts/serving/app_my_transactions.sql`](models/marts/serving/app_my_transactions.sql) | secure view + row access policy: a client only sees their own payments |

## Tests

| Kind | Examples | Where |
|---|---|---|
| Generic | `unique`, `not_null`, `accepted_values`, `relationships` | `_staging.yml`, `_intermediate.yml`, `_marts.yml` |
| Custom (business rules) | live balance reconciles; no payment in the future; ECB and Marketplace rates agree within 0.5 % | [`tests/`](tests/) |
| Freshness | warns when a source stops arriving | `models/staging/_sources.yml` |

## Run it

In Snowflake (the normal way):

```sql
EXECUTE DBT PROJECT DATABANK.DBT.DATABANK_DBT ARGS = 'build';
```

The documentation and lineage graph can be generated with `dbt docs generate`.
Layer-by-layer description: [docs/data_model.md](../../docs/data_model.md).
