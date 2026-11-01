-- C · Daily closing prices (USD) of the tickers our clients hold, from the Marketplace share
select
    ticker,
    date            as price_date,
    value           as close_usd,
    primary_exchange_name
from {{ source('marketplace', 'stock_price_timeseries') }}
where variable = 'post-market_close'
  and ticker in ({{ "'" ~ var('held_tickers') | join("', '") ~ "'" }})
