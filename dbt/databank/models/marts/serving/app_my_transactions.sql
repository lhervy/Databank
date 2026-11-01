{{ config(materialized='view', secure=true,
          grants={'select': ['DATABANK_CLIENT_APP']},
          post_hook=["{{ add_client_row_policy('client_id') }}"]) }}
-- App-facing: a client's own card payments (row access policy filters by logged-in client)
select client_id, transaction_id, event_ts, merchant_name, category, amount_eur, status, booking_status, is_suspicious
from {{ ref('fct_card_transactions') }}
