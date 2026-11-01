-- No payment can be timestamped more than 5 minutes in the future (clock or parsing bug).
select transaction_id, event_ts
from {{ ref('fct_card_transactions') }}
where event_ts > dateadd(minute, 5, sysdate())
