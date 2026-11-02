# Sources and ingestion methods

Six sources, six different ingestion methods. Letters and numbers match the architecture diagram.

| | Source | Real / simulated | Format | Volume | Method (step) | Frequency | Lands in |
|---|---|---|---|---|---|---|---|
| A | Card terminals (TPE) | simulated | JSON messages | ~5 msg/s during demos, 300k history | micro-batch streaming (1) | every 10 s, on demand | `RAW.TPE_AUTHORIZATIONS` |
| B | Core banking OLTP | simulated | relational rows | 10k clients, 13.6k accounts | CDC: streams + task (2) | every 15 min | `RAW.CORE_BANKING_CHANGES` |
| C | Snowflake Marketplace | **real** | shared tables | Nasdaq prices, FX history | secure data share (3) | provider-managed | `SNOWFLAKE_CURATED_DATA_FREE` |
| D | ECB Data Portal API | **real** | CSV over HTTPS | 4 currencies × working days | REST pull, incremental (4) | daily 16:30 Paris | `RAW.ECB_FX_RATES` |
| E | Banque de France | simulated | CSV files `;` | 200 lines full, ~15 delta | PUT + Snowpipe (5) | daily 07:00 Paris | `RAW.BDF_REGISTRY` |
| F | Mobile app backend | simulated | gzip JSON lines | ~12k events / run | PUT + COPY INTO (6) | 3× a day | `RAW.APP_EVENTS` |

## The ingestion types from the course, and where each one is used

| Type (course) | What it means | Databank source |
|---|---|---|
| Batch | load a whole file or table on a schedule | F · app events (3 times a day) |
| Incremental | load only what is new since the last run (watermark) | D · ECB API |
| Micro-batch | very small batches, very often | A · card terminals (every 10 s) |
| CDC | copy only the changes of an operational database | B · core banking |
| Streaming | continuous flow of single records | A in production (Kafka / Snowpipe Streaming) |
| File + Snowpipe | serverless load as soon as a file arrives | E · Banque de France |
| Data sharing | read another account's data without copying it | C · Marketplace |

All six methods are **idempotent**: running them twice does not create duplicates.

| Source | What prevents duplicates |
|---|---|
| A | dbt keeps one row per `transaction_id` (network retries are removed) |
| B | a stream returns each change only once; the capture runs in one transaction |
| C | nothing is loaded |
| D | MERGE on `(rate_date, currency)` + watermark |
| E | Snowpipe remembers every file it loaded |
| F | `COPY INTO` remembers every file loaded in the last 64 days |

## How each method works

**A · Micro-batch streaming.** `producer.py` sends a batch of authorization messages every 10 seconds
(`executemany` into `RAW.TPE_AUTHORIZATIONS`). It reads card tokens and merchant ids from two narrow views,
never client identities. Defects are injected on purpose: ~1 % duplicates (network retries), ~0.2 % broken
messages, ~0.3 % unusual amounts. In production: Kafka + Snowflake Kafka connector / Snowpipe Streaming.

**B · CDC (change data capture).** Snowflake streams on `CORE_BANKING.CLIENTS`, `ACCOUNTS` and `POSITIONS`
record every insert, update and delete. The capture procedure drains the three streams in one transaction
into an append-only change log. dbt rebuilds an SCD type 2 client history from it (`int_client_history`).

**C · Secure data sharing.** The free *Snowflake Curated Data* listing appears as a read-only database. No
copy, no pipeline, no storage cost; the provider keeps it updated (3-month lag on the free tier).

**D · REST API, incremental.** The loader reads the watermark (`MAX(rate_date)`), calls the ECB API only for
later days, and MERGEs on `(rate_date, currency)`. Re-running loads nothing new and updates nothing: idempotent.
The ECB answers HTTP 404 when no new rate is published (weekends, holidays): handled as "nothing to load".

**E · Snowpipe.** The loader writes the day's CSV, `PUT`s it on the encrypted internal stage `INGEST.STG_BDF`,
then calls the Snowpipe REST endpoint `insertFiles` (key-pair JWT). Snowflake loads it with serverless
compute and keeps a load history, so a file is never loaded twice. With an S3 bucket the same pipe would use
`AUTO_INGEST = TRUE` (S3 event notification) - optional block in `02_raw_landing.sql`.

**F · Batch COPY INTO.** The loader exports events to a gzip JSON-lines file, `PUT`s it under a
`yyyy/mm/dd/` prefix of `INGEST.STG_APP_EVENTS` and runs `COPY INTO`. Snowflake remembers loaded files for
64 days: a re-run loads 0 files. `--target s3` sends the file to S3 instead, for the auto-ingest pipe.

## Batch vs streaming: which latency, and why

| Use case | Needs | Our choice |
|---|---|---|
| Live balance in the app | minutes, not hours | micro-batch (A) + dynamic tables, 1-min lag |
| Client dashboards | 15 min | task DAG every 15 min |
| Investments | daily close | Marketplace (C) + ECB (D), daily |
| Regulators | daily | daily files (E), daily marts |

Streaming everything would multiply cost without business value.
