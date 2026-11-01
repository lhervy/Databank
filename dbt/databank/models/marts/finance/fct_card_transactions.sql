{{ config(
    materialized = 'dynamic_table',
    target_lag = '1 minute',
    snowflake_warehouse = 'DATABANK_WH',
    refresh_mode = 'AUTO'
) }}
-- Gold fact: every valid card payment, deduplicated (network retries), enriched, fraud-scored.
-- A DYNAMIC TABLE: Snowflake keeps it at most 1 minute behind RAW, no scheduler needed.
with valid as (
    select *
    from {{ ref('stg_tpe__authorizations') }}
    where is_parsable
      and amount_eur > 0
      and event_ts is not null
    qualify row_number() over (partition by transaction_id order by ingested_at) = 1
)
select
    v.transaction_id,
    a.account_id,
    a.client_id,
    v.merchant_id,
    m.merchant_name,
    m.category,
    v.amount_eur,
    v.country,
    v.status,
    v.event_ts,
    v.event_ts::date                                           as event_date,
    v.ingested_at,
    datediff(millisecond, v.event_ts, v.ingested_at)           as ingest_latency_ms,
    {{ fraud_score('v.amount_eur', 'v.country', 'v.event_ts') }} as fraud_score,
    {{ fraud_score('v.amount_eur', 'v.country', 'v.event_ts') }} >= {{ var('fraud_score_threshold') }} as is_suspicious,
    iff(v.event_ts > a.balance_as_of, 'PENDING', 'BOOKED')     as booking_status
from valid v
join {{ ref('stg_core_banking__accounts') }}  a on a.card_token  = v.card_token
join {{ ref('stg_core_banking__merchants') }} m on m.merchant_id = v.merchant_id
