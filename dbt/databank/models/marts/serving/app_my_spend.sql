{{ config(materialized='view', secure=true,
          grants={'select': ['DATABANK_CLIENT_APP']},
          post_hook=["{{ add_client_row_policy('client_id') }}"]) }}
-- App-facing: a client's spending by day and category
select * from {{ ref('client_daily_spend') }}
