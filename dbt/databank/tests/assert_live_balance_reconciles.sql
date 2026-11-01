-- Live balance must equal ledger balance minus pending payments (single source of truth check).
select account_id
from {{ ref('account_live_balance') }}
where abs(available_balance_eur - (ledger_balance_eur - pending_amount_eur)) > 0.01
