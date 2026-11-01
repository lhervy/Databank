# Data model and dbt

The dbt project lives in [`dbt/databank`](../dbt/databank) and runs inside Snowflake as a dbt Project
(`DATABANK.DBT.DATABANK_DBT`). `dbt build` runs models and tests together; `dbt docs generate` produces the
lineage graph.

## Layers

| Folder | Schema | Materialization | Role |
|---|---|---|---|
| `models/staging` | `STAGING` | view | one model per source table: rename, cast, parse JSON, dedupe |
| `models/intermediate` | `INTERMEDIATE` | table | business logic shared by several marts |
| `models/marts/*` | `MARTS` | table, dynamic table, secure view | what consumers read |

## Staging (Silver) - 11 models

`stg_tpe__authorizations`, `stg_core_banking__clients`, `stg_core_banking__accounts`,
`stg_core_banking__merchants`, `stg_core_banking__positions`, `stg_cdc__core_banking_changes`,
`stg_market__stock_prices`, `stg_market__fx_rates`, `stg_ecb__fx_rates`, `stg_bdf__registry`,
`stg_app__events`.

## Intermediate

| Model | What it does |
|---|---|
| `int_fx_rates_daily` | joins ECB API (D) and Marketplace (C) rates, keeps both, computes the gap |
| `int_client_history` | SCD type 2 history of clients rebuilt from the CDC change log (B) |
| `int_client_credit_status` | joins clients to the BdF registry (E) |

## Marts (Gold)

| Domain | Models |
|---|---|
| finance | `fct_card_transactions` (dynamic table), `dim_clients`, `dim_accounts`, `dim_merchants`, `client_daily_spend` |
| serving | `account_live_balance` (dynamic table), `portfolio_valuation`, `app_my_transactions`, `app_my_balance`, `app_my_portfolio`, `app_my_spend` |
| regulatory | `reg_bdf_daily_report`, `aml_alerts`, `credit_risk_watchlist` |
| market | `fx_rates_daily`, `stock_prices_daily` |
| digital | `app_engagement_daily` |
| dq | `dq_rejected_authorizations` |

Star schema at the core: `fct_card_transactions` with `dim_clients`, `dim_accounts`, `dim_merchants`.

## Tests

- Generic tests in `_staging.yml` and `_marts.yml`: `unique`, `not_null`, `accepted_values`, `relationships`.
- Singular tests in `tests/`:
  - `assert_transactions_not_in_future`
  - `assert_live_balance_reconciles` (available = ledger − pending)
  - `assert_fx_sources_agree` (severity warn: ECB vs Marketplace within 0.5 %)
- Source freshness on every source in `_sources.yml` (warn / error thresholds), run by task `T_20_DBT_FRESHNESS`.

## Macros

| Macro | Use |
|---|---|
| `generate_schema_name` | writes to `STAGING` / `INTERMEDIATE` / `MARTS` exactly |
| `mask_column` | post-hook that attaches a masking policy to a Gold column |
| `add_client_row_policy` | post-hook that attaches the row access policy to app views |
| `fraud_score` | rule-based score (amount, night, foreign country, velocity) |

Variables in `dbt_project.yml`: `fraud_score_threshold` (50), `held_tickers`, `fx_currencies`.
