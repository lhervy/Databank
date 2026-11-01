-- Gold · personalized dashboards: spend per client, day and category
select
    client_id,
    event_date,
    category,
    count(*)        as n_transactions,
    sum(amount_eur) as spend_eur
from {{ ref('fct_card_transactions') }}
where status = 'AUTHORIZED'
group by client_id, event_date, category
