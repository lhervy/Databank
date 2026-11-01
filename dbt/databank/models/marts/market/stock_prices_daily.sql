-- Gold · market: daily closes in USD and EUR for the tickers our clients hold
select
    s.ticker,
    s.price_date,
    s.close_usd,
    round(s.close_usd / fx.eur_rate, 4) as close_eur,
    fx.rate_source                      as fx_source
from {{ ref('stg_market__stock_prices') }} s
left join {{ ref('int_fx_rates_daily') }} fx
       on fx.currency = 'USD' and fx.rate_date = s.price_date
