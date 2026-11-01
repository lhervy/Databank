# Architecture and data flow

![Architecture](img/architecture.png)

One cloud (**AWS**, region `eu-west-3` Paris). Snowflake runs on AWS; the loaders run on GitHub Actions
runners and push into Snowflake over HTTPS with key-pair authentication. No service outside AWS stores data.

## Sources (letters)

| | Source | Owner |
|---|---|---|
| A | Card payment terminals (TPE) | merchant acquirer network |
| B | Core banking OLTP (clients, accounts, positions) | Databank IT |
| C | Snowflake Marketplace: Nasdaq prices, FX | Snowflake (provider) |
| D | ECB Data Portal REST API: euro reference rates | European Central Bank |
| E | Banque de France registry extracts (CSV) | Banque de France |
| F | Mobile app backend events (JSON lines) | Databank digital team |

## Steps (numbers)

| # | Step | Technology | Lands in / produces |
|---|---|---|---|
| 1 | Micro-batch streaming of card authorizations | Python producer (`ingestion/a_tpe_stream`) | `RAW.TPE_AUTHORIZATIONS` |
| 2 | Change data capture of the core banking tables | Snowflake streams + `CAPTURE_CHANGES` procedure | `RAW.CORE_BANKING_CHANGES` |
| 3 | Secure data share | Snowflake Marketplace, zero-copy | `SNOWFLAKE_CURATED_DATA_FREE` |
| 4 | Incremental REST pull | GitHub Actions + Python, watermark + MERGE | `RAW.ECB_FX_RATES` |
| 5 | File load with Snowpipe | PUT on internal stage + Snowpipe REST `insertFiles` | `RAW.BDF_REGISTRY` |
| 6 | Batch file load | PUT + `COPY INTO` (S3 auto-ingest option) | `RAW.APP_EVENTS` |
| 7 | Transform Bronze → Silver → Gold, test, document | dbt Project on Snowflake, task graph every 15 min | `STAGING`, `INTERMEDIATE`, `MARTS` |
| 8 | Live path | dynamic tables, 1-minute target lag | `MARTS.FCT_CARD_TRANSACTIONS`, `MARTS.ACCOUNT_LIVE_BALANCE` |
| 9 | Governance and serving | masking policies, row access policy, roles, secure views | app, analysts, compliance, regulators |

## Orchestration

```
DBT.T_00_ROOT           every 15 min   CALL CORE_BANKING.CAPTURE_CHANGES()      (step 2)
 └── DBT.T_10_DBT_BUILD  after root     EXECUTE DBT PROJECT ... ARGS='build'     (step 7: run + test)
      └── DBT.T_20_DBT_FRESHNESS        EXECUTE DBT PROJECT ... 'source freshness'
```

GitHub Actions schedules (UTC): ECB rates weekdays 15:30, BdF file weekdays 06:00, app events 05:00 / 11:00 / 17:00.
The card stream is started on demand (`workflow_dispatch`) for demos. Dynamic tables refresh on their own.

## Consumers

| Consumer | Role | Reads |
|---|---|---|
| Mobile app (client) | `DATABANK_CLIENT_APP` | secure views `MARTS.APP_MY_*` filtered to the logged-in client |
| Analysts / dashboards | `DATABANK_ANALYST` | `MARTS` with personal data masked |
| Compliance / AML | `DATABANK_COMPLIANCE` | `MARTS` unmasked, `AML_ALERTS`, `CREDIT_RISK_WATCHLIST` |
| Banque de France / State | export from `REG_BDF_DAILY_REPORT` | aggregated daily report |
| Data team | `DATABANK_ENGINEER` | everything, via dbt |

## Design choices

- **ELT, not ETL**: raw data lands untouched (JSON kept as text or VARIANT), so it can be replayed. Cleaning
  happens in dbt, versioned in git.
- **Bad data is quarantined, not dropped**: broken card messages go to `MARTS.DQ_REJECTED_AUTHORIZATIONS`.
- **Two sources for FX** (C and D) are compared every day (`int_fx_rates_daily.source_diff_pct`, test
  `assert_fx_sources_agree`).
- **Workload isolation**: `DATABANK_INGEST_WH` for loaders, `DATABANK_WH` for dbt and dashboards, both
  XSMALL with 60 s auto-suspend, capped by resource monitor `DATABANK_RM`.
