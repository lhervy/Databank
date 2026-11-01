-- B · Accounts. ledger_balance_eur is the booked balance at balance_as_of (single source of truth).
select
    account_id,
    client_id,
    account_type,
    card_token,
    ledger_balance_eur,
    balance_as_of,
    status,
    updated_at
from {{ source('core_banking', 'accounts') }}
