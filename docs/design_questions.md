# Design questions: how the architecture answers them

In class we were told to be ready to defend the architecture on six questions. This page answers each one,
then covers the topics flagged after the mid-term (formats, schema, serverless, pruning).

## 1. Latency: what does the business really need?

| Need | Required freshness | What we built | Why not faster |
|---|---|---|---|
| See a card payment in the app | ~1 minute | micro-batches every 10 s + dynamic tables with a 1-minute lag | a client does not notice the difference between 1 s and 60 s for a "pending" line |
| Personal dashboards | 15 minutes | task graph every 15 minutes | people check budgets a few times a day |
| Portfolio value | daily | market close prices + ECB daily rate | the ECB publishes once a day, and the free Marketplace data is daily |
| Regulatory reports | daily | daily files and daily marts | the Banque de France works with daily figures |

**Rule we applied:** stream only what must be live. Streaming everything would keep compute running all
day and multiply the cost with no business value.

**What about true real-time (sub-second)?** Tools such as ClickHouse are built for live dashboards and huge
streams of logs or IoT events where data is only appended. Databank's live need is one screen (the
pending payments), not a real-time analytics product, so a 1-minute lag inside Snowflake is enough. If the
bank wanted instant balances, we would add a small operational store (for example DynamoDB or Snowflake
Hybrid Tables) in front of the app, fed by the same stream, and keep Snowflake for analytics.

## 2. Scaling: can it grow?

| What grows | How the platform copes |
|---|---|
| More data | Snowflake separates storage from compute: storage grows without changing anything; a bigger warehouse (scale **up**) speeds up heavy queries |
| More users at the same time | a multi-cluster warehouse adds clusters automatically (scale **out**) |
| More workloads | each workload gets its own warehouse (scale **across**): loaders use `DATABANK_INGEST_WH`, dbt and dashboards use `DATABANK_WH` |
| More sources | a new source = one new loader folder + one staging model; nothing else changes |
| More card payments | in production the micro-batch producer is replaced by Kafka + Snowpipe Streaming, which is built for that volume |

## 3. Ownership: who fixes a broken arrow at 3 a.m.?

Each part of the pipeline has one owner (see the team table in the [README](../README.md#8-team-and-ownership)).
The tools help the owner find the problem quickly:

| If this breaks… | You see it in… | Owner |
|---|---|---|
| A loader (A, D, E, F) | the red run in GitHub Actions + `OPS.SOURCE_FRESHNESS` | Ingestion |
| A file load | `OPS.FILE_LOADS` (file name, rows, first error) | Ingestion |
| CDC capture | task `T_00_ROOT` in task history | Core banking & governance |
| A dbt model or test | task `T_10_DBT_BUILD`, dbt output | Transformation & serving |
| A late source | task `T_20_DBT_FRESHNESS` warns | whoever owns that source |

We did **not** use a data mesh (each business domain owning its own data). The course notes that a mesh fits
large organisations with many domains; a small bank with one data team is better served by one shared
platform with clear owners.

## 4. Single source of truth: is each number computed in one place only?

| Number | Computed only in |
|---|---|
| Booked balance of an account | the core banking system (source B), copied by CDC, never recalculated |
| Live (available) balance | `MARTS.ACCOUNT_LIVE_BALANCE` = booked balance − pending card payments |
| Fraud score | the dbt macro `fraud_score`, used by every model that needs it |
| EUR exchange rate | `INTERMEDIATE.INT_FX_RATES_DAILY`: ECB API first, Marketplace as fallback |

A dbt test (`assert_live_balance_reconciles`) checks on every run that the live balance really equals
"booked minus pending". The app reads secure views on top of Gold, never its own copy.

## 5. Cost driver: storage, compute or data transfer?

**Compute is the cost driver.** Storage is under 1 GB (pennies per month) and there is no transfer
between clouds because everything is on AWS Paris.

| How we keep compute low | |
|---|---|
| A budget before any query | resource monitor: 20 credits per month, warehouses suspend at 100 % |
| Small warehouses | XSMALL, suspend after 60 seconds of inactivity |
| Workload isolation | two warehouses, so the cost of each workload is visible separately |
| No streaming by default | the live parts run only during demos (`07_live_demo.sql` / `98_pause_all.sql`) |
| Serverless where it is cheaper | Snowpipe for files, no warehouse kept running |

Measured cost and per-action estimates: [runbook.md](runbook.md#costs).

## 6. Security: where is personal data, and who can see it?

| Personal data | Where | Who sees it in clear |
|---|---|---|
| Name, email, IBAN, birth date | `CORE_BANKING.CLIENTS`, `MARTS.DIM_CLIENTS` | Compliance only (and the pipeline owner role that builds the tables) |
| The same fields inside the change log | `RAW.CORE_BANKING_CHANGES` (JSON) | Compliance only (and the pipeline owner role); the fields are removed from the JSON for everyone else |
| Card numbers | **nowhere**: terminals send a token, never the card number | nobody |
| A client's own transactions | `MARTS.APP_MY_*` views | that client only (row access policy) |

Full details: [security.md](security.md).

## 7. File formats: CSV, JSON, Parquet

| Source | Format received | Why |
|---|---|---|
| E · Banque de France | CSV (`;` separated) | regulators and partners exchange simple flat files |
| F · App events | JSON lines, compressed (gzip) | app logs are semi-structured and change often |
| A · Card terminals | JSON messages | the standard format of payment messages |

**Parquet** is a columnar, compressed format: it is smaller than CSV and much faster to query because a
query reads only the columns it needs. We do not keep files as the long-term store: once loaded, Snowflake
stores every table in its own compressed columnar format (micro-partitions), which gives the same
advantages as Parquet. If the platform moved to a lakehouse (files on S3 queried by several engines), we
would write Bronze as **Parquet / Iceberg** tables.

## 8. Schema on read or on write?

**Both, on purpose, depending on the layer:**

- **Bronze is schema on read.** Card messages are stored as raw text and app events as `VARIANT` (JSON).
  We do not reject anything on arrival; the structure is applied when the data is read. This is why a broken
  message never stops the pipeline.
- **Silver and Gold are schema on write.** dbt casts every field to a fixed type and name, and tests
  enforce the rules (unique ids, accepted values, no future dates). Consumers always get a stable schema.

## 9. Serverless features we use

| Feature | What it does for us |
|---|---|
| Snowpipe | loads Banque de France files with compute managed by Snowflake: no warehouse to start |
| Secure data sharing | market data is available without any loading job or storage cost |
| Auto-suspend / auto-resume | warehouses exist only while a query runs |
| Dynamic tables | Snowflake decides when to refresh to meet the 1-minute target; no scheduler to write |
| dbt Projects on Snowflake | dbt runs inside Snowflake: no server or container to maintain |
| GitHub Actions | the loaders run on machines that exist only for the duration of the job |

## 10. Performance: pruning and pre-computation

- **Pruning** means Snowflake skips the micro-partitions that cannot contain the rows a query asks for.
  It works when queries filter on a column that follows the order in which data arrives. Our payments
  arrive in time order, and the dashboard always filters on dates (`event_date`, `price_date`), so old
  partitions are skipped. At this volume (300,000 rows) no explicit clustering key is needed; on billions
  of rows we would cluster `FCT_CARD_TRANSACTIONS` by `event_date`.
- **Pre-computation:** "the fastest query is the one you don't run". Gold tables and dynamic tables hold
  the answers in advance, so the app and dashboards read small, ready tables instead of scanning Bronze.
