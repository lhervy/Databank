# Incident scenarios

Two realistic incidents, how the pipeline detects them, who acts, and how it recovers.
**Both were tested on 3 November 2026.** Incident 2 was observed for real: before the first ECB load the
feed was empty, exactly like an outage; the first load then caught up two years of rates. Results: [evidence.md](evidence.md).

---

## Incident 1 · A loader retries and sends the same payments twice (tested)

| | |
|---|---|
| **What happens** | the card loader times out and retries; the same 500 payments arrive a second time |
| **Risk** | double counting: balances too low, regulatory figures too high, every task still "green" (a silent failure) |
| **Detection** | the `unique` test on `transaction_id` in Gold; the reconciliation test on live balances |
| **Owner** | Thomas (ingestion); Adrien (transformation) if a test fails |
| **Why nothing breaks** | raw data is append-only and keeps the duplicates for audit; dbt keeps one row per `transaction_id` (the first received) |
| **Recovery** | nothing to do: the next run produces the same figures. If a test ever failed, dbt would stop the downstream models and Gold would keep its last good version |

**Test result:** raw messages went from 303,295 to 303,795, transactions in Gold stayed at 299,747, and the
Banque de France figure for 15 October stayed at €176,580.44. Logged as drill `replay` in
`OPS.EVIDENCE_LOG`.

**Related drill (a check that fails):** a payment dated 2030 was injected; `assert_transactions_not_in_future`
failed, dbt skipped the 13 dependent steps, the regulatory report kept its last good version; after removing
the row, the pipeline passed again (drill `future_payment`).

---

## Incident 2 · The ECB exchange-rate API is unavailable

| | |
|---|---|
| **What happens** | the ECB API does not answer (outage, network problem, or no rate published on a holiday) |
| **Risk** | portfolios valued with no exchange rate, or with an old one, without anyone noticing |
| **Detection** | the GitHub Actions run of loader D fails (red run, e-mail to the repository owner); `dbt source freshness` warns when the newest rate is more than 4 days old |
| **Owner** | Thomas (ingestion) |
| **Why nothing breaks** | `int_fx_rates_daily` uses the ECB rate first and the Snowflake Marketplace rate as fallback; each row says which source it used (`rate_source`) |
| **Recovery** | when the API is back, the next run reads the watermark (last date loaded) and fetches every missing day; MERGE on `(rate_date, currency)` means re-running never duplicates a rate |

**Test result (3 Nov, before the first ECB load):** the ECB table was empty, `dbt source freshness` returns **WARN** for
`ecb_api.ecb_fx_rates`, 100 % of rates come from the Marketplace fallback, and the 10,575 positions are
still valued (€259,871,013). Logged as drill `ecb_outage`.

**Recovery observed:** the first run of the ECB job (in its Docker container) read an empty watermark and
loaded every working day of the last two years at once: 2,036 rates for 4 currencies, 4 Nov 2024 to
2 Nov 2026. No manual step was needed.

---

## Incident report template (filled for incident 1)

| Field | Value |
|---|---|
| Date | 3 Nov 2026, drill |
| Detected by | dbt tests (`unique`, `assert_live_balance_reconciles`), reconciliation of the daily report |
| Impact | none on business figures; +500 rows in the raw layer |
| Root cause | loader retry without idempotent write at the source |
| Fix | none needed: de-duplication in staging, one row per `transaction_id` |
| Prevention | keep raw append-only, de-duplicate once in dbt, keep the reconciliation test in every build |
| Owner | Thomas (ingestion), Adrien (transformation) |
