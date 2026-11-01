-- D · ECB euro reference rates from the API. Re-loads are possible: keep the latest load per day and currency.
select
    rate_date,
    currency,
    rate,
    series_key,
    loaded_at,
    run_id
from {{ source('ecb_api', 'ecb_fx_rates') }}
qualify row_number() over (partition by rate_date, currency order by loaded_at desc) = 1
