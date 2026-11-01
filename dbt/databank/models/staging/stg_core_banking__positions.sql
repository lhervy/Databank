-- B · Securities held on investment accounts
select
    account_id,
    client_id,
    ticker,
    quantity,
    avg_buy_price_usd,
    updated_at
from {{ source('core_banking', 'positions') }}
