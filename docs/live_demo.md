# Live demo and running order (oral defense, 15 minutes)

The talk lasts about **15 minutes with three speakers**: Adrien opens (slides 1–5), Thomas presents the
pipeline and runs every live demo (slides 6–10), Lélia closes with the cloud, the best case, the forecast and
the conclusion (slides 11–14). All demo queries are in
[`snowflake/11_demo_script.sql`](../snowflake/11_demo_script.sql), in order. The full speaking script is a
shared document (link in the team chat).

## Running order

The slides are in Canva (14 slides). The three diagrams on slides 5, 12 and 13 are the images in
[`docs/img/`](img/), drawn by [`make_slide_diagrams.py`](img/make_slide_diagrams.py).

**One running example, told three times:** Camille pays €12.40 for lunch at a bakery in Lyon. Adrien follows
the payment through today's pipeline (slide 5); Lélia follows the same payment through the best case
(slide 12) and through Databank in 2030 (slide 13), so the differences are clear.

| Time | Speaker | Slide | Live part |
|---|---|---|---|
| 0:00–0:40 | Adrien | 1 Title | |
| 0:40–1:10 | Adrien | 2 Agenda | |
| 1:10–2:00 | Adrien | 3 Databank at a glance | |
| 2:00–2:50 | Adrien | 4 Three use cases | |
| 2:50–4:10 | Adrien | 5 Architecture today | Camille's payment, today |
| 4:10–5:10 | Thomas | 6 Six sources, six ingestion methods | **Steps 1–2:** payments arriving now, then in Gold seconds later |
| 5:10–6:40 | Thomas | 7 Transform & serve | **Step 3:** dashboard (first client in the list), then *Pipeline health* |
| 6:40–7:30 | Thomas | 8 Proof it works | |
| 7:30–8:30 | Thomas | 9 Reliability (failing check, 2 incidents) | live **Step 5** only if ahead of time |
| 8:30–10:00 | Thomas | 10 Security & costs | **Step 4:** analyst sees masked names and is denied raw data; compliance sees them in clear |
| 10:00–11:00 | Lélia | 11 Cloud & IaC (Terraform, Docker, GitHub Actions) | |
| 11:00–12:40 | Lélia | 12 Best case | Camille's payment, best case |
| 12:40–14:20 | Lélia | 13 Forecast 2026 → 2030 | Camille's payment, 2027 → 2030 |
| 14:20–15:00 | Lélia | 14 Conclusion | |

## Before the defense

| When | What | Who |
|---|---|---|
| The day before | one full rehearsal with a timer; check every query of `11_demo_script.sql` runs | all three |
| T-15 min | log in to Snowflake and GitHub on the presenting laptop; open the demo tabs (below) | Thomas |
| T-10 min | GitHub → *Actions* → **A · Card terminals** → *Run workflow* (minutes = 20) | Thomas |
| T-10 min | run `snowflake/07_live_demo.sql` once (turns on live tables, schedule, simulator) | Thomas |
| T-5 min | open the dashboard once, so its container is already started | Thomas |
| T-2 min | run Step 1: the message count must be above 0 | Thomas |

**Tabs to have open, in this order:** the slides · GitHub *Actions* (stream running) · Snowflake
workspace with `11_demo_script.sql` · the dashboard · the GitHub repository README.

## The demo, step by step

| Step | Speaker | Do | Say | Expected |
|---|---|---|---|---|
| 1 | Thomas | run the Step 1 query | "These are card payments sent by a GitHub Actions job right now, every 10 seconds." | a few hundred messages in the last 5 minutes, last one a few seconds ago |
| 2 | Thomas | run the Step 2 query | "The same payments, de-duplicated and validated, already in Gold, a few seconds later." | the 10 latest payments, `seconds_since_payment` small, status `PENDING` |
| 4 | Thomas | run the Step 4 block | "Same table, two roles: the analyst sees masked data and cannot open raw data; compliance sees it in clear." | masked names / IBAN `FR76 ****`; then an *not authorized* error; then clear names |
| 3 | Thomas | open the dashboard (the first client has a portfolio and pending payments), click *Refresh*, then *Pipeline health* | "This is what the client app reads: balance minus pending payments, updated live." | pending payments listed; freshness green for card payments |
| 5 | Thomas | (optional) run the Step 5 block | "A payment dated 2030 is injected: the check fails, dbt stops what depends on it, the regulatory report keeps its last good version." | build fails with `ERROR=1`, downstream skipped; recovery run passes |

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
