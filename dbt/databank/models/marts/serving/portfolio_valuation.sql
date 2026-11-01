-- Gold · investments: positions valued at the last real closing price (C), converted to EUR
-- with the conformed FX rate (D, or C as fallback).
with last_price as (
    select ticker, price_date, close_usd
    from {{ ref('stg_market__stock_prices') }}
    qualify row_number() over (partition by ticker order by price_date desc) = 1
),
usd as (
    select rate_date, eur_rate
    from {{ ref('int_fx_rates_daily') }}
    where currency = 'USD'
    qualify row_number() over (order by rate_date desc) = 1
)
select
    p.client_id,
    p.account_id,
    p.ticker,
    p.quantity,
    lp.close_usd,
    lp.price_date,
    usd.eur_rate                                                         as usd_per_eur,
    usd.rate_date                                                        as fx_date,
    round(p.quantity * lp.close_usd / usd.eur_rate, 2)                   as market_value_eur,
    round(p.quantity * (lp.close_usd - p.avg_buy_price_usd) / usd.eur_rate, 2) as unrealized_pnl_eur
from {{ ref('stg_core_banking__positions') }} p
join last_price lp on lp.ticker = p.ticker
cross join usd
