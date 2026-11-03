# Live demo and running order (oral defense, 10 minutes)

The talk lasts about **10 minutes with three speakers**; the live demo is spread through it (about
3 minutes in total) so each speaker shows the part they own. All queries are in
[`snowflake/11_demo_script.sql`](../snowflake/11_demo_script.sql), in order.

## Running order

The slides are in Canva (14 slides); each slide's speaker notes repeat the speaker, the timing and what to say.
The three diagrams on slides 5, 12 and 13 are drawn by [`docs/img/make_slide_diagrams.py`](img/make_slide_diagrams.py).

| Time | Speaker | Slide | Live part |
|---|---|---|---|
| 0:00–0:40 | Thomas | 1 Title · 2 Agenda | |
| 0:40–1:05 | Thomas | 3 Databank at a glance | |
| 1:05–1:30 | Thomas | 4 Three use cases | |
| 1:30–2:20 | Thomas | 5 Architecture today | |
| 2:20–3:00 | Thomas | 6 Six sources, six ingestion methods | **Steps 1–2:** payments arriving now, then in Gold seconds later |
| 3:00–4:20 | Adrien | 7 Transform & serve | **Step 3:** dashboard, client C000042, pending payments, pipeline health |
| 4:20–4:55 | Adrien | 8 Proof it works | |
| 4:55–5:40 | Adrien | 9 Reliability (failing check, 2 incidents) | live **Step 5** only if time allows |
| 5:40–7:00 | Lélia | 10 Security & costs | **Step 4:** analyst sees masked names and is denied raw data; compliance sees them in clear |
| 7:00–7:50 | Lélia | 11 Cloud & IaC (Terraform, Docker, GitHub Actions) | |
| 7:50–8:40 | Lélia | 12 Best case (all the budget, best platforms) | |
| 8:40–9:30 | Lélia | 13 Forecast 2026 → 2030 (Gartner) | |
| 9:30–10:00 | Lélia | 14 Conclusion | |

## Before the defense

| When | What | Who |
|---|---|---|
| The day before | one full rehearsal with a timer; check every query of `11_demo_script.sql` runs | all three |
| T-15 min | log in to Snowflake and GitHub; open the demo tabs (below) | Thomas |
| T-10 min | GitHub → *Actions* → **A · Card terminals** → *Run workflow* (minutes = 20) | Thomas |
| T-10 min | run `snowflake/07_live_demo.sql` once (turns on live tables, schedule, simulator) | Lélia |
| T-5 min | open the dashboard once, so its container is already started | Adrien |
| T-2 min | run Step 1: the message count must be above 0 | Thomas |

**Tabs to have open, in this order:** the slides · GitHub *Actions* (stream running) · Snowflake
workspace with `11_demo_script.sql` · the dashboard · the GitHub repository README.

## The demo, step by step

| Step | Speaker | Do | Say | Expected |
|---|---|---|---|---|
| 1 | Thomas | run the Step 1 query | "These are card payments sent by a GitHub Actions job right now, every 10 seconds." | a few hundred messages in the last 5 minutes, last one a few seconds ago |
| 2 | Thomas | run the Step 2 query | "The same payments, de-duplicated and validated, already in Gold, a few seconds later." | the 10 latest payments, `seconds_since_payment` small, status `PENDING` |
| 4 | Lélia | run the Step 4 block | "Same table, two roles: the analyst sees masked data and cannot open raw data; compliance sees it in clear." | masked names / IBAN `FR76 ****`; then an *not authorized* error; then clear names |
| 3 | Adrien | open the dashboard, client C000042, click *Refresh*, then *Pipeline health* | "This is what the client app reads: balance minus pending payments, updated live." | pending payments listed; freshness green for card payments |
| 5 | Adrien | (optional) run the Step 5 block | "A payment dated 2030 is injected: the check fails, dbt stops what depends on it, the regulatory report keeps its last good version." | build fails with `ERROR=1`, downstream skipped; recovery run passes |

## If something goes wrong

| Problem | Backup |
|---|---|
| No Wi-Fi / Snowflake slow | show the backup screenshots in the slides; the same results are in [evidence.md](evidence.md) |
| Step 1 returns 0 | the stream is not running: show the GitHub run, re-start it; meanwhile show Step 2 (older payments) |
| Dashboard takes long to open | it starts a container (about 1 minute): go on with the slides and come back |
| A role error in Step 4 | run `USE SECONDARY ROLES NONE;` again before the query |

## Afterwards (stops all credit use)

1. GitHub: cancel the **A · Card terminals** run if it is still going.
2. Snowflake: run `snowflake/98_pause_all.sql`.
3. Snowflake: `ALTER COMPUTE POOL SYSTEM_COMPUTE_POOL_CPU STOP ALL;` (stops the dashboard container).
