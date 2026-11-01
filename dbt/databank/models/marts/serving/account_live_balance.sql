{{ config(
    materialized = 'dynamic_table',
    target_lag = '1 minute',
    snowflake_warehouse = 'DATABANK_WH',
    refresh_mode = 'AUTO'
) }}
-- Gold · live balance = booked ledger balance (single source of truth) - pending card payments
select
    a.account_id,
    a.client_id,
    a.ledger_balance_eur,
    a.balance_as_of,
    coalesce(sum(iff(t.status = 'AUTHORIZED', t.amount_eur, 0)), 0)                        as pending_amount_eur,
    count_if(t.status = 'AUTHORIZED')                                                      as pending_count,
    a.ledger_balance_eur - coalesce(sum(iff(t.status = 'AUTHORIZED', t.amount_eur, 0)), 0) as available_balance_eur,
    max(t.event_ts)                                                                        as last_payment_ts
from {{ ref('stg_core_banking__accounts') }} a
left join {{ ref('fct_card_transactions') }} t
       on t.account_id = a.account_id
      and t.booking_status = 'PENDING'
where a.account_type = 'CURRENT'
group by a.account_id, a.client_id, a.ledger_balance_eur, a.balance_as_of
