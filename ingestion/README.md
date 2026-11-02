# `ingestion/`: the Python loaders (pillar 1 · Ingest)

This folder holds the code that brings **external** data into Snowflake. There is one folder per source;
the letter matches the architecture diagram.

| Folder | Source | Method | Lands in | Runs |
|---|---|---|---|---|
| [`a_tpe_stream/`](a_tpe_stream/producer.py) | A · Card terminals | micro-batch streaming (a batch every 10 s) | `RAW.TPE_AUTHORIZATIONS` | on demand, before a demo |
| [`d_ecb_api/`](d_ecb_api/ingest_ecb_fx.py) | D · ECB exchange rates (real) | REST API pull, incremental (watermark + MERGE) | `RAW.ECB_FX_RATES` | working days, 16:30 Paris |
| [`e_bdf_snowpipe/`](e_bdf_snowpipe/load_bdf_registry.py) | E · Banque de France files | CSV file → stage → Snowpipe | `RAW.BDF_REGISTRY` | working days, 07:00 Paris |
| [`f_app_events/`](f_app_events/load_app_events.py) | F · Mobile app events | gzip JSON file → stage → `COPY INTO` | `RAW.APP_EVENTS` | 3 times a day |
| [`common/`](common/snowflake_conn.py) | shared | Snowflake connection (key pair, or browser login for local runs) | | |

Sources **B** (core banking, CDC) and **C** (Marketplace share) have no Python code: they work entirely
inside Snowflake. See [`snowflake/01_core_banking.sql`](../snowflake/01_core_banking.sql) and
[`snowflake/03_marketplace_share.sql`](../snowflake/03_marketplace_share.sql).

## What every loader has in common

- **Written as code, run by a schedule**: no manual upload, no drag and drop. The schedules are in
  [`.github/workflows/`](../.github/workflows/).
- **Idempotent**: running a loader twice does not create duplicates (MERGE for the API, Snowflake's file
  load history for Snowpipe and `COPY INTO`).
- **Least privilege**: the loaders log in as the service user `SVC_DATABANK_INGEST`, whose role can only
  write to the landing tables. They can read card tokens and merchant ids, never client names or balances.
- **No secrets in the code**: the private key comes from a GitHub encrypted secret.
- **Lineage**: each row records where it came from (`SOURCE_FILE`, `BATCH_ID`, `RUN_ID`, load time).

## What is simulated, what is real

Sources A, E and F generate **fictive** data in the same format a real bank would receive, including
realistic defects so that the pipeline has something to clean: duplicated payments (network retries),
broken messages, unusual amounts. Source D calls the **real** public API of the European Central Bank.

## Run a loader on your own computer

```bash
pip install -r ingestion/requirements.txt
export SNOWFLAKE_ACCOUNT=xedwtqk-wk19730 SNOWFLAKE_USER=<your Snowflake user>   # opens a browser login
python -m ingestion.d_ecb_api.ingest_ecb_fx
python -m ingestion.a_tpe_stream.producer --minutes 5
```
