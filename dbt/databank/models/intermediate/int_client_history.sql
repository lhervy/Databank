-- SCD type 2 history of clients, rebuilt from the CDC change log (source B).
-- Every INSERT in the log (initial snapshot or after-image of an update) opens a version.
with versions as (
    select
        client_id,
        record:CITY::string    as city,
        record:SEGMENT::string as segment,
        captured_at            as valid_from
    from {{ ref('stg_cdc__core_banking_changes') }}
    where source_table = 'CLIENTS'
      and change_type = 'INSERT'
)
select
    client_id,
    city,
    segment,
    valid_from,
    lead(valid_from) over (partition by client_id order by valid_from) as valid_to,
    lead(valid_from) over (partition by client_id order by valid_from) is null as is_current,
    row_number() over (partition by client_id order by valid_from)     as version
from versions
