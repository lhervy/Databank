{{ config(materialized='view') }}
-- Data quality · quarantine: authorization messages that cannot become a transaction, with the reason
select
    a.record_json,
    a.ingested_at,
    case
        when not a.is_parsable                  then 'UNPARSABLE_JSON'
        when a.amount_eur is null
          or a.amount_eur <= 0                  then 'INVALID_AMOUNT'
        when a.event_ts is null                 then 'INVALID_TIMESTAMP'
        when acc.account_id is null             then 'UNKNOWN_CARD'
        when m.merchant_id is null              then 'UNKNOWN_MERCHANT'
    end as reject_reason
from {{ ref('stg_tpe__authorizations') }} a
left join {{ ref('stg_core_banking__accounts') }}  acc on acc.card_token = a.card_token
left join {{ ref('stg_core_banking__merchants') }} m   on m.merchant_id  = a.merchant_id
where not a.is_parsable
   or a.amount_eur is null or a.amount_eur <= 0
   or a.event_ts is null
   or acc.account_id is null
   or m.merchant_id is null
