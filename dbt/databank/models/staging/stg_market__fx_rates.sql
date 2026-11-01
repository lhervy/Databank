-- C · Daily FX rates from the Marketplace share (units of currency for 1 EUR)
select
    date               as rate_date,
    quote_currency_id  as currency,
    value              as rate
from {{ source('marketplace', 'fx_rates_timeseries') }}
where base_currency_id = 'EUR'
  and quote_currency_id in ({{ "'" ~ var('fx_currencies') | join("', '") ~ "'" }})
