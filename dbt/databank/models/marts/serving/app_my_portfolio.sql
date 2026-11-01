{{ config(materialized='view', secure=true,
          grants={'select': ['DATABANK_CLIENT_APP']},
          post_hook=["{{ add_client_row_policy('client_id') }}"]) }}
-- App-facing: a client's portfolio valued in EUR
select * from {{ ref('portfolio_valuation') }}
