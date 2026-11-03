# The company: Databank

Databank is a **fictive** French mobile bank. Everything below is invented for the project, but every
number is either measured in our Snowflake data or stated as an explicit assumption (marked **A1, A2…**),
so it can be checked or challenged.

## 1. Who the customers are and how Databank earns money

**Customers:** individuals in France who manage their everyday money and their savings from a mobile app.
They get a current account with a debit card, and can open an investment account (shares).

| Segment | Share of clients (measured) | What they pay (assumption) |
|---|---|---|
| Retail | 80 % (8,003 of 10,000) | free plan |
| Premium | 17 % (1,735) | €7.99 per month (**A1**) |
| Private | 3 % (262) | €24.99 per month (**A1**) |

**Revenue model:** five sources of income, typical of a mobile bank.

| Revenue line | How it works | Driver in our data |
|---|---|---|
| Card interchange | the bank receives a small fee on each card payment; EU rules cap it at 0.2 % for debit cards | €506 of card spending per client per month (measured) |
| Subscriptions | Premium and Private plans | segment mix (measured), prices (**A1**) |
| Net interest on deposits | money left on current accounts is placed at a higher rate than paid to clients | average current-account balance €7,474 (measured) |
| Investment fees | custody and trading fees on investment accounts | 35.8 % of clients hold an investment account (measured) |
| Overdraft and credit | interest on overdrafts | 205 clients (2.1 %) have a Banque de France credit incident (measured) |

## 2. Size, operations and stakeholders

| | Value | Source |
|---|---|---|
| Clients | 250,000 (**A2**); our dataset is a **4 % sample** of 10,000 clients | assumption / measured |
| Employees | about 220 (**A3**), of which a data team of 3 (Lélia, Thomas, Adrien) | assumption |
| Card payments | about 3,200 per day for the 10,000-client sample (290,735 authorized in 91 days), so about 80,000 per day at full size | measured, then scaled with A2 |
| Card spending | €15.2 M in 91 days for the sample (average payment €52.21, median €20.21) | measured |
| Payments abroad | 5 % (14,893) | measured |
| Declined payments | 3 % (9,012) | measured |
| Regulators | Banque de France / ACPR (supervision), Tracfin (anti-money laundering) | real institutions |
| Region | France; data must stay in the EU | regulation (GDPR, DORA) |

**Stakeholders and what they need from data:**

| Stakeholder | Needs | Use case |
|---|---|---|
| Clients | see a payment and their balance right away; understand their spending | UC1, UC2 |
| Customer advisors | know a client's spending and portfolio before a call | UC2 |
| Compliance officer | review suspicious payments, file declarations to Tracfin | UC3 |
| Banque de France | daily card figures, credit incidents | UC3 |
| Head of risk | clients with a credit incident and a negative balance | UC3 |
| CFO | card volumes and revenue drivers | UC2, UC3 |
| Data team | a pipeline that is reliable, cheap and auditable | all |

## 3. The problem, in numbers

Today (in the story) Databank's data sits in separate systems: card authorizations at the card processor,
balances in the core banking system, market prices with a data vendor, regulatory files on a server. That
causes four concrete problems:

| Problem | Constraint the platform must meet |
|---|---|
| Clients see a card payment only when it is booked (often the next day), so they think they have more money than they do | a payment must appear in the app in **under 2 minutes** (target: 1 minute) |
| Spending and portfolio are not visible in one place | dashboard data refreshed at least **every 15 minutes**; portfolio valued **daily** with real market prices |
| Regulatory figures are compiled by hand | the daily Banque de France report must be ready **before 09:00 the next working day**, and reproducible |
| Suspicious payments are found late | every payment scored for fraud on arrival; alerts reviewed **within 24 hours** (**A4**) |

**Other constraints:**

| Constraint | Value |
|---|---|
| Budget for the prototype | **€0**: free Snowflake trial credits and free tiers only; nothing is paid (course rule) |
| Compute cap | resource monitor of 20 trial credits per month, warehouses suspended at 100 % |
| Personal data | names, emails, IBANs and birth dates visible only to compliance; card numbers never stored |
| Data retention | transactions kept at least 5 years after the end of the relationship (French anti-money-laundering law) |
| Peak load | 10× the average payment rate at lunchtime and on sales days (**A5**) |

## 4. Assumptions

| # | Assumption | Why it is reasonable | What changes if it is wrong |
|---|---|---|---|
| A1 | Premium €7.99/month, Private €24.99/month | in line with French mobile banks' paid plans | revenue only; no impact on the pipeline |
| A2 | 250,000 clients in total; the 10,000 in Snowflake are a 4 % sample | a mid-sized French neobank | volumes × 25; Snowflake scales without redesign (see design_questions.md) |
| A3 | about 220 employees, data team of 3 | typical for this size | ownership: each person owns one area of the pipeline |
| A4 | AML alerts reviewed within 24 h | internal policy; legal duty is to declare "without delay" | the daily refresh of `AML_ALERTS` would need to be faster |
| A5 | peak = 10× average payment rate | lunch and sales peaks in card data | the live path uses an XSMALL warehouse; a multi-cluster warehouse absorbs peaks |
| A6 | simulated data reproduces real defects: ~1 % duplicates, ~0.2 % broken amounts, ~0.3 % large payments | standard rates for card message streams | measured in our data: 0.99 %, 0.18 %, 0.30 % (see [evidence.md](evidence.md)) |

Business uses of this data: [use_cases.md](use_cases.md).
