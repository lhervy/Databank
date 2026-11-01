-- A · Card terminal authorizations: parse the raw JSON, type every field.
-- No filtering here: invalid rows are flagged and kept for the quarantine model.
with source as (
    select * from {{ source('tpe', 'tpe_authorizations') }}
),

parsed as (
    select try_parse_json(record_json) as j, record_json, producer_id, batch_id, ingested_at
    from source
)

select
    j:transaction_id::string                         as transaction_id,
    j:card_token::string                             as card_token,
    j:merchant_id::string                            as merchant_id,
    j:terminal_id::string                            as terminal_id,
    try_to_number(j:amount::string, 12, 2)           as amount_eur,
    j:currency::string                               as currency,
    j:country::string                                as country,
    j:status::string                                 as status,
    try_to_timestamp_ntz(j:event_ts::string)         as event_ts,
    ingested_at,
    producer_id,
    batch_id,
    (j is not null and j:transaction_id is not null) as is_parsable,
    record_json
from parsed
