-- Two independent FX sources (D: ECB API, C: Marketplace) -> one conformed daily rate.
-- The ECB API is the reference; the Marketplace fills days the API has not loaded.
with api as (
    select rate_date, currency, rate from {{ ref('stg_ecb__fx_rates') }}
),
mkt as (
    select rate_date, currency, rate from {{ ref('stg_market__fx_rates') }}
)
select
    coalesce(api.rate_date, mkt.rate_date)             as rate_date,
    coalesce(api.currency, mkt.currency)               as currency,
    coalesce(api.rate, mkt.rate)                       as eur_rate,
    iff(api.rate is not null, 'ECB_API', 'MARKETPLACE') as rate_source,
    api.rate                                           as ecb_api_rate,
    mkt.rate                                           as marketplace_rate,
    round(100 * (api.rate - mkt.rate) / nullif(mkt.rate, 0), 4) as source_diff_pct
from api
full outer join mkt
  on api.rate_date = mkt.rate_date and api.currency = mkt.currency
