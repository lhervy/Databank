-- Gold · risk: clients with a Banque de France incident whose live balance is negative
select
    c.client_id,
    c.segment,
    c.incident_type,
    c.credit_status_as_of,
    b.available_balance_eur,
    b.pending_count
from {{ ref('dim_clients') }} c
join {{ ref('account_live_balance') }} b on b.client_id = c.client_id
where c.has_credit_incident
  and b.available_balance_eur < 0
