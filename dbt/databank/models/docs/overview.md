{% docs __overview__ %}
# Databank · data platform

Fictive French bank on **Snowflake (AWS, Paris region)**. This dbt project builds the
**Silver** (staging, intermediate) and **Gold** (marts) layers from six sources:

| | Source | Ingestion method |
|---|---|---|
| A | Card terminals (TPE) | micro-batch streaming (Python producer) |
| B | Core banking system | CDC with Snowflake streams + task |
| C | Market data (Nasdaq, FX) | Snowflake Marketplace secure share (real data) |
| D | ECB exchange-rate API | REST API pull, incremental (GitHub Actions) |
| E | Banque de France files | Snowpipe from a stage (REST-triggered) |
| F | Mobile app events | batch COPY INTO from a stage |

Live models (`fct_card_transactions`, `account_live_balance`) are **dynamic tables**
refreshed every minute; everything else is rebuilt by the task graph every 15 minutes.

Open the **lineage graph** (bottom right) to see the full DAG from sources to marts.
{% enddocs %}
