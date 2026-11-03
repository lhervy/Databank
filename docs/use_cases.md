# Use cases: decisions, metrics and acceptance tests

Databank's platform serves **three use cases**. For each one: the decision it supports and who makes it,
the exact metric (grain, formula, exclusions), why it is refreshed at that frequency, and the test that
proves it is right. Every figure below was measured in Snowflake (period 31 Jul – 29 Oct 2026, 91 days,
10,000 clients).

---

## UC1 · Live card payments and available balance

| | |
|---|---|
| **Decision** | "Can I afford this?": the client decides whether to spend; support agents answer "why was my card declined?" |
| **User** | the client in the mobile app; customer support |
| **Served by** | `MARTS.ACCOUNT_LIVE_BALANCE` (dynamic table) → secure view `MARTS.APP_MY_BALANCE` |

**Metric: available balance**

| | Definition |
|---|---|
| Grain | one row per **current account** (10,000 rows) |
| Formula | `available_balance_eur = ledger_balance_eur − Σ amount_eur` of pending card payments |
| Pending payment | a card payment with `status = 'AUTHORIZED'` and `event_ts > balance_as_of` (not yet booked by the core banking system) |
| Exclusions | declined payments · duplicate messages (same `transaction_id`, first one kept) · quarantined messages (invalid amount, timestamp, unknown card or merchant) · payments already booked · investment accounts |
| Source of truth | the booked balance comes only from the core banking system (CDC, source B); Databank never recalculates it |

**Frequency: at most 1 minute behind.** A client checks the balance right after paying; if the payment is
not there, they think they have more money than they do. The dynamic table has a 1-minute target lag;
1 second would require a separate operational database (see [target_architecture.md](target_architecture.md)).

**Acceptance tests**

| Test | Expected | Result |
|---|---|---|
| `assert_live_balance_reconciles`: available = ledger − pending, for every account | 0 rows | ✅ passes on every build |
| `account_id` unique and not null | 0 failures | ✅ |
| A payment streamed during the demo appears in the app view | within 2 minutes | to be shown live (needs the GitHub key) |
| A client only sees their own balance (row access policy) | 1 client | ✅ 29 rows, all for client C000042 ([evidence.md](evidence.md)) |

---

## UC2 · Personal spending dashboard and portfolio

| | |
|---|---|
| **Decision** | the client adjusts their budget by category; an advisor decides whether to propose a Premium plan or an investment product |
| **User** | the client; the customer advisor |
| **Served by** | `MARTS.CLIENT_DAILY_SPEND`, `MARTS.PORTFOLIO_VALUATION` → Streamlit dashboard and `APP_MY_SPEND`, `APP_MY_PORTFOLIO` |

**Metric 1: spending**

| | Definition |
|---|---|
| Grain | one row per **client × day × merchant category** |
| Formula | `spend_eur = Σ amount_eur` of card payments with `status = 'AUTHORIZED'` |
| Day | `event_date` = date of the payment in UTC |
| Exclusions | declined payments · duplicates · quarantined messages |

**Metric 2: portfolio value**

| | Definition |
|---|---|
| Grain | one row per **investment position** (account × share) |
| Formula | `market_value_eur = quantity × last close_usd ÷ EUR/USD rate` |
| Price | latest daily close of the share (Snowflake Marketplace, real data) |
| Exchange rate | latest EUR/USD rate: ECB API first, Marketplace as fallback |
| Exclusions | shares without a price (none today) |

**Frequency.** Spending: **every 15 minutes** (task graph); clients look at budgets a few times a day.
Portfolio: **daily**; prices are daily closes, so refreshing more often would cost credits for no change.

**Acceptance tests**

| Test | Expected | Result |
|---|---|---|
| Σ spending over all clients, days and categories = Σ authorized amount in `FCT_CARD_TRANSACTIONS` | equal | ✅ €15,172,571 = €15,172,571 |
| Every position has a price and a rate | 10,575 positions valued | ✅ 10,575 positions, 3,483 clients |
| ECB and Marketplace rates agree within 0.5 % on common days (`assert_fx_sources_agree`, warning) | 0 rows | ✅ (no common days yet: ECB feed not loaded) |

---

## UC3 · Regulatory reporting and anti-money laundering

| | |
|---|---|
| **Decision** | the compliance officer decides whether to file a suspicious-activity declaration with Tracfin or block a card; the bank submits its daily card figures to the Banque de France |
| **User** | compliance officer, head of risk, Banque de France |
| **Served by** | `MARTS.REG_BDF_DAILY_REPORT`, `MARTS.AML_ALERTS`, `MARTS.CREDIT_RISK_WATCHLIST` |

**Metric 1: daily regulatory figures**

| | Definition |
|---|---|
| Grain | one row per **calendar day** (`event_date`, UTC) |
| Formulas | `n_transactions` = count of valid payments (authorized + declined) · `authorized_amount_eur` = Σ amount where authorized · `cross_border_amount_eur` = same, where `country ≠ 'FR'` · `n_suspicious` = count where fraud score ≥ 50 · `n_active_clients` = distinct clients |
| Exclusions | duplicates · quarantined messages |

**Metric 2: fraud score (rule-based)**

`fraud_score = min(100, 50 if amount > €1,000 + 30 if paid abroad + 20 if between 01:00 and 05:00 UTC)`;
a payment is **suspicious** when the score is ≥ 50 (variable `fraud_score_threshold` in `dbt_project.yml`).
Defined once, in the dbt macro `fraud_score`.

**Frequency: daily.** The Banque de France works with daily figures and the compliance review target is
24 hours. A faster refresh would not change any decision.

**Acceptance tests**

| Test | Expected | Result |
|---|---|---|
| `event_date` unique and not null | 0 failures | ✅ 91 days, one row each |
| Independent recomputation from the raw JSON for 15 Oct 2026 = Gold report | equal | ✅ 3,333 payments, €176,580.44 in both ([evidence.md](evidence.md)) |
| Every AML alert has a score ≥ 50 | 0 rows below | ✅ by construction (`where is_suspicious`) |
| Names in AML alerts visible to compliance only | masked for analysts | ✅ ([evidence.md](evidence.md)) |

**Known limitation:** the rule-based score flags 3,880 payments (1.3 %), many of them false positives
(any payment over €1,000). In the target architecture it is replaced by a machine-learning model scoring
before the payment is accepted.
