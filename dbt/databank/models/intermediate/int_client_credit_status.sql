-- Latest Banque de France status per client: a later extract can clear an incident.
select
    client_id,
    incident_flag,
    incident_type,
    incident_date,
    extract_date as status_as_of,
    source_file
from {{ ref('stg_bdf__registry') }}
qualify row_number() over (partition by client_id, registry order by extract_date desc, loaded_at desc) = 1
