-- B · CDC change log, one row per captured change
select
    source_table,
    change_type,
    is_update,
    captured_at,
    record:CLIENT_ID::string  as client_id,
    record:ACCOUNT_ID::string as account_id,
    record
from {{ source('cdc', 'core_banking_changes') }}
