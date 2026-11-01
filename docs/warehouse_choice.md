# Why Snowflake on AWS (architecture decision record)

**Decision:** AWS is the single cloud; Snowflake (hosted on AWS, region `eu-west-3` Paris) is the data
warehouse; dbt runs inside Snowflake; GitHub Actions runs the loaders.
**Status:** accepted · **Date:** November 2026

## What the bank needs

| Need | Why it matters for Databank |
|---|---|
| Data residency in France / EU | GDPR, ACPR supervision, DORA |
| Semi-structured data | card messages and app events are JSON |
| Near-real-time and batch on one platform | live balances (minutes) and regulatory reports (daily) |
| Strong governance | masking of personal data, row-level access for the app, audit |
| External data without pipelines | market data and FX rates |
| Low operations for a small team | no clusters to size, patch or vacuum |
| Cost control | pay for compute only when it runs |

## Options compared

| Criterion | **Snowflake on AWS** | Amazon Redshift (Serverless) | Google BigQuery | Databricks on AWS |
|---|---|---|---|---|
| Single cloud = AWS | ✅ runs on AWS Paris | ✅ native | ❌ GCP (breaks the 1-cloud rule) | ✅ |
| Storage / compute separation | ✅ per-workload warehouses | ⚠️ RPU-based, less isolation | ✅ slots | ✅ clusters |
| JSON (VARIANT) | ✅ native, schema-on-read | ⚠️ SUPER type, more limited | ✅ JSON type | ✅ |
| Streaming + CDC built in | ✅ Snowpipe, streams, tasks, dynamic tables | ⚠️ streaming ingestion from Kinesis/MSK | ✅ | ✅ Delta Live Tables |
| Data sharing / marketplace | ✅ zero-copy share, Marketplace (used for source C) | ⚠️ data sharing, smaller marketplace | ✅ Analytics Hub | ✅ Delta Sharing |
| Governance (masking, row access) | ✅ policies on columns and rows | ✅ (dynamic data masking, RLS) | ✅ | ✅ Unity Catalog |
| dbt | ✅ dbt Projects run natively | ✅ via dbt Cloud / core | ✅ | ✅ |
| Operations | ✅ near-zero | ⚠️ workgroups, vacuum/analyze on provisioned | ✅ near-zero | ⚠️ cluster management |
| Course alignment | ✅ used in TD 2 | — | used in TD 1.2 | — |

## Why not the others

- **BigQuery** is excellent and serverless, but it is a GCP service: using it means a second cloud (AWS for
  everything else), so it fails the "one cloud" requirement. Our Google credits are not needed.
- **Redshift** is the AWS-native choice. We would choose it if everything had to stay inside AWS services.
  Snowflake wins for us on semi-structured data, zero-copy sharing (our market-data source works with no
  pipeline), and workload isolation with no tuning.
- **Databricks** fits ML-heavy and lakehouse-first teams. Databank is SQL-first with a small team; a
  warehouse with less to operate is the better fit.

## Consequences

- Two warehouses (`DATABANK_INGEST_WH`, `DATABANK_WH`) isolate ingestion from transformation, so the cost
  driver per workload is visible (see `snowflake/08_monitoring.sql`).
- Trial accounts block outbound network calls from Snowflake (external access), so API and file loaders
  run in GitHub Actions and push into Snowflake with key-pair authentication. This is also the usual
  production pattern.
- The live path inside Snowflake reaches about 1 minute (dynamic table lag). A sub-second app experience
  would add an operational store (e.g. DynamoDB or Snowflake Hybrid Tables) in front: see the deck.
