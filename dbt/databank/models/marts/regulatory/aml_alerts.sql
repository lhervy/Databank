{{ config(materialized='view') }}
-- Gold · anti-money-laundering alerts to review (then declared to Tracfin). Names masked except for Compliance.
select
    t.transaction_id,
    t.event_ts,
    t.client_id,
    c.first_name,
    c.last_name,
    c.segment,
    c.has_credit_incident,
    t.amount_eur,
    t.country,
    t.merchant_name,
    t.fraud_score
from {{ ref('fct_card_transactions') }} t
join {{ ref('dim_clients') }} c on c.client_id = t.client_id
where t.is_suspicious
