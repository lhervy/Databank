-- E · Banque de France registry lines (one file per extract date)
select
    client_id,
    registry,
    incident_flag,
    incident_type,
    incident_date,
    extract_date,
    source_file,
    loaded_at::timestamp_ntz as loaded_at
from {{ source('bdf', 'bdf_registry') }}
