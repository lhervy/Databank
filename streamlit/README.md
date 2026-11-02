# `streamlit/`: the dashboard (pillar 3 · Consume)

[`streamlit_app.py`](streamlit_app.py) is a dashboard that runs inside Snowflake (Streamlit in Snowflake).
It reads **only Gold tables** (`MARTS`) and monitoring views (`OPS`), never raw data.

| Tab | What it shows | Use case |
|---|---|---|
| **Client view** | a client's available balance, pending card payments, latest payments, spending by category, portfolio value | 1 (live payments), 2 (investments), 3 (personal dashboard) |
| **Markets** | real stock prices of the shares clients hold; EUR/USD from two independent sources | 2 (reliable market data) |
| **Pipeline health** | freshness of each source, quarantined messages, ingestion delay | monitoring ("who fixes it at 3 a.m.?") |

## How to open it

In Snowflake: *Projects → Workspaces → Databank_Team → Databank Dashboard → streamlit_app.py → Run*.

It runs as a **container** on a Snowflake compute pool and queries the warehouse `DATABANK_WH`.

> **Cost note:** once opened, the dashboard's container keeps running for up to 3 days if nobody stops it
> (about 2.7 credits a day). Stop it after the demo: see [docs/runbook.md](../docs/runbook.md#costs).
