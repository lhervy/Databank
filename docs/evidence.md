# Evidence: proof that the pipeline works

Every result below was produced in Snowflake on **3 November 2026** and logged in the table
`DATABANK.OPS.EVIDENCE_LOG`, so it can be re-checked at any time:

```sql
SELECT drill, step, metric, value, logged_at FROM DATABANK.OPS.EVIDENCE_LOG ORDER BY logged_at;
```

All of it ran on free trial credits; nothing was paid. To reproduce every check: [`snowflake/10_evidence_drills.sql`](../snowflake/10_evidence_drills.sql).

## 1. Business output verified against known data

The card-terminal simulator injects defects at **known rates**: about 1 % network retries (same payment
sent twice), 0.2 % broken amounts and 0.3 % unusually large payments. If the pipeline is right, it must find
exactly those proportions.

| Check | Expected | Measured | |
|---|---|---|---|
| Raw messages received | | 303,295 | |
| Duplicate messages removed (same `transaction_id`) | ≈ 1 % | 2,995 (0.99 %) | ✅ |
| Messages with an invalid amount, sent to quarantine | ≈ 0.2 % | 557 (0.18 %) | ✅ |
| Payments over €1,000 (fraud rule) | ≈ 0.3 % | 897 (0.30 %) | ✅ |
| Valid, unique transactions in Gold | 300,300 distinct ids − 553 invalid | 299,747 | ✅ |
| Duplicates left in Gold | 0 | 0 (299,747 rows = 299,747 distinct ids) | ✅ |
| Σ daily spending (UC2) = Σ authorized amount in the fact table | equal | €15,172,571 = €15,172,571 | ✅ |

**Independent recomputation.** The Banque de France figures for 15 October 2026 were recomputed directly
from the raw JSON messages (a separate SQL path that does not use dbt) and compared with the Gold report:

| | Payments | Authorized amount |
|---|---|---|
| Recomputed from `RAW.TPE_AUTHORIZATIONS` | 3,333 | €176,580.44 |
| Gold `MARTS.REG_BDF_DAILY_REPORT` | 3,333 | €176,580.44 |

## 2. Access control: allowed and denied

Each test ran with `USE SECONDARY ROLES NONE`, so only the tested role's own permissions applied.

| Role | Query | Expected | Result |
|---|---|---|---|
| `DATABANK_ANALYST` | read `MARTS.DIM_CLIENTS` | allowed, personal data masked | ✅ 10,000 rows; names `*** masked ***`, IBAN `FR76 **** **** **** 5082`, birth date reduced to the year |
| `DATABANK_ANALYST` | read `RAW.TPE_AUTHORIZATIONS` | **denied** | ✅ `Schema 'DATABANK.RAW' does not exist or not authorized` |
| `DATABANK_COMPLIANCE` | read `MARTS.DIM_CLIENTS` | allowed, data in clear | ✅ real (fictive) names and IBANs visible |
| `DATABANK_CLIENT_APP` | read `MARTS.APP_MY_TRANSACTIONS` | only the logged-in client | ✅ 29 rows, all for client `C000042` |
| `DATABANK_CLIENT_APP` | read `MARTS.FCT_CARD_TRANSACTIONS` | **denied** | ✅ `Object … does not exist or not authorized` |

## 3. A check that fails, and blocks bad data

Drill `future_payment`: a payment dated 1 January 2030 (clock or parsing bug) was injected into the raw
layer, then the pipeline was run.

| Step | Result |
|---|---|
| dbt build after the injection | **PASS 8, ERROR 1, SKIP 13**: the test `assert_transactions_not_in_future` found 1 bad row, and dbt skipped the 13 models and tests that depend on it |
| Gold reports during the failure | unchanged: last date still 29 Oct 2026, the 2030 payment never reached the regulatory report |
| Recovery: bad row deleted, pipeline re-run | **PASS 22, ERROR 0**; 299,747 transactions, 0 in the future |

**Honest limitation:** the live dynamic table `FCT_CARD_TRANSACTIONS` did contain the bad row for a few
minutes, because it refreshes before the tests run. The protection works for every table built after it
(daily spend, regulatory report, AML). Production fix: filter impossible dates in the staging model, before
the live table.

## 4. Replay without double counting

Drill `replay`: 500 messages that had already been loaded were sent again (what happens when a loader
retries after a timeout).

| | Before | After |
|---|---|---|
| Raw messages | 303,295 | 303,795 (+500) |
| Transactions in Gold | 299,747 | 299,747 |
| Authorized amount, Banque de France report, 15 Oct 2026 | €176,580.44 | €176,580.44 |

The duplicates stay in the raw layer, where they are kept for audit. They are removed once, in dbt (one row
per `transaction_id`), so a replay never changes a business figure.

## 5. Freshness and a source outage

Drill `ecb_outage`: the ECB API feed (source D) has no data yet, which behaves exactly like an outage.

| Check | Result |
|---|---|
| `dbt source freshness` | ⚠️ WARN on `ecb_api.ecb_fx_rates` (also on app events, Banque de France and CDC, not refreshed since 29 Oct); PASS on card payments |
| Exchange rates used | 100 % from the Marketplace fallback (38,616 daily rates, `rate_source = 'MARKETPLACE'`) |
| Portfolio valuation | still computed: €259,871,013 for 10,575 positions |

The pipeline keeps serving correct figures, and the freshness check tells the owner that a source is late.

## 6. Scheduling and run history

| What | Where to see it |
|---|---|
| Task graph `T_00_ROOT → T_10_DBT_BUILD → T_20_DBT_FRESHNESS` | ran end to end with all three tasks **SUCCEEDED** (1 Nov 2026); Snowsight → Transformation → Tasks |
| dbt full build | 32 models + 43 tests: PASS 75, ERROR 0 (1 Nov 2026) |
| Dynamic table refreshes | `INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY()`: last refresh SUCCEEDED (3 Nov 2026) |
| GitHub Actions runs (loaders, Docker job, Terraform) | *Actions* tab of the repository, once the key is set up |

## 7. Not proven yet

| Item | Why | Next step |
|---|---|---|
| Loaders A, D, E, F running from GitHub Actions | the GitHub ↔ Snowflake key is not set up yet | add the key ([setup_github_actions.md](setup_github_actions.md)), run the workflows |
| Containerised job run in the cloud | same reason; the image is built and checked by CI on every change | run *D · ECB FX rates* once the key exists |
| Terraform `apply` | same reason; `fmt` and `validate` run in CI | run the *Terraform* workflow with `plan`, then `apply` |
