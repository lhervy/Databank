# `streamlit/`: the dashboard (pillar 3 · Consume)

[`streamlit_app.py`](streamlit_app.py) is a dashboard that runs inside Snowflake (Streamlit in Snowflake).
It reads **only Gold tables** (`MARTS`) and monitoring views (`OPS`), never raw data.

| Tab | What it shows | Use case |
|---|---|---|
| **Client view** | 4 key-figure cards (available balance, pending card payments, portfolio value, fraud alerts), latest payments, spending by category, portfolio ring chart | UC1 (live balance), UC2 (spending and portfolio) |
| **Markets** | real share prices of the stocks clients hold (1 year), EUR/USD from the ECB API and the Marketplace on one chart | UC2 (reliable market data) |
| **Pipeline health** | one card per source with its status (Fresh / Late / Stale), quarantined messages, ingestion delay in the last hour | monitoring ("who fixes it at 3 a.m.?"), UC3 |

**Look and feel:** same colours as the presentation (greens, Poppins), set in the app's CSS and in
[`.streamlit/config.toml`](.streamlit/config.toml) (light theme). The client list starts with a client who
has a portfolio and pending payments, so every chart has data during the demo.

## How to open it

In Snowflake: *Projects → Workspaces → Databank_Team → Databank Dashboard → streamlit_app.py → Run*.

It runs as a **container** on a Snowflake compute pool and queries the warehouse `DATABANK_WH`.

> **Cost note:** once opened, the dashboard's container keeps running for up to 3 days if nobody stops it
> (about 2.7 credits a day). Stop it after the demo: see [docs/runbook.md](../docs/runbook.md#costs).
