-- Gold dimension: merchants
select merchant_id, merchant_name, category, city
from {{ ref('stg_core_banking__merchants') }}
