-- F · Mobile app events (JSON lines)
select
    record:event_id::string                       as event_id,
    record:client_id::string                      as client_id,
    record:event_type::string                     as event_type,
    record:screen::string                         as screen,
    record:device::string                         as device,
    record:app_version::string                    as app_version,
    try_to_timestamp_ntz(record:event_ts::string) as event_ts,
    source_file,
    loaded_at::timestamp_ntz                      as loaded_at
from {{ source('app', 'app_events') }}
qualify row_number() over (partition by record:event_id::string order by loaded_at) = 1
