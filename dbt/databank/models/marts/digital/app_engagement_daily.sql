-- Gold · digital: daily app usage (source F) - which features clients use
select
    event_ts::date                          as event_date,
    event_type,
    screen,
    device,
    count(*)                                as n_events,
    count(distinct client_id)               as n_clients
from {{ ref('stg_app__events') }}
group by 1, 2, 3, 4
