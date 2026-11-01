-- Gold · regulatory: daily figures for the Banque de France report
select
    event_date,
    count(*)                                                           as n_transactions,
    count_if(status = 'DECLINED')                                      as n_declined,
    sum(iff(status = 'AUTHORIZED', amount_eur, 0))                     as authorized_amount_eur,
    sum(iff(status = 'AUTHORIZED' and country <> 'FR', amount_eur, 0)) as cross_border_amount_eur,
    count_if(is_suspicious)                                            as n_suspicious,
    count(distinct client_id)                                          as n_active_clients
from {{ ref('fct_card_transactions') }}
group by event_date
