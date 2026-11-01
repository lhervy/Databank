-- Gold dimension: accounts (current and investment)
select account_id, client_id, account_type, status, ledger_balance_eur, balance_as_of
from {{ ref('stg_core_banking__accounts') }}
